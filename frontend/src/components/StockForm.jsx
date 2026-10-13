import { useState } from "react";

const REASONS = {
  RESTOCK: 1,
  RETURN: 1,
  SALE: -1,
  DAMAGED: -1,
  CORRECTION: 0,
};

export default function StockForm({ product, onSubmit }) {
  const [reason, setReason] = useState("RESTOCK");
  const [amount, setAmount] = useState(1);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const sign = REASONS[reason];
  const change = sign === 0 ? Number(amount) : sign * Math.abs(Number(amount));
  const after = product.quantity + (Number.isFinite(change) ? change : 0);

  async function submit(e) {
    e.preventDefault();
    const note = new FormData(e.currentTarget).get("note");
    setSaving(true);
    setError("");
    try {
      await onSubmit({ change, reason, note });
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="form">
      {error && <p className="alert">{error}</p>}
      <div className="segmented">
        {Object.keys(REASONS).map((r) => (
          <button type="button" key={r} className={r === reason ? "on" : ""} onClick={() => setReason(r)}>
            {r.toLowerCase()}
          </button>
        ))}
      </div>
      <label>
        {sign === 0 ? "Change (use a negative number to remove)" : "Units"}
        <input type="number" required value={amount} min={sign === 0 ? undefined : 1}
               onChange={(e) => setAmount(e.target.value)} />
      </label>
      <label>
        Note
        <input name="note" maxLength={200} placeholder="PO-2291, counter sale, cycle count…" />
      </label>
      <p className={`preview ${after < 0 ? "bad" : ""}`}>
        {product.quantity} → <b>{after}</b> units
      </p>
      <button className="primary" disabled={saving || after < 0 || change === 0}>Record movement</button>
    </form>
  );
}
