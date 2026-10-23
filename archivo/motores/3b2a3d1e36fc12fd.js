/* Lee comentarios públicos de un OBJKT Teia; no publica ni conecta cartera. */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.TeiaComentarios = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const CONTRACT = 'KT1FXFxUcZvne1ApoSaeZfvmDR73u2BsuFUP';
  const DEFAULT_FA2 = 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton';
  const DEFAULT_TZKT = 'https://api.tzkt.io';
  const DEFAULT_GATEWAYS = [
    'https://ipfsmsg.teia.art/ipfs/',
    'https://ipfs.io/ipfs/',
    'https://gateway.pinata.cloud/ipfs/',
  ];
  const MAX_PAGE = 50;
  const MAX_CHARS = 300;

  class TeiaCommentError extends Error {
    constructor(code, message, cause) {
      super(message);
      this.name = 'TeiaCommentError';
      this.code = code;
      if (cause !== undefined) this.cause = cause;
    }
  }

  function checkedNat(value, label) {
    const id = String(value ?? '');
    if (!/^\d+$/.test(id)) throw new TeiaCommentError('INVALID_ID', `${label} debe ser numérico.`);
    return id;
  }

  function checkedAddress(value) {
    const address = String(value ?? '').trim();
    if (!/^KT1[1-9A-HJ-NP-Za-km-z]{33}$/.test(address)) {
      throw new TeiaCommentError('INVALID_FA2', 'La dirección FA2 debe ser un contrato KT1 válido.');
    }
    return address;
  }

  function makeUrl(base, path, params) {
    const url = new URL(path.replace(/^\//, ''), base.replace(/\/$/, '') + '/');
    for (const [key, value] of Object.entries(params || {})) url.searchParams.set(key, String(value));
    return url.toString();
  }

  async function getJson(url, fetchImpl, signal, code = 'TZKT_UNAVAILABLE') {
    let response;
    try { response = await fetchImpl(url, { signal, headers: { Accept: 'application/json' } }); }
    catch (error) { throw new TeiaCommentError(code, `No se pudo consultar ${new URL(url).host}.`, error); }
    if (!response.ok) {
      const error = new TeiaCommentError(code, `La consulta devolvió HTTP ${response.status}.`);
      error.status = response.status;
      throw error;
    }
    try { return await response.json(); }
    catch (error) { throw new TeiaCommentError(code, 'La respuesta no contiene JSON válido.', error); }
  }

  function decodeHex(hex) {
    const value = String(hex || '').replace(/^0x/i, '');
    if (!value || value.length % 2 || !/^[0-9a-f]+$/i.test(value)) {
      throw new TeiaCommentError('INVALID_CONTENT', 'El contenido del comentario no es hexadecimal válido.');
    }
    const bytes = new Uint8Array(value.match(/.{2}/g).map(part => parseInt(part, 16)));
    try { return new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
    catch (error) { throw new TeiaCommentError('INVALID_CONTENT', 'El contenido del comentario no es UTF-8 válido.', error); }
  }

  async function fetchIpfsJson(uri, { fetch: fetchImpl = globalThis.fetch, gateways = DEFAULT_GATEWAYS, signal } = {}) {
    if (typeof uri !== 'string' || !uri.startsWith('ipfs://')) {
      throw new TeiaCommentError('INVALID_CONTENT_URI', 'El comentario no apunta a IPFS.');
    }
    const cid = uri.slice('ipfs://'.length).replace(/^ipfs\//, '');
    if (!/^[a-zA-Z0-9]+$/.test(cid)) throw new TeiaCommentError('INVALID_CONTENT_URI', 'El CID del comentario no es válido.');
    const failures = [];
    for (const gateway of gateways) {
      try {
        const value = await getJson(new URL(cid, gateway.endsWith('/') ? gateway : `${gateway}/`).toString(), fetchImpl, signal, 'IPFS_UNAVAILABLE');
        if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('El JSON de IPFS no es un objeto.');
        return value;
      } catch (error) { failures.push(error); }
    }
    throw new TeiaCommentError('IPFS_UNAVAILABLE', `No se pudo recuperar ${uri} de los gateways configurados.`, failures.at(-1));
  }

  function eventsUrl(tzkt, fa2Address, tokenId, { cursor, limit = MAX_PAGE, sort = 'asc' } = {}) {
    const params = {
      contract: CONTRACT,
      tag: 'comment_posted',
      [`sort.${sort}`]: 'id',
      limit,
      'payload.fa2_address': fa2Address,
      'payload.token_id': tokenId,
    };
    if (cursor !== undefined && cursor !== null) params['id.gt'] = cursor;
    return makeUrl(tzkt, '/v1/contracts/events', params);
  }

  async function fetchEvents(fa2Address, tokenId, options, paging) {
    return getJson(eventsUrl(options.tzkt, fa2Address, tokenId, paging), options.fetch, options.signal);
  }

  async function fetchRows(ids, options) {
    const rows = new Map();
    // TzKT exposes the contract bigmap's single-key route explicitly. Use it
    // instead of `keys?key.in=...`: that list-filter form can return HTTP 400
    // for this contract endpoint even though the event query succeeds.
    const unique = [...new Set(ids.map(String))];
    for (let start = 0; start < unique.length; start += 8) {
      const slice = unique.slice(start, start + 8);
      const found = await Promise.all(slice.map(async key => {
        const url = makeUrl(options.tzkt,
          `/v1/contracts/${CONTRACT}/bigmaps/comments/keys/${encodeURIComponent(key)}`);
        try { return [key, await getJson(url, options.fetch, options.signal)]; }
        catch (error) {
          if (error.status === 404) return [key, null];
          throw error;
        }
      }));
      for (const [key, row] of found) if (row?.value) rows.set(key, row.value);
    }
    return rows;
  }

  function contentFromPayload(payload, event, row) {
    if (!payload || payload.type !== 'teia-token-comment' || typeof payload.content !== 'string') {
      throw new TeiaCommentError('INVALID_COMMENT', `El comentario ${event.payload.comment_id} tiene un formato que Teia no reconoce.`);
    }
    if (String(payload.tokenId) !== String(row.token_id) || payload.fa2Address !== row.fa2_address) {
      throw new TeiaCommentError('COMMENT_MISMATCH', `El comentario ${event.payload.comment_id} apunta a otra pieza.`);
    }
    return payload.content;
  }

  async function parseComment(event, row, options) {
    if (!row || row.hidden) return null;
    if (String(row.token_id) !== String(event.payload.token_id) || row.fa2_address !== event.payload.fa2_address) return null;
    const raw = decodeHex(row.content);
    let content = raw;
    if (raw.startsWith('ipfs://')) {
      content = contentFromPayload(await fetchIpfsJson(raw, options), event, row);
    } else if (raw.startsWith('{')) {
      let payload;
      try { payload = JSON.parse(raw); }
      catch (error) { throw new TeiaCommentError('INVALID_COMMENT', `El comentario ${event.payload.comment_id} contiene JSON inválido.`, error); }
      content = contentFromPayload(payload, event, row);
    }
    return {
      fa2Address: row.fa2_address,
      tokenId: String(row.token_id),
      id: String(event.payload.comment_id),
      sender: row.sender,
      parentId: row.parent_id === null ? null : String(row.parent_id),
      timestamp: row.timestamp || event.payload.timestamp,
      hidden: Boolean(row.hidden),
      version: Number.parseInt(row.version || '1', 10) || 1,
      content,
    };
  }

  function segmentText(text, maxChars = MAX_CHARS) {
    if (!Number.isInteger(maxChars) || maxChars < 1) throw new RangeError('maxChars debe ser un entero positivo.');
    const chunks = [];
    let part = '';
    for (const token of (text.match(/\s+|[^\s]+/gu) || [])) {
      if (part && part.length + token.length > maxChars) { chunks.push(part); part = ''; }
      if (token.length <= maxChars) { part += token; continue; }
      const points = [...token];
      if (part) { chunks.push(part); part = ''; }
      while (points.length > maxChars) chunks.push(points.splice(0, maxChars).join(''));
      part = points.join('');
    }
    if (part || !chunks.length) chunks.push(part);
    return chunks;
  }

  function toQueueItems(comments, { maxChars = MAX_CHARS } = {}) {
    return comments.flatMap(comment => {
      if (comment.hidden || !/\S/u.test(comment.content)) return [];
      const parts = segmentText(comment.content, maxChars).filter(part => /\S/u.test(part));
      return parts.map((text, index) => ({
        id: `teia-comment/${comment.fa2Address}/${comment.tokenId}/${comment.id}/v${comment.version}/${index + 1}`,
        source: 'teia-token-comment',
        fa2Address: comment.fa2Address,
        tokenId: comment.tokenId,
        commentId: comment.id,
        version: comment.version,
        sender: comment.sender,
        timestamp: comment.timestamp,
        parentId: comment.parentId,
        text,
        originalText: comment.content,
        part: index + 1,
        parts: parts.length,
      }));
    });
  }

  function createQueue({
    tokenId,
    fa2Address = DEFAULT_FA2,
    tzkt = DEFAULT_TZKT,
    fetch: fetchImpl = globalThis.fetch,
    gateways = DEFAULT_GATEWAYS,
    maxChars = MAX_CHARS,
    pageSize = MAX_PAGE,
    signal,
  }) {
    const token = checkedNat(tokenId, 'El ID del OBJKT');
    const fa2 = checkedAddress(fa2Address);
    if (typeof fetchImpl !== 'function') throw new TypeError('Se requiere fetch; sirve en navegador estático o Node moderno.');
    if (!Number.isInteger(pageSize) || pageSize < 1 || pageSize > MAX_PAGE) throw new RangeError(`pageSize debe estar entre 1 y ${MAX_PAGE}.`);
    const options = { tzkt, fetch: fetchImpl, gateways, signal };
    const pending = new Map();
    const done = new Set();
    let cursor = null;
    let started = false;

    async function latestEvent() {
      const events = await fetchEvents(fa2, token, options, { limit: 1, sort: 'desc' });
      return events[0] || null;
    }

    async function readEvents(events) {
      const ids = [...new Set(events.map(event => String(event.payload.comment_id)))];
      const rows = ids.length ? await fetchRows(ids, options) : new Map();
      const comments = [];
      for (const event of events) {
        const row = rows.get(String(event.payload.comment_id));
        if (!row || row.hidden) continue;
        const comment = await parseComment(event, row, options);
        if (comment) comments.push(comment);
      }
      return comments;
    }

    return {
      tokenId: token,
      fa2Address: fa2,
      async start() {
        const latest = await latestEvent();
        cursor = latest ? String(latest.id) : '0';
        started = true;
        return { cursor, tokenId: token, fa2Address: fa2, latestCommentId: latest ? String(latest.payload.comment_id) : null };
      },
      async readLatest() {
        const event = await latestEvent();
        if (!event) return [];
        return toQueueItems(await readEvents([event]), { maxChars });
      },
      async poll() {
        if (!started) await this.start();
        const events = await fetchEvents(fa2, token, options, { cursor, limit: pageSize, sort: 'asc' });
        const ordered = (events || []).sort((a, b) => Number(a.id) - Number(b.id));
        const comments = await readEvents(ordered);
        const items = [];
        for (const item of toQueueItems(comments, { maxChars })) {
          if (done.has(item.id) || pending.has(item.id)) continue;
          pending.set(item.id, item);
          items.push(item);
        }
        if (ordered.length) cursor = String(Math.max(Number(cursor), ...ordered.map(event => Number(event.id) || 0)));
        return { items, cursor };
      },
      acknowledge(itemId) { pending.delete(itemId); done.add(itemId); },
      get cursor() { return cursor; },
    };
  }

  return {
    createQueue, decodeHex, fetchIpfsJson, segmentText, toQueueItems,
    TeiaCommentError, contract: CONTRACT, defaultFa2: DEFAULT_FA2,
    gateways: DEFAULT_GATEWAYS.slice(), maxChars: MAX_CHARS,
    version: 'teia-token-comments-reader-1',
  };
});
