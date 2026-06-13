"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import FilingsTable from "@/components/tables/FilingsTable";
import BuySellChart from "@/components/charts/BuySellChart";
import { apiFetch } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";

export default function CompanyPage() {
  const { ticker } = useParams<{ ticker: string }>();
  const [data, setData] = useState<any>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [thirddg, setThirddg] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ticker) return;
    const t = ticker.toUpperCase();
    Promise.all([
      apiFetch(`/api/form4/company/${t}?days=365`),
      apiFetch(`/api/form4/buy-sell-ratio/${t}?days=365`),
      apiFetch(`/api/13dg/company/${t}?days=1095`),
    ]).then(([company, chart, dg]) => {
      setData(company);
      setChartData(chart);
      setThirddg(dg);
      setLoading(false);
    });
  }, [ticker]);

  if (loading) return <div className="text-subtext p-8">Loading...</div>;
  if (!data) return <div className="text-danger p-8">No data found for {ticker}</div>;

  const s = data.summary;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border border-border rounded-xl p-6 bg-surface">
        <div className="flex items-start justify-between">
          <div>
            <span className="font-mono text-accent text-xl font-bold">{data.ticker}</span>
            <h1 className="text-xl font-semibold text-text mt-1">{data.company_name}</h1>
          </div>
          <a
            href={`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=${data.ticker}&type=4&dateb=&owner=include&count=40`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-subtext hover:text-accent border border-border rounded px-3 py-1"
          >
            View on EDGAR →
          </a>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
          {[
            { label: "Total Filings", value: formatNumber(s.total_filings) },
            { label: "Buy Transactions", value: formatNumber(s.buy_count), color: "text-accent" },
            { label: "Sell Transactions", value: formatNumber(s.sell_count), color: "text-danger" },
            { label: "Buy Volume", value: formatCurrency(s.buy_value), color: "text-accent" },
            { label: "Sell Volume", value: formatCurrency(s.sell_value), color: "text-danger" },
          ].map((stat) => (
            <div key={stat.label} className="bg-bg rounded-lg p-3 border border-border">
              <div className="text-subtext text-xs">{stat.label}</div>
              <div className={`text-lg font-mono font-semibold mt-1 ${stat.color || "text-text"}`}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Buy/Sell chart */}
      {chartData.length > 0 && (
        <div className="border border-border rounded-xl p-6 bg-surface">
          <h2 className="text-sm font-semibold text-subtext uppercase tracking-wider mb-4">
            Monthly Buy / Sell Volume
          </h2>
          <BuySellChart data={chartData} />
        </div>
      )}

      {/* Form 4 table */}
      <div className="border border-border rounded-xl p-6 bg-surface">
        <h2 className="text-sm font-semibold text-subtext uppercase tracking-wider mb-4">
          Form 4 Filings (Last 12 months)
        </h2>
        <FilingsTable data={{ items: data.filings, total: data.filings.length }} loading={false} />
      </div>

      {/* 13D/13G table */}
      {thirddg?.filings?.length > 0 && (
        <div className="border border-border rounded-xl p-6 bg-surface">
          <h2 className="text-sm font-semibold text-subtext uppercase tracking-wider mb-4">
            13D / 13G Filings
          </h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-subtext text-xs border-b border-border">
                <th className="text-left py-2">Form</th>
                <th className="text-left py-2">Filer</th>
                <th className="text-right py-2">% Owned</th>
                <th className="text-right py-2">Shares</th>
                <th className="text-right py-2">Filed</th>
                <th className="text-right py-2">Link</th>
              </tr>
            </thead>
            <tbody>
              {thirddg.filings.map((f: any) => (
                <tr key={f.id} className="border-b border-border table-row-hover">
                  <td className="py-2 font-mono text-xs text-subtext">{f.form_type}</td>
                  <td className="py-2">{f.filer_name}</td>
                  <td className="py-2 text-right font-mono">
                    {f.percent_owned != null ? `${Number(f.percent_owned).toFixed(2)}%` : "—"}
                  </td>
                  <td className="py-2 text-right font-mono">
                    {f.shares_owned != null ? formatNumber(f.shares_owned) : "—"}
                  </td>
                  <td className="py-2 text-right text-subtext">
                    {f.filing_date ? new Date(f.filing_date).toLocaleDateString() : "—"}
                  </td>
                  <td className="py-2 text-right">
                    {f.form_url && (
                      <a href={f.form_url} target="_blank" rel="noopener noreferrer"
                        className="text-accent hover:underline text-xs">SEC →</a>
                    )}
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
