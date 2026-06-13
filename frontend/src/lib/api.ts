const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch(path: string) {
  const res = await fetch(`${API_URL}${path}`, {
    next: { revalidate: 60 }, // 60s cache for Next.js server components
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
