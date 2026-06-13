"use client";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

const fmt = (v: number) =>
  v >= 1_000_000 ? `$${(v / 1_000_000).toFixed(1)}M` : `$${(v / 1_000).toFixed(0)}K`;

export default function BuySellChart({ data }: { data: any[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} barCategoryGap="30%">
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis dataKey="month" tick={{ fill: "#6b7280", fontSize: 11 }} />
        <YAxis tickFormatter={fmt} tick={{ fill: "#6b7280", fontSize: 11 }} width={60} />
        <Tooltip
          contentStyle={{ background: "#111827", border: "1px solid #1f2937", borderRadius: 8 }}
          formatter={(v: number, name: string) => [fmt(v), name === "buy_volume" ? "Buys" : "Sells"]}
          labelStyle={{ color: "#94a3b8" }}
        />
        <Legend formatter={(v) => v === "buy_volume" ? "Buys" : "Sells"} />
        <Bar dataKey="buy_volume" fill="#22c55e" radius={[3, 3, 0, 0]} />
        <Bar dataKey="sell_volume" fill="#ef4444" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
