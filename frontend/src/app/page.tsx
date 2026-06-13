"use client";
import { useState, useEffect, useCallback } from "react";
import FilingsTable from "@/components/tables/FilingsTable";
import FilterBar from "@/components/FilterBar";
import StatsBar from "@/components/StatsBar";
import { apiFetch } from "@/lib/api";

export default function HomePage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    txn_type: "",
    days: 30,
    min_value: 50000,
    page: 1,
  });

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({
      ...(filters.txn_type && { txn_type: filters.txn_type }),
      days: String(filters.days),
      min_value: String(filters.min_value),
      page: String(filters.page),
      limit: "50",
    });
    const res = await apiFetch(`/api/form4/feed?${params}`);
    setData(res);
    setLoading(false);
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="border border-border rounded-xl p-6 bg-surface">
        <h1 className="text-2xl font-bold text-text tracking-tight">
          SEC Insider Trading Feed
        </h1>
        <p className="text-subtext mt-1 text-sm">
          Real-time Form 4 filings and 13D/13G disclosures from EDGAR. Updated every 15 minutes.
        </p>
      </div>

      <StatsBar />

      <FilterBar filters={filters} onChange={(f) => setFilters({ ...f, page: 1 })} />

      <FilingsTable
        data={data}
        loading={loading}
        page={filters.page}
        onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
      />
    </div>
  );
}
