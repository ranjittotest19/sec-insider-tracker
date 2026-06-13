"use client";
import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

export default function Page13DG() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ form_type: "", days: 90, page: 1 });

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({
      ...(filters.form_type && { form_type: filters.form_type }),
      days: String(filters.days),
      page: String(filters.page),
      limit: "50",
    });
    const res = await apiFetch(`/api/13dg/feed?${params}`);
    setData(res);
    setLoading(false);
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.ceil((data?.total || 0) / 50);

  return (
    <div className="space-y-6">
      <div className="border border-border rounded-xl p-6 bg-surface">
        <h1 className="text-xl font-bold">13D / 13G Filings</h1>
        <p className="text-subtext text-sm mt-1">
          Filings triggered when an investor crosses the 5% ownership threshold. 13D = activist intent, 13G = passive.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="flex rounded-lg border border-border overflow-hidden text-sm">
          {["", "SC 13D", "SC 13G", "SC 13D/A", "SC 13G/A"].map((v) => (
            <button key={v}
              onClick={() => setFilters(f => ({ ...f, form_type: v, page: 1 }))}
              className={`px-3 py-1.5 transition-colors ${filters.form_type === v ? "bg-border text-text font-semibold" : "text-subtext hover:text-text"}`}
            >
              {v || "All"}
            </button>
          ))}
        </div>
        <select
          className="bg-surface border border-border rounded-lg px-3 py-1.5 text-sm text-text"
          value={filters.days}
          onChange={(e) => setFilters(f => ({ ...f, days: Number(e.target.value), page: 1 }))}
        >
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      {/* Table */}
      <div className="border border-border rounded-xl bg-surface overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-subtext text-sm animate-pulse">Loading…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-xs text-subtext uppercase tracking-wider">
                  <th className="text-left px-4 py-3">Form</th>
                  <th className="text-left px-4 py-3">Ticker</th>
                  <th className="text-left px-4 py-3">Subject Company</th>
                  <th className="text-left px-4 py-3">Filer</th>
                  <th className="text-right px-4 py-3">% Owned</th>
                  <th className="text-right px-4 py-3">Shares</th>
                  <th className="text-right px-4 py-3">Filed</th>
                  <th className="text-right px-4 py-3">Link</th>
                </tr>
              </thead>
              <tbody>
                {data?.items?.map((f: any) => (
                  <tr key={f.id} className="border-b border-border table-row-hover">
                    <td className="px-4 py-3 font-mono text-xs text-subtext">{f.form_type}</td>
                    <td className="px-4 py-3 font-mono">
                      {f.subject_ticker ? (
                        <Link href={`/company/${f.subject_ticker}`} className="text-accent hover:underline font-semibold">
                          {f.subject_ticker}
                        </Link>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-3 text-subtext truncate max-w-[200px]">{f.subject_company || "—"}</td>
                    <td className="px-4 py-3">{f.filer_name || "—"}</td>
                    <td className="px-4 py-3 text-right font-mono text-xs">
                      {f.percent_owned != null ? `${Number(f.percent_owned).toFixed(2)}%` : "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs">
                      {f.shares_owned != null ? Number(f.shares_owned).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-3 text-right text-subtext text-xs">
                      {f.filing_date ? new Date(f.filing_date).toLocaleDateString("en-CA") : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {f.form_url ? (
                        <a href={f.form_url} target="_blank" rel="noopener noreferrer"
                          className="text-accent hover:underline text-xs">SEC →</a>
                      ) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border text-sm">
            <span className="text-subtext text-xs">{data?.total?.toLocaleString()} results</span>
            <div className="flex items-center gap-2">
              <button disabled={filters.page <= 1}
                onClick={() => setFilters(f => ({ ...f, page: f.page - 1 }))}
                className="px-3 py-1 rounded border border-border text-subtext hover:text-text disabled:opacity-30">← Prev</button>
              <span className="text-subtext text-xs">Page {filters.page} / {totalPages}</span>
              <button disabled={filters.page >= totalPages}
                onClick={() => setFilters(f => ({ ...f, page: f.page + 1 }))}
                className="px-3 py-1 rounded border border-border text-subtext hover:text-text disabled:opacity-30">Next →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
