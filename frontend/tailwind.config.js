/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0e17",
        surface: "#111827",
        border: "#1f2937",
        accent: "#22c55e",      // green — buys
        danger: "#ef4444",      // red — sells
        muted: "#6b7280",
        text: "#f1f5f9",
        subtext: "#94a3b8",
      },
      fontFamily: {
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
        sans: ["var(--font-sans)", "Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
