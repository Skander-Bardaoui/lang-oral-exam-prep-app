export function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

export function csrfHeaders(extra = {}) {
  return {
    'X-CSRFToken': getCsrfToken(),
    ...extra,
  };
}
