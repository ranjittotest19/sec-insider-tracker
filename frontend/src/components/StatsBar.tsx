"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { formatCurrency } from "@/lib/format";

export default function StatsBar() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      apiFetch("/api/form4/feed?days=1&limit=1"),
      apiFetch("/api/form4/feed?days=1&txn_type=A&limit=1"),
      apiFetch("/api/form4/feed?days=1&txn_type=D&limit=1"),
    ]).then(([all, buys, sells]) => {
      setStats({ today: all.total, buys: buys.total, sells: sells.total });
    });
  }, []);

  if (!stats) return null;

  return (
    <div className="grid grid-cols-3 gap-4">
      {[
        { label: "Filings Today", value: stats.today?.toLocaleString() || "—" },
        { label: "Buys Today", value: stats.buys?.toLocaleString() || "—", color: "text-accent" },
        { label: "Sells Today", value: stats.sells?.toLocaleString() || "—", color: "text-danger" },
      ].map((s) => (
        <div key={s.label} className="border border-border rounded-xl p-4 bg-surface text-center">
          <div className="text-xs text-subtext">{s.label}</div>
          <div className={`text-2xl font-mono font-bold mt-1 ${s.color || "text-text"}`}>{s.value}</div>
        </div>
      ))}
    </div>
  );
}
