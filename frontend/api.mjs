// Small fetch helper for calling the Django JSON API.

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[2]) : null;
}

export class ApiError extends Error {
  constructor(status, errors) {
    super('Request failed');
    this.status = status;
    this.errors = errors || {};
  }
}

// Send JSON, or a FormData (for file uploads; the browser sets the boundary).
async function send(method, url, data) {
  const isForm = data instanceof FormData;
  const res = await fetch(url, {
    method,
    credentials: 'same-origin',
    headers: {
      ...(isForm ? {} : { 'Content-Type': 'application/json' }),
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: data === undefined ? undefined : isForm ? data : JSON.stringify(data),
  });
  const body = res.status === 204 ? {} : await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, body);
  return body;
}

export function apiPost(url, data = {}) {
  return send('POST', url, data);
}

// Turn DRF error responses ({field: ["msg"], non_field_errors: [...]})
// into { fieldErrors: {field: "msg"}, message: "..." }.
export function parseErrors(err) {
  if (!(err instanceof ApiError)) {
    return { fieldErrors: {}, message: 'Network error. Please try again.' };
  }
  const fieldErrors = {};
  let message = '';
  for (const [key, value] of Object.entries(err.errors)) {
    const text = Array.isArray(value) ? value[0] : String(value);
    if (key === 'non_field_errors' || key === 'detail') message = text;
    else fieldErrors[key] = text;
  }
  if (!message && !Object.keys(fieldErrors).length) {
    message = 'Something went wrong. Please try again.';
  }
  return { fieldErrors, message };
}

export async function apiGet(url, params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(query ? `${url}?${query}` : url, { credentials: 'same-origin' });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, body);
  return body;
}

export function apiPatch(url, data = {}) {
  return send('PATCH', url, data);
}

export function apiDelete(url) {
  return send('DELETE', url);
}
