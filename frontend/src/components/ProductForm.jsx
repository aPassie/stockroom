import { useState } from "react";

export default function ProductForm({ product, categories, onSubmit }) {
  const editing = Boolean(product);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e) {
    e.preventDefault();
    const form = Object.fromEntries(new FormData(e.currentTarget));
    const body = {
      name: form.name.trim(),
      category: form.category.trim() || "General",
      unit_price: form.unit_price || "0",
      reorder_level: Number(form.reorder_level || 0),
    };
    if (!editing) {
      body.sku = form.sku.trim();
      body.quantity = Number(form.quantity || 0);
    }
    setSaving(true);
    setError("");
    try {
      await onSubmit(body);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="form">
      {error && <p className="alert">{error}</p>}
      <div className="grid-2">
        <label>
          SKU
          <input name="sku" required={!editing} disabled={editing} defaultValue={product?.sku}
                 pattern="[A-Za-z0-9\-]{2,40}" placeholder="KB-101" />
        </label>
        <label>
          Category
          <input name="category" list="categories" defaultValue={product?.category} placeholder="Peripherals" />
          <datalist id="categories">
            {categories.map((c) => <option key={c} value={c} />)}
          </datalist>
        </label>
      </div>
      <label>
        Name
        <input name="name" required maxLength={160} defaultValue={product?.name} placeholder="Mechanical keyboard" />
      </label>
      <div className="grid-3">
        <label>
          Unit price (₹)
          <input name="unit_price" type="number" min="0" step="0.01" defaultValue={product?.unit_price ?? ""} />
        </label>
        {!editing && (
          <label>
            Opening stock
            <input name="quantity" type="number" min="0" defaultValue="0" />
          </label>
        )}
        <label>
          Reorder level
          <input name="reorder_level" type="number" min="0" defaultValue={product?.reorder_level ?? 10} />
        </label>
      </div>
      <button className="primary" disabled={saving}>{editing ? "Save changes" : "Add product"}</button>
    </form>
  );
}
