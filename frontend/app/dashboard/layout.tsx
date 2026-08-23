import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import Link from "next/link";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession(authOptions);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="mx-auto max-w-7xl px-4">
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-6">
              <Link href="/" className="text-lg font-bold text-indigo-600">
                Resume Optimizer
              </Link>
              <nav className="hidden sm:flex items-center gap-4">
                <Link href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">
                  Resumes
                </Link>
                <Link href="/dashboard/optimizations" className="text-sm text-gray-600 hover:text-gray-900">
                  Optimizations
                </Link>
                <Link href="/dashboard/jds/new" className="text-sm text-gray-600 hover:text-gray-900">
                  Add JD
                </Link>
                <Link href="/pricing" className="text-sm text-gray-600 hover:text-gray-900">
                  Pricing
                </Link>
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/dashboard/account" className="text-sm text-gray-600 hover:text-gray-900">
                {session?.user?.email}
              </Link>
              <Link href="/api/auth/signout" className="text-sm text-red-600 hover:underline">
                Sign out
              </Link>
            </div>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  );
}
