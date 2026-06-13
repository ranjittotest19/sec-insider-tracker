"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { formatCurrency } from "@/lib/format";

export default function ClusterBuysPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);
  const [minInsiders, setMinInsiders] = useState(2);

  useEffect(() => {
    setLoading(true);
    apiFetch(`/api/form4/cluster-buys?days=${days}&min_insiders=${minInsiders}&min_value=50000`)
      .then((r) => { setData(r); setLoading(false); });
  }, [days, minInsiders]);

  return (
    <div className="space-y-6">
      <div className="border border-border rounded-xl p-6 bg-surface">
        <h1 className="text-xl font-bold">Cluster Buys</h1>
        <p className="text-subtext text-sm mt-1">
          Stocks where multiple insiders are buying simultaneously — historically a high-conviction signal.
        </p>
      </div>

      <div className="flex gap-3 flex-wrap">
        <select className="bg-surface border border-border rounded-lg px-3 py-1.5 text-sm text-text"
          value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={3}>Last 3 days</option>
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
        </select>
        <select className="bg-surface border border-border rounded-lg px-3 py-1.5 text-sm text-text"
          value={minInsiders} onChange={(e) => setMinInsiders(Number(e.target.value))}>
          <option value={2}>2+ insiders</option>
          <option value={3}>3+ insiders</option>
          <option value={4}>4+ insiders</option>
        </select>
      </div>

      {loading ? (
        <div className="border border-border rounded-xl bg-surface p-8 text-center text-subtext animate-pulse">
          Loading…
        </div>
      ) : data.length === 0 ? (
        <div className="border border-border rounded-xl bg-surface p-8 text-center text-subtext">
          No cluster buys in this window. Try widening the date range.
        </div>
      ) : (
        <div className="border border-border rounded-xl bg-surface overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-subtext uppercase tracking-wider">
                <th className="text-left px-4 py-3">Ticker</th>
                <th className="text-left px-4 py-3 hidden md:table-cell">Company</th>
                <th className="text-center px-4 py-3">Insiders</th>
                <th className="text-right px-4 py-3">Total Buy Value</th>
                <th className="text-right px-4 py-3">Latest Buy</th>
              </tr>
            </thead>
            <tbody>
              {data.map((r: any) => (
                <tr key={r.ticker} className="border-b border-border table-row-hover">
                  <td className="px-4 py-3 font-mono">
                    <Link href={`/company/${r.ticker}`} className="text-accent hover:underline font-bold">
                      {r.ticker}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-subtext hidden md:table-cell">{r.company_name}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="bg-accent/15 text-accent font-mono font-bold px-2 py-0.5 rounded text-xs">
                      {r.insider_count}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-accent font-semibold">
                    {formatCurrency(r.total_buy_value)}
                  </td>
                  <td className="px-4 py-3 text-right text-subtext text-xs">
                    {r.latest_buy ? new Date(r.latest_buy).toLocaleDateString("en-CA") : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
