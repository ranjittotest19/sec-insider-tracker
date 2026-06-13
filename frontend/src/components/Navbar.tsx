"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import SearchBar from "./SearchBar";
import clsx from "clsx";

const NAV = [
  { href: "/", label: "Live Feed" },
  { href: "/screener", label: "Screener" },
  { href: "/13dg", label: "13D / 13G" },
  { href: "/cluster-buys", label: "Cluster Buys" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="border-b border-border bg-surface sticky top-0 z-50">
      <div className="max-w-screen-xl mx-auto px-4 h-14 flex items-center gap-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <span className="text-accent font-mono font-bold text-lg">⬡</span>
          <span className="font-semibold text-text text-sm hidden sm:block">InsiderTrack</span>
        </Link>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-1">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={clsx(
                "px-3 py-1.5 rounded text-sm transition-colors",
                pathname === n.href
                  ? "bg-accent/10 text-accent"
                  : "text-subtext hover:text-text hover:bg-border/50"
              )}
            >
              {n.label}
            </Link>
          ))}
        </nav>

        {/* Search */}
        <div className="ml-auto w-64">
          <SearchBar />
        </div>
      </div>
    </header>
  );
}
