async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail) ? body.detail.map((d) => d.msg).join(", ") : body.detail;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

export const api = {
  products: (params) => request(`/products?${new URLSearchParams(params)}`),
  createProduct: (body) => request("/products", { method: "POST", body }),
  updateProduct: (id, body) => request(`/products/${id}`, { method: "PUT", body }),
  deleteProduct: (id) => request(`/products/${id}`, { method: "DELETE" }),
  recordMovement: (id, body) => request(`/products/${id}/movements`, { method: "POST", body }),
  movements: () => request("/movements?limit=12"),
  stats: () => request("/stats"),
};
