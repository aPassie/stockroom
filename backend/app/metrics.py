from prometheus_client import Counter

stock_units_moved = Counter(
    "stockroom_stock_units_moved_total",
    "Units moved in or out of stock",
    ["reason", "direction"],
)
