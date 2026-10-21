async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : detail?.[0]?.msg || `Request failed (${response.status})`,
    );
  }
  return data;
}

export const api = {
  products: (filters = {}) =>
    request(
      `/products?${new URLSearchParams(Object.entries(filters).filter(([, v]) => v !== "" && v != null))}`,
    ),
  product: (sku) => request(`/products/${encodeURIComponent(sku)}`),
  chat: (message, history) =>
    request("/chat", {
      method: "POST",
      body: JSON.stringify({ message, history }),
    }),
  authMe: () => request("/auth/me"),
  authLogin: (username, password) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  authSignup: (username, password) =>
    request("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  authLogout: (csrf) =>
    request("/auth/logout", {
      method: "POST",
      headers: { "X-CSRF-Token": csrf },
    }),
  me: () => request("/admin/me"),
  login: (username, password) =>
    request("/admin/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: (csrf) =>
    request("/admin/logout", {
      method: "POST",
      headers: { "X-CSRF-Token": csrf },
    }),
  adminProducts: () => request("/admin/products"),
  create: (product, csrf) =>
    request("/admin/products", {
      method: "POST",
      headers: { "X-CSRF-Token": csrf },
      body: JSON.stringify(product),
    }),
  update: (sku, product, csrf) =>
    request(`/admin/products/${encodeURIComponent(sku)}`, {
      method: "PUT",
      headers: { "X-CSRF-Token": csrf },
      body: JSON.stringify(product),
    }),
  archive: (sku, csrf) =>
    request(`/admin/products/${encodeURIComponent(sku)}`, {
      method: "DELETE",
      headers: { "X-CSRF-Token": csrf },
    }),
};
