"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface Post {
  id: string;
  slug: string;
  title: string;
  content_md: string | null;
  meta_description: string | null;
  keywords: string[] | null;
  category: string | null;
  published_at: string | null;
}

export default function BlogPostPage() {
  const { slug } = useParams<{ slug: string }>();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/content/blog/${slug}`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setPost)
      .finally(() => setLoading(false));
  }, [slug]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-xl font-bold text-indigo-600">Resume Optimizer</Link>
          <Link href="/blog" className="text-sm text-gray-600 hover:text-gray-900">← Blog</Link>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-4 py-12">
        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : !post ? (
          <p className="text-red-600">Post not found.</p>
        ) : (
          <article>
            {post.category && (
              <p className="mb-2 text-xs font-medium uppercase text-indigo-600">{post.category}</p>
            )}
            <h1 className="mb-4 text-3xl font-bold text-gray-900">{post.title}</h1>
            {post.published_at && (
              <p className="mb-8 text-sm text-gray-500">{new Date(post.published_at).toLocaleDateString()}</p>
            )}
            {post.content_md ? (
              <div className="prose prose-gray max-w-none">
                {post.content_md.split("\n").map((line, i) => {
                  if (line.startsWith("## ")) return <h2 key={i} className="mt-8 mb-4 text-xl font-bold">{line.slice(3)}</h2>;
                  if (line.startsWith("# ")) return <h1 key={i} className="mt-8 mb-4 text-2xl font-bold">{line.slice(2)}</h1>;
                  if (line.trim() === "") return <br key={i} />;
                  return <p key={i} className="mb-4 text-gray-700 leading-relaxed">{line}</p>;
                })}
              </div>
            ) : (
              <p className="text-gray-400 italic">No content yet.</p>
            )}
          </article>
        )}
      </div>
    </div>
  );
}
