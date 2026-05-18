"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";

interface AccountData {
  user: { id: string; email: string; full_name: string | null; created_at: string };
  tier: string;
  tier_features: Record<string, any> | null;
  credits_used_this_month: number;
  credits_limit: number | null;
  subscription_status: string | null;
}

export default function AccountPage() {
  const { data: session } = useSession();
  const [account, setAccount] = useState<AccountData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/auth/account", {
      headers: { Authorization: `Bearer ${(session as any)?.accessToken || ""}` },
    })
      .then((r) => r.json())
      .then(setAccount)
      .finally(() => setLoading(false));
  }, [session]);

  if (loading) return <p className="text-gray-500 p-4">Loading...</p>;
  if (!account) return <p className="text-red-600 p-4">Could not load account.</p>;

  const tierColors: Record<string, string> = {
    free: "bg-gray-100 text-gray-600",
    pro: "bg-indigo-100 text-indigo-700",
    career: "bg-purple-100 text-purple-700",
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Account</h1>

      <div className="space-y-4">
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h2 className="mb-4 font-semibold text-gray-900">Profile</h2>
          <div className="space-y-2 text-sm">
            <p><span className="text-gray-500">Email:</span> <span className="text-gray-900">{account.user.email}</span></p>
            <p><span className="text-gray-500">Name:</span> <span className="text-gray-900">{account.user.full_name || "—"}</span></p>
            <p><span className="text-gray-500">Joined:</span> <span className="text-gray-900">{new Date(account.user.created_at).toLocaleDateString()}</span></p>
          </div>
        </div>

        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h2 className="mb-4 font-semibold text-gray-900">Plan</h2>
          <div className="flex items-center gap-3 mb-3">
            <span className={`rounded-full px-3 py-1 text-sm font-medium capitalize ${tierColors[account.tier] || tierColors.free}`}>
              {account.tier}
            </span>
            {account.subscription_status && (
              <span className="text-xs text-green-600 capitalize">{account.subscription_status}</span>
            )}
          </div>
          <p className="text-sm text-gray-600 mb-4">
            {account.credits_used_this_month} of {account.credits_limit ?? "unlimited"} optimizations used this month
          </p>
          {account.tier === "free" && (
            <Link href="/pricing" className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 inline-block">
              Upgrade Plan
            </Link>
          )}
          {(account.tier === "pro" || account.tier === "career") && (
            <button
              onClick={async () => {
                const res = await fetch("/api/v1/stripe/portal", {
                  headers: { Authorization: `Bearer ${(session as any)?.accessToken || ""}` },
                });
                if (res.redirected) window.location.href = res.url;
              }}
              className="rounded-md border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
            >
              Manage Billing
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
