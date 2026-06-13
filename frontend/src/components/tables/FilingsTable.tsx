"use client";
import Link from "next/link";
import { formatCurrency, formatNumber, txnLabel, txnBadgeClass } from "@/lib/format";

interface Props {
  data: any;
  loading: boolean;
  page?: number;
  onPageChange?: (p: number) => void;
}

export default function FilingsTable({ data, loading, page = 1, onPageChange }: Props) {
  if (loading) return (
    <div className="border border-border rounded-xl bg-surface p-8 text-center text-subtext text-sm animate-pulse">
      Loading filings…
    </div>
  );

  if (!data?.items?.length) return (
    <div className="border border-border rounded-xl bg-surface p-8 text-center text-subtext text-sm">
      No filings found. Try adjusting your filters.
    </div>
  );

  const totalPages = Math.ceil((data.total || 0) / (data.limit || 50));

  return (
    <div className="border border-border rounded-xl bg-surface overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-subtext uppercase tracking-wider">
              <th className="text-left px-4 py-3">Ticker</th>
              <th className="text-left px-4 py-3 hidden md:table-cell">Company</th>
              <th className="text-left px-4 py-3">Insider</th>
              <th className="text-left px-4 py-3 hidden lg:table-cell">Title</th>
              <th className="text-center px-4 py-3">Type</th>
              <th className="text-right px-4 py-3">Shares</th>
              <th className="text-right px-4 py-3">Price</th>
              <th className="text-right px-4 py-3">Value</th>
              <th className="text-right px-4 py-3">Date</th>
              <th className="text-right px-4 py-3 hidden lg:table-cell">Filed</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((f: any) => (
              <tr key={f.id || f.accession_number} className="border-b border-border table-row-hover">
                <td className="px-4 py-3 font-mono">
                  <Link href={`/company/${f.ticker}`} className="text-accent hover:underline font-semibold">
                    {f.ticker || "—"}
                  </Link>
                </td>
                <td className="px-4 py-3 text-subtext truncate max-w-[180px] hidden md:table-cell">
                  {f.company_name}
                </td>
                <td className="px-4 py-3">
                  <Link href={`/insider/${f.insider_cik}`} className="hover:text-accent">
                    {f.insider_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-subtext text-xs hidden lg:table-cell">
                  {f.officer_title || (f.is_director === "1" ? "Director" : "—")}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${txnBadgeClass(f.txn_type)}`}>
                    {txnLabel(f.txn_type, f.txn_code)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-mono text-xs">
                  {f.shares != null ? formatNumber(f.shares) : "—"}
                </td>
                <td className="px-4 py-3 text-right font-mono text-xs">
                  {f.price_per_share && Number(f.price_per_share) > 0
                    ? `$${Number(f.price_per_share).toFixed(2)}`
                    : "—"}
                </td>
                <td className={`px-4 py-3 text-right font-mono text-xs font-semibold ${
                  f.txn_type === "A" ? "text-accent" : f.txn_type === "D" ? "text-danger" : "text-text"
                }`}>
                  {f.total_value && Number(f.total_value) > 0 ? formatCurrency(f.total_value) : "—"}
                </td>
                <td className="px-4 py-3 text-right text-subtext text-xs">
                  {f.txn_date ? new Date(f.txn_date).toLocaleDateString("en-CA") : "—"}
                </td>
                <td className="px-4 py-3 text-right hidden lg:table-cell">
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

      {/* Pagination */}
      {totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-border text-sm">
          <span className="text-subtext text-xs">
            {data.total?.toLocaleString()} results
          </span>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="px-3 py-1 rounded border border-border text-subtext hover:text-text disabled:opacity-30"
            >
              ← Prev
            </button>
            <span className="text-subtext text-xs">Page {page} / {totalPages}</span>
            <button
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="px-3 py-1 rounded border border-border text-subtext hover:text-text disabled:opacity-30"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
