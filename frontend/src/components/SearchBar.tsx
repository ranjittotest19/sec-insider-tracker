"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any>(null);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (query.length < 1) { setResults(null); return; }
    const t = setTimeout(async () => {
      const res = await apiFetch(`/api/search/?q=${encodeURIComponent(query)}`);
      setResults(res);
      setOpen(true);
    }, 250);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const goTicker = (ticker: string) => {
    setQuery(""); setOpen(false);
    router.push(`/company/${ticker}`);
  };

  const goInsider = (cik: string) => {
    setQuery(""); setOpen(false);
    router.push(`/insider/${cik}`);
  };

  return (
    <div ref={ref} className="relative">
      <input
        type="text"
        placeholder="Search ticker or insider…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full bg-bg border border-border rounded-lg px-3 py-1.5 text-sm text-text placeholder-muted focus:outline-none focus:border-accent/60"
      />
      {open && results && (
        <div className="absolute top-full mt-1 w-80 bg-surface border border-border rounded-lg shadow-xl z-50 overflow-hidden">
          {results.tickers?.length > 0 && (
            <div>
              <div className="px-3 py-1.5 text-xs text-muted uppercase tracking-wider border-b border-border">
                Companies
              </div>
              {results.tickers.map((t: any) => (
                <button
                  key={t.ticker}
                  onClick={() => goTicker(t.ticker)}
                  className="w-full text-left px-3 py-2 hover:bg-border/50 flex items-center gap-3"
                >
                  <span className="font-mono text-accent text-sm w-14 shrink-0">{t.ticker}</span>
                  <span className="text-subtext text-sm truncate">{t.company_name}</span>
                </button>
              ))}
            </div>
          )}
          {results.insiders?.length > 0 && (
            <div>
              <div className="px-3 py-1.5 text-xs text-muted uppercase tracking-wider border-b border-border">
                Insiders
              </div>
              {results.insiders.map((i: any) => (
                <button
                  key={i.insider_cik}
                  onClick={() => goInsider(i.insider_cik)}
                  className="w-full text-left px-3 py-2 hover:bg-border/50"
                >
                  <span className="text-sm text-text">{i.insider_name}</span>
                </button>
              ))}
            </div>
          )}
          {!results.tickers?.length && !results.insiders?.length && (
            <div className="px-3 py-3 text-sm text-muted">No results</div>
          )}
        </div>
      )}
    </div>
  );
}
