export function normalizeApiUrl(value) {
  if (!value?.trim()) throw new Error('Missing required environment variable: API_URL');
  const normalized = value.trim().replace(/\/+$/, '');
  try {
    const url = new URL(normalized);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) throw new Error();
  } catch {
    throw new Error('Invalid API_URL: expected an HTTP(S) backend URL without credentials, query or fragment');
  }
  return normalized;
}

export function apiUrl(path, base = import.meta.env.API_URL) {
  return normalizeApiUrl(base) + '/' + path.replace(/^\/+/, '');
}

export function apiFetch(path, options) {
  return fetch(apiUrl(path), options);
}
