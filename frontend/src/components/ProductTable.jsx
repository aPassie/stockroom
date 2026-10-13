import { formatMoney } from "../format.js";

function StockLevel({ product }) {
  const target = Math.max(product.reorder_level * 3, 1);
  const width = Math.min(100, (product.quantity / target) * 100);
  const tone = product.quantity === 0 ? "danger" : product.low_stock ? "warn" : "ok";

  return (
    <div className="level">
      <div className="level-row">
        <b>{product.quantity}</b>
        {tone !== "ok" && <span className={`pill ${tone}`}>{tone === "danger" ? "Out" : "Low"}</span>}
      </div>
      <div className="bar"><i className={tone} style={{ width: `${width}%` }} /></div>
      <small>Reorder at {product.reorder_level}</small>
    </div>
  );
}

export default function ProductTable({ products, onAdjust, onEdit, onDelete }) {
  if (!products.length) {
    return <p className="empty">No products match these filters.</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>Category</th>
            <th className="num">Price</th>
            <th>Stock</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id}>
              <td data-label="Product">
                <b>{p.name}</b>
                <code>{p.sku}</code>
              </td>
              <td data-label="Category">{p.category}</td>
              <td data-label="Price" className="num">{formatMoney(p.unit_price)}</td>
              <td data-label="Stock"><StockLevel product={p} /></td>
              <td className="actions">
                <button onClick={() => onAdjust(p)}>Adjust</button>
                <button className="ghost" onClick={() => onEdit(p)}>Edit</button>
                <button className="ghost danger-text" onClick={() => onDelete(p)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
