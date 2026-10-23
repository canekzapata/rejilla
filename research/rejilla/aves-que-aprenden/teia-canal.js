/* Lectura pública de canales Teia v2 para obras estáticas; no escribe ni usa cartera. */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.TeiaCanal = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const CONTRACT = 'KT19ooSLPFxJQ5mx3kR4Qo2UY4KJDcdMdng9';
  const DEFAULT_TZKT = 'https://api.tzkt.io';
  const DEFAULT_GATEWAYS = [
    'https://ipfsmsg.teia.art/ipfs/',
    'https://ipfs.io/ipfs/',
    'https://gateway.pinata.cloud/ipfs/',
  ];
  const MAX_PAGE = 50;
  const MAX_CHARS = 300;

  class TeiaChannelError extends Error {
    constructor(code, message, cause) {
      super(message);
      this.name = 'TeiaChannelError';
      this.code = code;
      if (cause !== undefined) this.cause = cause;
    }
  }

  function checkedChannelId(value) {
    const id = String(value);
    if (!/^\d+$/.test(id)) throw new TeiaChannelError('INVALID_CHANNEL', 'El ID del canal debe ser numérico.');
    return id;
  }

  function makeUrl(base, path, params) {
    const url = new URL(path.replace(/^\//, ''), base.replace(/\/$/, '') + '/');
    for (const [key, value] of Object.entries(params || {})) url.searchParams.set(key, String(value));
    return url.toString();
  }

  async function getJson(url, fetchImpl, signal, code = 'TZKT_UNAVAILABLE') {
    let response;
    try { response = await fetchImpl(url, { signal, headers: { Accept: 'application/json' } }); }
    catch (error) { throw new TeiaChannelError(code, `No se pudo consultar ${new URL(url).host}.`, error); }
    if (!response.ok) {
      const e = new TeiaChannelError(code, `La consulta devolvió HTTP ${response.status}.`);
      e.status = response.status;
      throw e;
    }
    try { return await response.json(); }
    catch (error) { throw new TeiaChannelError(code, 'La respuesta no contiene JSON válido.', error); }
  }

  function decodeHex(hex) {
    const value = String(hex || '').replace(/^0x/i, '');
    if (!value || value.length % 2 || !/^[0-9a-f]+$/i.test(value)) {
      throw new TeiaChannelError('INVALID_CONTENT_URI', 'El contenido del mensaje no es una URI válida.');
    }
    const bytes = new Uint8Array(value.match(/.{2}/g).map(part => parseInt(part, 16)));
    try { return new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
    catch (error) { throw new TeiaChannelError('INVALID_CONTENT_URI', 'La URI del mensaje no es UTF-8 válido.', error); }
  }

  function accessMode(value) {
    if (typeof value === 'string') return value;
    return value && typeof value === 'object' ? Object.keys(value)[0] : undefined;
  }

  async function fetchIpfsJson(uri, { fetch: fetchImpl = globalThis.fetch, gateways = DEFAULT_GATEWAYS, signal } = {}) {
    if (typeof uri !== 'string' || !uri.startsWith('ipfs://')) {
      throw new TeiaChannelError('INVALID_CONTENT_URI', 'El mensaje no apunta a IPFS.');
    }
    const cid = uri.slice('ipfs://'.length).replace(/^ipfs\//, '');
    if (!/^[a-zA-Z0-9]+$/.test(cid)) {
      throw new TeiaChannelError('INVALID_CONTENT_URI', 'El CID del mensaje no es válido.');
    }
    const failures = [];
    for (const gateway of gateways) {
      try {
        const data = await getJson(new URL(cid, gateway.endsWith('/') ? gateway : `${gateway}/`).toString(), fetchImpl, signal, 'IPFS_UNAVAILABLE');
        if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('El JSON de IPFS no es un objeto.');
        return data;
      } catch (error) { failures.push(error); }
    }
    throw new TeiaChannelError('IPFS_UNAVAILABLE', `No se pudo recuperar ${uri} de los gateways configurados.`, failures.at(-1));
  }

  function channelUrl(tzkt, channelId) {
    return `${tzkt.replace(/\/$/, '')}/v1/contracts/${CONTRACT}/bigmaps/channels/keys/${channelId}`;
  }
  async function fetchChannel(channelId, options) {
    let raw;
    try { raw = await getJson(channelUrl(options.tzkt, channelId), options.fetch, options.signal); }
    catch (error) {
      if (error.status === 404) throw new TeiaChannelError('CHANNEL_NOT_FOUND', `No existe el canal ${channelId}.`, error);
      throw error;
    }
    const channel = raw && Object.prototype.hasOwnProperty.call(raw, 'value') ? raw.value : raw;
    if (!channel) throw new TeiaChannelError('CHANNEL_NOT_FOUND', `No existe el canal ${channelId}.`);
    if (channel.hidden) throw new TeiaChannelError('CHANNEL_HIDDEN', `El canal ${channelId} está oculto.`);
    const mode = accessMode(channel.access_mode);
    if (mode !== 'unrestricted') throw new TeiaChannelError('CHANNEL_NOT_PUBLIC', `El canal ${channelId} no es abierto (modo: ${mode || 'desconocido'}).`);
    return channel;
  }

  async function fetchEvents(tag, channelId, options, { cursor, offset, limit = MAX_PAGE, sort = 'asc' } = {}) {
    const params = {
      contract: CONTRACT, tag,
      [`sort.${sort}`]: 'id',
      limit,
      'payload.channel_id': channelId,
    };
    if (cursor !== undefined && cursor !== null) params['id.gt'] = cursor;
    if (offset !== undefined && offset > 0) params.offset = offset;
    return getJson(makeUrl(options.tzkt, '/v1/contracts/events', params), options.fetch, options.signal);
  }

  async function fetchRows(ids, options) {
    const rows = new Map();
    for (let start = 0; start < ids.length; start += 100) {
      const slice = [...new Set(ids.slice(start, start + 100))];
      const url = makeUrl(options.tzkt, `/v1/contracts/${CONTRACT}/bigmaps/messages/keys`, {
        active: 'true', select: 'key,value', 'key.in': slice.join(','), limit: slice.length,
      });
      const data = await getJson(url, options.fetch, options.signal);
      for (const row of data || []) rows.set(String(row.key), row.value);
    }
    return rows;
  }

  async function parseMessage(event, row, options) {
    const raw = decodeHex(row.content);
    let content = raw;
    let payload = null;
    if (raw.startsWith('ipfs://')) {
      payload = await fetchIpfsJson(raw, options);
      if (payload.type !== 'teia-channel-message' || typeof payload.content !== 'string') {
        throw new TeiaChannelError('INVALID_MESSAGE', `El mensaje ${event.payload.message_id} tiene un formato que Teia no reconoce.`);
      }
      content = payload.content;
    } else if (raw.startsWith('{')) {
      try { payload = JSON.parse(raw); } catch (error) { throw new TeiaChannelError('INVALID_MESSAGE', `El mensaje ${event.payload.message_id} contiene JSON inválido.`, error); }
      if (payload.type === 'teia-channel-message' && typeof payload.content === 'string') content = payload.content;
    }
    return {
      channelId: String(event.payload.channel_id),
      id: String(event.payload.message_id),
      sender: row.sender,
      timestamp: row.timestamp || event.payload.timestamp,
      hidden: Boolean(row.hidden),
      version: Number.parseInt(row.version || '1', 10) || 1,
      content,
      payload,
      deleted: false,
    };
  }

  function segmentText(text, maxChars = MAX_CHARS) {
    if (!Number.isInteger(maxChars) || maxChars < 1) throw new RangeError('maxChars debe ser un entero positivo.');
    const chunks = [];
    let part = '';
    for (const token of (text.match(/\s+|[^\s]+/gu) || [])) {
      if (part && part.length + token.length > maxChars) { chunks.push(part); part = ''; }
      if (token.length <= maxChars) { part += token; continue; }
      // Split an exceptional unbroken token by Unicode code point, preserving its characters.
      const points = [...token];
      if (part) { chunks.push(part); part = ''; }
      while (points.length > maxChars) chunks.push(points.splice(0, maxChars).join(''));
      part = points.join('');
    }
    if (part || !chunks.length) chunks.push(part);
    return chunks;
  }

  function toQueueItems(messages, { maxChars = MAX_CHARS } = {}) {
    return messages.flatMap(message => {
      const parts = segmentText(message.content, maxChars).filter(part => /\S/u.test(part));
      return parts.map((text, index) => ({
        id: `teia/${message.channelId}/${message.id}/v${message.version}/${index + 1}`,
        source: 'teia-channel-message',
        channelId: message.channelId, messageId: message.id, version: message.version,
        sender: message.sender, timestamp: message.timestamp,
        text, originalText: message.content,
        part: index + 1, parts: parts.length,
      }));
    });
  }

  function createQueue({
    channelId, tzkt = DEFAULT_TZKT, fetch: fetchImpl = globalThis.fetch,
    gateways = DEFAULT_GATEWAYS, maxChars = MAX_CHARS, pageSize = MAX_PAGE,
    signal,
  }) {
    const id = checkedChannelId(channelId);
    if (typeof fetchImpl !== 'function') throw new TypeError('Se requiere fetch; sirve en navegador estático o Node moderno.');
    if (!Number.isInteger(pageSize) || pageSize < 1 || pageSize > MAX_PAGE) throw new RangeError(`pageSize debe estar entre 1 y ${MAX_PAGE}.`);
    const options = { tzkt, fetch: fetchImpl, gateways, signal };
    const pending = new Map();
    const done = new Set();
    let cursor = null;
    let started = false;

    return {
      channelId: id,
      async start() {
        await fetchChannel(id, options);
        const [posted, edited, deleted] = await Promise.all([
          fetchEvents('message_posted', id, options, { limit: 1, sort: 'desc' }),
          fetchEvents('message_edited', id, options, { limit: 1, sort: 'desc' }),
          fetchEvents('message_deleted', id, options, { limit: 1, sort: 'desc' }),
        ]);
        cursor = Math.max(0, ...[...posted, ...edited, ...deleted].map(e => Number(e.id) || 0));
        started = true;
        return { cursor: String(cursor), channelId: id };
      },
      async poll() {
        if (!started) await this.start();
        await fetchChannel(id, options); // channel may have been hidden or closed since the last poll
        const [posted, edited, deleted] = await Promise.all([
          fetchEvents('message_posted', id, options, { cursor, limit: pageSize, sort: 'asc' }),
          fetchEvents('message_edited', id, options, { cursor, limit: pageSize, sort: 'asc' }),
          fetchEvents('message_deleted', id, options, { cursor, limit: pageSize, sort: 'asc' }),
        ]);
        const events = [...posted, ...edited, ...deleted].sort((a, b) => Number(a.id) - Number(b.id)).slice(0, pageSize);
        const newMessageEvents = events.filter(e => e.tag !== 'message_deleted');
        const newlyDeleted = new Set(events.filter(e => e.tag === 'message_deleted').map(e => String(e.payload.message_id)));
        const ids = [...new Set([...newMessageEvents.map(e => String(e.payload.message_id)), ...[...pending.values()].map(x => x.messageId)])];
        const rows = ids.length ? await fetchRows(ids, options) : new Map();
        const nextPending = new Map(pending);
        const withdrawn = [];
        for (const [queueId, queued] of nextPending) {
          const row = rows.get(queued.messageId);
          const removed = newlyDeleted.has(queued.messageId) || !row || Boolean(row.hidden);
          const superseded = !removed && events.some(e => e.tag === 'message_edited' && String(e.payload.message_id) === queued.messageId) && Number.parseInt(row.version || '1',10) !== queued.version;
          if (removed || superseded) {
            nextPending.delete(queueId);
            withdrawn.push({ id:queueId, reason:newlyDeleted.has(queued.messageId) || !row ? 'deleted' : row?.hidden ? 'hidden' : 'edited' });
          }
        }
        const messages = [];
        const activeRows = new Set();
        for (const event of events) {
          if (event.tag === 'message_deleted') continue;
          const messageId = String(event.payload.message_id);
          const row = rows.get(messageId);
          if (!row || row.hidden || newlyDeleted.has(messageId)) continue;
          const key = `${messageId}/v${Number.parseInt(row.version || '1',10) || 1}`;
          if (activeRows.has(key)) continue;
          activeRows.add(key);
          messages.push(await parseMessage(event, row, options));
        }
        const unique = new Map();
        for (const message of messages) unique.set(`${message.id}/v${message.version}`, message);
        const items = [];
        for (const message of [...unique.values()].sort((a,b) => Number(a.id)-Number(b.id))) {
          const parts = toQueueItems([message], { maxChars });
          const old = [...nextPending.values()].filter(item => item.messageId === message.id && item.version !== message.version);
          for (const item of old) { nextPending.delete(item.id); withdrawn.push({id:item.id,reason:'edited'}); }
          for (const item of parts) {
            if (done.has(item.id) || nextPending.has(item.id)) continue;
            nextPending.set(item.id, item);
            items.push(item);
          }
        }
        pending.clear(); for (const [key, value] of nextPending) pending.set(key, value);
        if (events.length) cursor = Math.max(cursor, ...events.map(e => Number(e.id) || 0));
        return { items, withdrawn, cursor:String(cursor) };
      },
      acknowledge(queueItemId) {
        pending.delete(queueItemId);
        done.add(queueItemId);
      },
      get cursor() { return cursor === null ? null : String(cursor); },
    };
  }

  return { createQueue, fetchChannel, fetchIpfsJson, segmentText, toQueueItems, TeiaChannelError,
    contract: CONTRACT, gateways: DEFAULT_GATEWAYS.slice(), maxChars: MAX_CHARS, version: 'teia-channel-reader-1' };
});
