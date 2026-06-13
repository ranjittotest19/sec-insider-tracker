"use client";

interface Filters {
  txn_type: string;
  days: number;
  min_value: number;
}

interface Props {
  filters: Filters;
  onChange: (f: Filters) => void;
}

export default function FilterBar({ filters, onChange }: Props) {
  const set = (k: keyof Filters, v: any) => onChange({ ...filters, [k]: v });

  return (
    <div className="flex flex-wrap gap-3 items-center">
      {/* Type toggle */}
      <div className="flex rounded-lg border border-border overflow-hidden text-sm">
        {[
          { v: "", label: "All" },
          { v: "A", label: "Buys" },
          { v: "D", label: "Sells" },
        ].map((opt) => (
          <button
            key={opt.v}
            onClick={() => set("txn_type", opt.v)}
            className={`px-4 py-1.5 transition-colors ${
              filters.txn_type === opt.v
                ? opt.v === "A"
                  ? "bg-accent text-bg font-semibold"
                  : opt.v === "D"
                  ? "bg-danger text-white font-semibold"
                  : "bg-border text-text font-semibold"
                : "text-subtext hover:text-text"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Date range */}
      <select
        className="bg-surface border border-border rounded-lg px-3 py-1.5 text-sm text-text"
        value={filters.days}
        onChange={(e) => set("days", Number(e.target.value))}
      >
        <option value={7}>Last 7 days</option>
        <option value={30}>Last 30 days</option>
        <option value={90}>Last 90 days</option>
        <option value={365}>Last year</option>
      </select>

      {/* Min value */}
      <select
        className="bg-surface border border-border rounded-lg px-3 py-1.5 text-sm text-text"
        value={filters.min_value}
        onChange={(e) => set("min_value", Number(e.target.value))}
      >
        <option value={0}>Any size</option>
        <option value={25000}>$25K+</option>
        <option value={50000}>$50K+</option>
        <option value={100000}>$100K+</option>
        <option value={500000}>$500K+</option>
        <option value={1000000}>$1M+</option>
      </select>
    </div>
  );
}
