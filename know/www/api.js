/**
 * spec-dashboard API client
 * Fetch wrappers for all REST endpoints.
 */

async function request(method, path, body) {
  const opts = { method, headers: {} };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok || data.ok === false) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

export async function fetchGraph() { return request('GET', '/api/graph'); }
export async function fetchRules() { return request('GET', '/api/rules'); }
export async function fetchHistory() { return request('GET', '/api/history'); }
export async function undo() { return request('POST', '/api/undo'); }
export async function chatStatus() { return request('GET', '/api/chat/status'); }

export async function addEntity(type, key, name, description) {
  return request('POST', '/api/entity', { type, key, name, description });
}
export async function updateEntity(entityId, fields) {
  return request('PUT', `/api/entity/${entityId}`, fields);
}
export async function deleteEntity(entityId) {
  return request('DELETE', `/api/entity/${entityId}`);
}
export async function addLink(from, to) {
  return request('POST', '/api/link', { from, to });
}
export async function removeLink(from, to) {
  return request('DELETE', '/api/link', { from, to });
}
export async function changePhase(entityId, phase, status) {
  return request('POST', '/api/phase', { entity_id: entityId, phase, status });
}

/**
 * Send a chat message and stream the response via SSE.
 * @param {string} message
 * @param {function} onChunk - called with each text chunk
 * @param {function} onDone - called when stream completes
 * @param {function} onError - called on error
 * @returns {function} abort function
 */
export function sendChat(message, onChunk, onDone, onError) {
  const controller = new AbortController();

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal: controller.signal,
  }).then(async (res) => {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6);
        try {
          const event = JSON.parse(data);
          if (event.type === 'done') {
            onDone?.();
            return;
          }
          if (event.type === 'error') {
            onError?.(event.message);
            return;
          }
          // Claude stream-json events
          if (event.type === 'assistant' && event.message?.content) {
            for (const block of event.message.content) {
              if (block.type === 'text') onChunk?.(block.text);
            }
          }
          // Partial content_block_delta
          if (event.type === 'content_block_delta' && event.delta?.text) {
            onChunk?.(event.delta.text);
          }
          // Result message (final)
          if (event.type === 'result' && event.result) {
            onChunk?.(event.result);
          }
        } catch (e) { /* skip unparseable lines */ }
      }
    }
    onDone?.();
  }).catch((e) => {
    if (e.name !== 'AbortError') onError?.(e.message);
  });

  return () => controller.abort();
}

/**
 * Connect to SSE events for hot graph updates.
 * @param {function} onGraphUpdated - called when graph file changes externally
 * @returns {EventSource} for cleanup
 */
export function connectEvents(onGraphUpdated) {
  const es = new EventSource('/api/events');
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'graph-updated') onGraphUpdated?.();
    } catch {}
  };
  es.onerror = () => {
    // SSE will auto-reconnect
  };
  return es;
}
