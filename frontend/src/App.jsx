import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import Modal from "./components/Modal.jsx";
import Movements from "./components/Movements.jsx";
import ProductForm from "./components/ProductForm.jsx";
import ProductTable from "./components/ProductTable.jsx";
import StatCards from "./components/StatCards.jsx";
import StockForm from "./components/StockForm.jsx";

const EMPTY_STATS = { products: 0, units: 0, inventory_value: 0, low_stock: 0, out_of_stock: 0, categories: [] };

export default function App() {
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [movements, setMovements] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [lowOnly, setLowOnly] = useState(false);
  const [modal, setModal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const params = {};
    if (search) params.q = search;
    if (category) params.category = category;
    if (lowOnly) params.low_stock = "true";
    try {
      const [p, s, m] = await Promise.all([api.products(params), api.stats(), api.movements()]);
      setProducts(p);
      setStats(s);
      setMovements(m);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [search, category, lowOnly]);

  useEffect(() => {
    const id = setTimeout(refresh, 200);
    return () => clearTimeout(id);
  }, [refresh]);

  const close = useCallback(() => setModal(null), []);

  async function done(action) {
    await action();
    setModal(null);
    refresh();
  }

  async function remove(product) {
    if (!window.confirm(`Delete ${product.name} and its stock history?`)) return;
    try {
      await api.deleteProduct(product.id);
      refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  const categories = stats.categories.map((c) => c.category);

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <svg viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" /><path d="M8 12l8-4 8 4v9l-8 4-8-4zM8 12l8 4 8-4M16 16v9" /></svg>
          <span>Stockroom</span>
        </div>
        <button className="primary" onClick={() => setModal({ type: "create" })}>+ New product</button>
      </header>

      <main>
        <div className="heading">
          <h1>Inventory</h1>
          <p>Live on EKS: track what is on the shelf, what moved, and what needs reordering.</p>
        </div>

        {error && <p className="alert">Cannot reach the API: {error}</p>}

        <StatCards stats={stats} />

        <div className="layout">
          <section className="panel">
            <div className="toolbar">
              <input type="search" placeholder="Search name or SKU" value={search}
                     onChange={(e) => setSearch(e.target.value)} />
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">All categories</option>
                {categories.map((c) => <option key={c}>{c}</option>)}
              </select>
              <label className="check">
                <input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} />
                Needs reorder
              </label>
            </div>
            {loading ? (
              <p className="empty">Loading…</p>
            ) : (
              <ProductTable
                products={products}
                onAdjust={(p) => setModal({ type: "stock", product: p })}
                onEdit={(p) => setModal({ type: "edit", product: p })}
                onDelete={remove}
              />
            )}
          </section>

          <Movements movements={movements} />
        </div>
      </main>

      {modal?.type === "create" && (
        <Modal title="New product" onClose={close}>
          <ProductForm categories={categories} onSubmit={(body) => done(() => api.createProduct(body))} />
        </Modal>
      )}
      {modal?.type === "edit" && (
        <Modal title={`Edit ${modal.product.sku}`} onClose={close}>
          <ProductForm product={modal.product} categories={categories}
                       onSubmit={(body) => done(() => api.updateProduct(modal.product.id, body))} />
        </Modal>
      )}
      {modal?.type === "stock" && (
        <Modal title={`Adjust stock · ${modal.product.name}`} onClose={close}>
          <StockForm product={modal.product}
                     onSubmit={(body) => done(() => api.recordMovement(modal.product.id, body))} />
        </Modal>
      )}
    </div>
  );
}
