const money = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" });
const number = new Intl.NumberFormat("en-IN");

export const formatMoney = (value) => money.format(Number(value));
export const formatNumber = (value) => number.format(value);

export function timeAgo(iso) {
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
