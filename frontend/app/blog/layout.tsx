import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Resume Advice Blog | Resume Optimizer",
  description:
    "ATS resume tips, AI job-search guides, and practical career advice from the Resume Optimizer team — steps you can apply in minutes.",
};

export default function BlogLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}