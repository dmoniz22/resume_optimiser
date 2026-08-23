import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create Your Account | Resume Optimizer",
  description: "Create a free Resume Optimizer account to tailor your resume to any job description with AI, score it against ATS filters, and export a polished PDF.",
  robots: { index: false, follow: false },
};

export default function SignupLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}