import type { MetadataRoute } from "next";
import { getPosts } from "@/lib/blog-server";

const SITE = "https://applystudio.app";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const entries: MetadataRoute.Sitemap = [
    { url: SITE, lastModified: now, changeFrequency: "weekly", priority: 1 },
    { url: `${SITE}/pricing`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${SITE}/blog`, lastModified: now, changeFrequency: "weekly", priority: 0.9 },
  ];

  // Posts come from the backend; if it is unreachable the sitemap degrades to
  // the base routes rather than failing (getPosts never throws).
  const posts = await getPosts();
  for (const post of posts) {
    entries.push({
      url: `${SITE}/blog/${post.slug}`,
      lastModified: post.published_at ? new Date(post.published_at) : now,
      changeFrequency: "monthly",
      priority: 0.7,
    });
  }
  return entries;
}