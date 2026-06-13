"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import FilingsTable from "@/components/tables/FilingsTable";
import { apiFetch } from "@/lib/api";

export default function InsiderPage() {
  const { cik } = useParams<{ cik: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!cik) return;
    apiFetch(`/api/form4/insider/${cik}`).then((r) => {
      setData(r);
      setLoading(false);
    });
  }, [cik]);

  if (loading) return <div className="text-subtext p-8">Loading…</div>;
  if (!data) return <div className="text-danger p-8">Insider not found.</div>;

  const buys = data.filings.filter((f: any) => f.txn_type === "A");
  const sells = data.filings.filter((f: any) => f.txn_type === "D");

  return (
    <div className="space-y-6">
      <div className="border border-border rounded-xl p-6 bg-surface">
        <h1 className="text-xl font-bold">{data.insider_name}</h1>
        <p className="text-subtext text-xs mt-1 font-mono">CIK: {data.insider_cik}</p>
        <div className="flex gap-4 mt-4 text-sm">
          <span className="text-accent">{buys.length} buys</span>
          <span className="text-danger">{sells.length} sells</span>
          <span className="text-subtext">{data.filings.length} total transactions (3 years)</span>
        </div>
      </div>
      <FilingsTable data={{ items: data.filings, total: data.filings.length }} loading={false} />
    </div>
  );
}
