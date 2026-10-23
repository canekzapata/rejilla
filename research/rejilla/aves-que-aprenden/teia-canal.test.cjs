const test = require('node:test');
const assert = require('node:assert/strict');
const Teia = require('./teia-canal.js');

function jsonResponse(data, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => data };
}
function bytesHex(s) { return Buffer.from(s, 'utf8').toString('hex'); }

function makeFetch({ mode = 'unrestricted', hiddenChannel = false } = {}) {
  const calls = [];
  const events = {
    message_posted: [
      { id: 100, payload: { channel_id: '10', message_id: '19', timestamp: '2026-01-01T00:00:00Z' } },
      { id: 101, payload: { channel_id: '10', message_id: '21', timestamp: '2026-01-01T00:01:00Z' } },
      { id: 102, payload: { channel_id: '10', message_id: '22', timestamp: '2026-01-01T00:02:00Z' } },
      { id: 103, payload: { channel_id: '10', message_id: '23', timestamp: '2026-01-01T00:03:00Z' } },
    ],
    message_edited: [{ id: 104, payload: { channel_id: '10', message_id: '21', timestamp: '2026-01-01T00:04:00Z', version: 2 } }],
    message_deleted: [{ id: 105, payload: { channel_id: '10', message_id: '23' } }],
  };
  const rows = {
    '19': { sender: 'tz1old', content: bytesHex('ipfs://bafycid0'), hidden: false, timestamp: '2026-01-01T00:00:00Z', version: '1' },
    '21': { sender: 'tz1bird', content: bytesHex('ipfs://bafycid1'), hidden: false, timestamp: '2026-01-01T00:01:00Z', version: '2' },
    '22': { sender: 'tz1hidden', content: bytesHex('ipfs://bafycid2'), hidden: true, timestamp: '2026-01-01T00:02:00Z', version: '1' },
    '23': { sender: 'tz1deleted', content: bytesHex('ipfs://bafycid3'), hidden: false, timestamp: '2026-01-01T00:03:00Z', version: '1' },
  };
  const fetch = async (urlString) => {
    const url = new URL(urlString); calls.push(url);
    if (url.pathname.endsWith('/bigmaps/channels/keys/10')) {
      return jsonResponse({ value: { hidden: hiddenChannel, access_mode: { [mode]: {} } } });
    }
    if (url.pathname.endsWith('/bigmaps/messages/keys')) {
      const ids = url.searchParams.get('key.in').split(',');
      return jsonResponse(ids.filter(id => rows[id]).map(key => ({ key, value: rows[key] })));
    }
    if (url.pathname.endsWith('/v1/contracts/events')) {
      const tag = url.searchParams.get('tag');
      const all = events[tag] || [];
      const after = Number(url.searchParams.get('id.gt') || 0);
      const filter = url.searchParams.get('payload.message_id.in');
      let matched = url.searchParams.has('id.gt')
        ? all.filter(e => Number(e.id) > after)
        : (filter ? all : (tag === 'message_posted' ? all.filter(e => Number(e.id) === 100) : []));
      if (filter) matched = matched.filter(e => filter.split(',').includes(String(e.payload.message_id)));
      if (url.searchParams.get('sort.desc')) matched.reverse();
      return jsonResponse(matched.slice(0, Number(url.searchParams.get('limit') || 50)).map(event => ({ ...event, tag })));
    }
    if (/\/bafycid\d+$/.test(url.pathname)) {
      if (url.hostname === 'ipfsmsg.teia.art') return jsonResponse({ error: 'temporarily unavailable' }, 502);
      return jsonResponse({ type: 'teia-channel-message', version: 1, content: 'x'.repeat(305), author: 'tz1bird' });
    }
    throw new Error(`Ruta de prueba inesperada: ${url}`);
  };
  return { fetch, calls, events, rows };
}

test('espera mensajes nuevos, respeta ocultamientos/borrados y crea segmentos con versión estable', async () => {
  const { fetch, calls, events, rows } = makeFetch();
  const queue = Teia.createQueue({ channelId: 10, fetch, maxChars: 300 });
  await queue.start();
  assert.equal(queue.cursor, '100');
  const batch = await queue.poll();
  const items = batch.items;
  assert.equal(batch.withdrawn.length, 0);
  assert.equal(items.length, 2);
  assert.equal(items[0].messageId, '21');
  assert.equal(items[0].version, 2);
  assert.equal(items[0].text.length, 300);
  assert.equal(items[1].text.length, 5);
  assert.equal(items[0].originalText, 'x'.repeat(305));
  assert.match(items[0].id, /teia\/10\/21\/v2\/1$/);
  assert.ok(calls.some(url => url.hostname === 'ipfsmsg.teia.art'));
  assert.ok(calls.some(url => url.hostname === 'ipfs.io'));
  assert.equal(items.some(item => item.messageId === '22' || item.messageId === '23'), false);
  rows['21'].version = '3';
  events.message_edited.push({ id:106, payload:{channel_id:'10',message_id:'21',version:3} });
  const edit = await queue.poll();
  assert.deepEqual(edit.withdrawn.map(x => x.reason), ['edited','edited']);
  assert.ok(edit.items.every(item => item.version === 3));
  events.message_deleted.push({ id:107, payload:{channel_id:'10',message_id:'21'} });
  const removal = await queue.poll();
  assert.deepEqual(removal.items, []);
  assert.deepEqual(removal.withdrawn.map(x => x.reason), ['deleted','deleted']);
  queue.acknowledge(items[0].id);
  queue.acknowledge(items[1].id);
  assert.deepEqual((await queue.poll()).items, []);
});

test('rechaza canales cerrados u ocultos antes de leer mensajes', async () => {
  for (const config of [{ mode: 'closed' }, { hiddenChannel: true }]) {
    const { fetch } = makeFetch(config);
    const queue = Teia.createQueue({ channelId: '10', fetch });
    await assert.rejects(() => queue.start(), error => error instanceof Teia.TeiaChannelError && ['CHANNEL_NOT_PUBLIC','CHANNEL_HIDDEN'].includes(error.code));
  }
});

test('segmenta sin perder texto ni romper pares surrogate', () => {
  const source = 'hola '.repeat(4) + '🪶'.repeat(7);
  const parts = Teia.segmentText(source, 8);
  assert.equal(parts.join(''), source);
  assert.ok(parts.every(part => [...part].length <= 8));
  assert.deepEqual(Teia.toQueueItems([{ channelId:'10', id:'44', version:1, content:'   ' }]), []);
});
