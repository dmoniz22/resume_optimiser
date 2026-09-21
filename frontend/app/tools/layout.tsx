import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Free ATS Keyword Gap Checker | Resume Optimizer",
  description:
    "Paste your resume and any job description to see which ATS keywords you match and which you're missing — free, instant, and nothing leaves your browser.",
  alternates: { canonical: "https://applystudio.app/tools/keyword-gap" },
  openGraph: {
    title: "Free ATS Keyword Gap Checker | Resume Optimizer",
    description:
      "Paste your resume and any job description to see which ATS keywords you match and which you're missing — free and instant.",
    url: "https://applystudio.app/tools/keyword-gap",
    type: "website",
  },
};

export default function KeywordGapLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
