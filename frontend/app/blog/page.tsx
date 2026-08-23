import Link from "next/link";
import { getPosts } from "@/lib/blog-server";

export const dynamic = "force-dynamic";

export default async function BlogPage() {
  const posts = await getPosts();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-xl font-bold text-indigo-600">Resume Optimizer</Link>
          <div className="flex items-center gap-4">
            <Link href="/blog" className="text-sm font-medium text-indigo-600">Blog</Link>
            <Link href="/pricing" className="text-sm text-gray-600 hover:text-gray-900">Pricing</Link>
            <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">Sign In</Link>
            <Link href="/signup" className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">Sign Up</Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-4 py-12">
        <h1 className="mb-2 text-4xl font-bold text-gray-900">Blog</h1>
        <p className="mb-8 text-gray-600">Resume tips, career advice, and industry insights.</p>

        {posts.length === 0 ? (
          <p className="text-gray-500">No posts yet. Check back soon.</p>
        ) : (
          <div className="grid gap-6 md:grid-cols-2">
            {posts.map((post) => (
              <Link
                key={post.id}
                href={`/blog/${post.slug}`}
                className="rounded-lg bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
              >
                {post.category && (
                  <p className="mb-1 text-xs font-medium uppercase text-indigo-600">{post.category}</p>
                )}
                <h2 className="mb-2 text-lg font-semibold text-gray-900">{post.title}</h2>
                {post.meta_description && (
                  <p className="text-sm text-gray-600 line-clamp-2">{post.meta_description}</p>
                )}
                {post.published_at && (
                  <p className="mt-3 text-xs text-gray-400">{new Date(post.published_at).toLocaleDateString()}</p>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}