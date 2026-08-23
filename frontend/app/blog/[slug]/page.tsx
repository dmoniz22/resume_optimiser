import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getPost, cleanContent } from "@/lib/blog-server";

export const dynamic = "force-dynamic";

const SITE = "https://applystudio.app";

// SEO-tag hygiene: keep <title> <= 60 chars and meta description <= 155.
// Clamping happens in the tag only — the on-page content is untouched.
function seoTitle(title: string): string {
  const branded = `${title} | Resume Optimizer`;
  if (branded.length <= 60) return branded;
  const cleaned = title.length > 52 ? `${title.slice(0, 52).trimEnd()}…` : title;
  return cleaned.length <= 60 ? cleaned : `${cleaned.slice(0, 57).trimEnd()}…`;
}

function seoDescription(desc: string | null): string | undefined {
  if (!desc) return undefined;
  return desc.length > 155 ? `${desc.slice(0, 155).trimEnd()}…` : desc;
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const post = await getPost(params.slug);
  if (!post) {
    return { title: "Post Not Found | Resume Optimizer" };
  }
  const title = seoTitle(post.title);
  const description = seoDescription(post.meta_description);
  return {
    title,
    description,
    alternates: { canonical: `${SITE}/blog/${post.slug}` },
    openGraph: {
      title,
      description,
      url: `${SITE}/blog/${post.slug}`,
      type: "article",
    },
  };
}

export default async function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug);
  if (!post) notFound();

  return (
    <div className="min-h-screen bg-gray-50">
      <style>{`
        .blog-content pre code {
          background: transparent !important;
          padding: 0 !important;
        }
        .blog-content table {
          border-collapse: collapse;
          width: 100%;
        }
        .blog-content th {
          border: 1px solid #d1d5db;
          background: #f3f4f6;
          padding: 0.5rem 0.75rem;
          text-align: left;
          font-size: 0.875rem;
          font-weight: 600;
        }
        .blog-content td {
          border: 1px solid #d1d5db;
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
        }
      `}</style>
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-xl font-bold text-indigo-600">Resume Optimizer</Link>
          <div className="flex items-center gap-4">
            <Link href="/pricing" className="text-sm text-gray-600 hover:text-gray-900">Pricing</Link>
            <Link href="/blog" className="text-sm text-gray-600 hover:text-gray-900">← Blog</Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-4 py-12">
        <article>
          {post.category && (
            <p className="mb-2 text-xs font-medium uppercase text-indigo-600">{post.category}</p>
          )}
          <h1 className="mb-4 text-3xl font-bold text-gray-900">{post.title}</h1>
          {post.published_at && (
            <p className="mb-8 text-sm text-gray-500">{new Date(post.published_at).toLocaleDateString()}</p>
          )}
          {post.content_md ? (
            <div className="blog-content prose prose-gray max-w-none
              prose-headings:scroll-mt-20
              prose-a:text-indigo-600 prose-a:no-underline hover:prose-a:underline
              prose-code:rounded prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:text-sm prose-code:font-normal
              prose-pre:rounded-lg prose-pre:bg-gray-900 prose-pre:text-gray-100
              prose-blockquote:border-l-4 prose-blockquote:border-indigo-300 prose-blockquote:bg-indigo-50 prose-blockquote:px-4 prose-blockquote:py-1 prose-blockquote:italic
            ">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Post bodies use # for section headings; demote to h2 so the
                  // article title stays the page's single H1 (SEO hygiene).
                  h1: (props) => <h2 className="mt-8 mb-4 text-2xl font-bold" {...props} />,
                }}
              >
                {cleanContent(post.content_md)}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="text-gray-400 italic">No content yet.</p>
          )}
        </article>
      </div>
    </div>
  );
}