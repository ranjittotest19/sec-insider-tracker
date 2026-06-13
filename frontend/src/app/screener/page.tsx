"use client";
import { useState, useEffect, useCallback } from "react";
import FilingsTable from "@/components/tables/FilingsTable";
import { apiFetch } from "@/lib/api";

export default function ScreenerPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    txn_type: "A",
    min_value: 100000,
    days: 30,
    is_officer: "",
    is_director: "",
    role: "",
    exclude_awards: true,
    page: 1,
  });

  const run = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({
      ...(filters.txn_type && { txn_type: filters.txn_type }),
      min_value: String(filters.min_value),
      days: String(filters.days),
      ...(filters.is_officer && { is_officer: filters.is_officer }),
      ...(filters.is_director && { is_director: filters.is_director }),
      ...(filters.role && { role: filters.role }),
      exclude_awards: String(filters.exclude_awards),
      page: String(filters.page),
      limit: "50",
    });
    const res = await apiFetch(`/api/screener/form4?${params}`);
    setData(res);
    setLoading(false);
  }, [filters]);

  useEffect(() => { run(); }, [run]);

  const set = (k: string, v: any) => setFilters((f) => ({ ...f, [k]: v, page: 1 }));

  return (
    <div className="space-y-6">
      <div className="border border-border rounded-xl p-6 bg-surface">
        <h1 className="text-xl font-bold">Screener</h1>
        <p className="text-subtext text-sm mt-1">Filter Form 4 transactions by size, role, and type.</p>
      </div>

      {/* Filter panel */}
      <div className="border border-border rounded-xl p-5 bg-surface grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className="text-xs text-subtext block mb-1">Transaction Type</label>
          <select
            className="w-full bg-bg border border-border rounded px-3 py-2 text-sm text-text"
            value={filters.txn_type}
            onChange={(e) => set("txn_type", e.target.value)}
          >
            <option value="">All</option>
            <option value="A">Buys only</option>
            <option value="D">Sells only</option>
          </select>
        </div>

        <div>
          <label className="text-xs text-subtext block mb-1">Min Transaction Value</label>
          <select
            className="w-full bg-bg border border-border rounded px-3 py-2 text-sm text-text"
            value={filters.min_value}
            onChange={(e) => set("min_value", Number(e.target.value))}
          >
            <option value={25000}>$25,000+</option>
            <option value={100000}>$100,000+</option>
            <option value={500000}>$500,000+</option>
            <option value={1000000}>$1M+</option>
            <option value={5000000}>$5M+</option>
          </select>
        </div>

        <div>
          <label className="text-xs text-subtext block mb-1">Date Range</label>
          <select
            className="w-full bg-bg border border-border rounded px-3 py-2 text-sm text-text"
            value={filters.days}
            onChange={(e) => set("days", Number(e.target.value))}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last 12 months</option>
          </select>
        </div>

        <div>
          <label className="text-xs text-subtext block mb-1">Insider Role</label>
          <input
            type="text"
            placeholder="CEO, CFO, Director…"
            className="w-full bg-bg border border-border rounded px-3 py-2 text-sm text-text placeholder-muted"
            value={filters.role}
            onChange={(e) => set("role", e.target.value)}
          />
        </div>

        <div className="flex items-center gap-2 col-span-2 md:col-span-4">
          <input
            type="checkbox"
            id="exclude_awards"
            checked={filters.exclude_awards}
            onChange={(e) => set("exclude_awards", e.target.checked)}
            className="accent-accent"
          />
          <label htmlFor="exclude_awards" className="text-sm text-subtext">
            Exclude option grants / awards (show open-market only)
          </label>
        </div>
      </div>

      {data && (
        <div className="text-subtext text-xs">
          {data.total.toLocaleString()} results
        </div>
      )}

      <FilingsTable
        data={data}
        loading={loading}
        page={filters.page}
        onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
      />
    </div>
  );
}
