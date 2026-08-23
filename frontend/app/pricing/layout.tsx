import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing | Resume Optimizer",
  description:
    "Free resume optimization with 3 ATS-scored rewrites a month. Upgrade for unlimited AI rewrites, cover letters, and multiple resume versions. Cancel anytime.",
};

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}