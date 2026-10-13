import { timeAgo } from "../format.js";

export default function Movements({ movements }) {
  return (
    <aside className="panel feed">
      <h2>Recent movements</h2>
      {!movements.length && <p className="empty">Nothing recorded yet.</p>}
      <ul>
        {movements.map((m) => (
          <li key={m.id}>
            <span className={`delta ${m.change > 0 ? "in" : "out"}`}>
              {m.change > 0 ? `+${m.change}` : m.change}
            </span>
            <div>
              <b>{m.product_name}</b>
              <small>
                {m.reason.toLowerCase()}
                {m.note && ` · ${m.note}`} · {timeAgo(m.created_at)}
              </small>
            </div>
          </li>
        ))}
      </ul>
    </aside>
  );
}
