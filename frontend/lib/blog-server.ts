// Server-only helpers for blog content. Used by blog pages and sitemap.
// Default hostname matches the live rewrite target in next.config.js
// (http://resume_optimiser-backend-1:8000) so this resolves inside the app
// container. Override with BACKEND_URL for other environments.
const BACKEND = process.env.BACKEND_URL ?? "http://resume_optimiser-backend-1:8000";

export interface Post {
  id: string;
  slug: string;
  title: string;
  content_md: string | null;
  meta_description: string | null;
  keywords: string[] | null;
  category: string | null;
  published_at: string | null;
}

// Defensive by design: never throw, never 500 the page. Missing data renders
// a degraded state instead (consistent with the seo-ops honesty rules).
export async function getPosts(): Promise<Post[]> {
  try {
    const res = await fetch(`${BACKEND}/api/v1/content/blog`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : data.posts ?? [];
  } catch {
    return [];
  }
}

export async function getPost(slug: string): Promise<Post | null> {
  try {
    const res = await fetch(`${BACKEND}/api/v1/content/blog/${encodeURIComponent(slug)}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// Strip YAML frontmatter (--- ... ---) and the first # heading
// (since the title is already rendered from the DB field)
export function cleanContent(md: string): string {
  return md
    .replace(/^---[\s\S]*?---\n*/, "")
    .replace(/^\s*# .+\n*/m, "");
}