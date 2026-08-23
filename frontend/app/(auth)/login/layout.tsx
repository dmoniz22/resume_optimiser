import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In | Resume Optimizer",
  description: "Sign in to your Resume Optimizer account to rewrite your resume with AI, get an instant ATS score, and land more interviews.",
  robots: { index: false, follow: false },
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}