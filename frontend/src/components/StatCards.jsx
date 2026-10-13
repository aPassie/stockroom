import { formatMoney, formatNumber } from "../format.js";

export default function StatCards({ stats }) {
  const cards = [
    { label: "Products", value: formatNumber(stats.products) },
    { label: "Units on hand", value: formatNumber(stats.units) },
    { label: "Inventory value", value: formatMoney(stats.inventory_value) },
    { label: "Need reorder", value: formatNumber(stats.low_stock), tone: stats.low_stock ? "warn" : "" },
    { label: "Out of stock", value: formatNumber(stats.out_of_stock), tone: stats.out_of_stock ? "danger" : "" },
  ];

  return (
    <section className="stats">
      {cards.map((card) => (
        <div key={card.label} className={`stat ${card.tone}`}>
          <span>{card.label}</span>
          <strong>{card.value}</strong>
        </div>
      ))}
    </section>
  );
}
