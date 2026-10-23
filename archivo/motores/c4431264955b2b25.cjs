const test = require('node:test');
const assert = require('node:assert/strict');
const Teia = require('../lib/siringua/teia-comentarios.js');

const FA2 = Teia.defaultFa2;
const CONTRACT = Teia.contract;
const TOKEN = '885842';
const CID = 'QmPDG3xAyqKCVwGS3Qo1v42LGCBsjrJwfGAR8S6n128vey';
const bytesHex = value => Buffer.from(value, 'utf8').toString('hex');
const response = (data, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => data });

function fixture() {
  const calls = [];
  const old = { id: 100, tag: 'comment_posted', payload: { fa2_address: FA2, token_id: TOKEN, comment_id: '80', sender: 'tz1bird', timestamp: '2026-10-18T19:33:25Z' } };
  const events = [old];
  const newEvents = [];
  const rows = {
    '80': { fa2_address: FA2, token_id: TOKEN, sender: 'tz1bird', content: bytesHex(`ipfs://${CID}`), parent_id: null, hidden: false, timestamp: old.payload.timestamp, version: '1' },
    '81': { fa2_address: FA2, token_id: TOKEN, sender: 'tz1writer', content: bytesHex('agua y ala'), parent_id: '80', hidden: false, timestamp: '2026-10-18T19:35:00Z', version: '1' },
    '82': { fa2_address: FA2, token_id: TOKEN, sender: 'tz1hidden', content: bytesHex('oculto'), parent_id: null, hidden: true, timestamp: '2026-10-18T19:36:00Z', version: '1' },
  };
  const fetch = async urlString => {
    const url = new URL(urlString); calls.push(url);
    if (url.pathname.endsWith('/v1/contracts/events')) {
      assert.equal(url.searchParams.get('contract'), CONTRACT);
      assert.equal(url.searchParams.get('tag'), 'comment_posted');
      assert.equal(url.searchParams.get('payload.fa2_address'), FA2);
      assert.equal(url.searchParams.get('payload.token_id'), TOKEN);
      const after = Number(url.searchParams.get('id.gt') || 0);
      const matches = [...events, ...newEvents].filter(event => Number(event.id) > after &&
        event.payload.fa2_address === FA2 && event.payload.token_id === TOKEN);
      const sorted = url.searchParams.has('sort.desc') ? matches.slice().sort((a, b) => Number(b.id) - Number(a.id)) : matches;
      return response(sorted.slice(0, Number(url.searchParams.get('limit') || 50)));
    }
    const commentKey = url.pathname.match(/\/bigmaps\/comments\/keys\/(\d+)$/)?.[1];
    if (commentKey) {
      if (!rows[commentKey]) return response({ message: 'Not found' }, 404);
      return response({ key: commentKey, value: rows[commentKey], active: true });
    }
    if (url.hostname === 'ipfsmsg.teia.art') return response({ error: 'temporarily unavailable' }, 502);
    if (url.hostname === 'ipfs.io' && url.pathname.endsWith(`/${CID}`)) {
      return response({ type: 'teia-token-comment', version: 1, fa2Address: FA2, tokenId: TOKEN,
        content: 'hola bola de hola', author: 'tz1bird', timestamp: old.payload.timestamp });
    }
    throw new Error(`Ruta de prueba inesperada: ${url}`);
  };
  return { calls, events, newEvents, rows, fetch };
}

test('resuelve token_id → comment_id → bigmap → IPFS y no canta el historial al iniciar', async () => {
  const f = fixture();
  const queue = Teia.createQueue({ tokenId: TOKEN, fetch: f.fetch });
  const state = await queue.start();
  assert.equal(state.cursor, '100');
  assert.equal(state.latestCommentId, '80');
  f.newEvents.push(...[
    { id: 101, tag: 'comment_posted', payload: { fa2_address: FA2, token_id: TOKEN, comment_id: '81', sender: 'tz1writer', timestamp: '2026-10-18T19:35:00Z' } },
    { id: 102, tag: 'comment_posted', payload: { fa2_address: FA2, token_id: TOKEN, comment_id: '82', sender: 'tz1hidden', timestamp: '2026-10-18T19:36:00Z' } },
    { id: 103, tag: 'comment_posted', payload: { fa2_address: 'KT1OtherFA2Address0000000000000000000', token_id: TOKEN, comment_id: '83', sender: 'tz1other', timestamp: '2026-10-18T19:37:00Z' } },
  ]);
  const batch = await queue.poll();
  assert.deepEqual(batch.items.map(item => item.text), ['agua y ala']);
  assert.equal(batch.items[0].commentId, '81');
  assert.equal(batch.items[0].parentId, '80');
  assert.equal(batch.items[0].source, 'teia-token-comment');
  assert.equal(batch.cursor, '102');
  queue.acknowledge(batch.items[0].id);
  assert.deepEqual((await queue.poll()).items, []);
});

test('permite cantar bajo demanda el comentario existente que la pieza ya tiene', async () => {
  const f = fixture();
  const queue = Teia.createQueue({ tokenId: TOKEN, fetch: f.fetch });
  const items = await queue.readLatest();
  assert.equal(items.length, 1);
  assert.equal(items[0].commentId, '80');
  assert.equal(items[0].text, 'hola bola de hola');
  assert.equal(items[0].originalText, 'hola bola de hola');
  assert.ok(f.calls.some(url => url.hostname === 'ipfsmsg.teia.art'));
  assert.ok(f.calls.some(url => url.hostname === 'ipfs.io'));
});

test('valida el ID de pieza y crea segmentos estables por comentario y versión', () => {
  assert.throws(() => Teia.createQueue({ tokenId: '885842?x=1', fetch: async () => response([]) }), /numérico/);
  const items = Teia.toQueueItems([{ fa2Address: FA2, tokenId: TOKEN, id: '90', version: 2,
    content: 'hoja '.repeat(3), sender: 'tz1', timestamp: 'hoy', parentId: null }], { maxChars: 6 });
  assert.deepEqual(items.map(item => item.text), ['hoja ', 'hoja ', 'hoja ']);
  assert.match(items[0].id, /885842\/90\/v2\/1$/);
});
