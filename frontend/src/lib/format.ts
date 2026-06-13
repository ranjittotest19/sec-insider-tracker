export function formatCurrency(v: number | string | null): string {
  const n = Number(v);
  if (!n || isNaN(n)) return "—";
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

export function formatNumber(v: number | string | null): string {
  const n = Number(v);
  if (!n || isNaN(n)) return "—";
  return n.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

export function txnLabel(txn_type: string, txn_code?: string): string {
  if (txn_type === "A") {
    if (txn_code === "P") return "Buy";
    if (txn_code === "A") return "Award";
    if (txn_code === "M") return "Option";
    return "Acquired";
  }
  if (txn_type === "D") {
    if (txn_code === "S") return "Sell";
    if (txn_code === "F") return "Tax Sale";
    if (txn_code === "G") return "Gift";
    return "Disposed";
  }
  return txn_type || "—";
}

export function txnBadgeClass(txn_type: string): string {
  if (txn_type === "A") return "bg-accent/15 text-accent";
  if (txn_type === "D") return "bg-danger/15 text-danger";
  return "bg-border text-subtext";
}
