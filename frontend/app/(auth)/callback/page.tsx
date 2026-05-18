export default function CallbackPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="mb-2 text-2xl font-bold">Check your email</h1>
        <p className="text-gray-600">A sign in link has been sent to your email address.</p>
        <p className="mt-4 text-sm text-gray-500">
          <a href="/login" className="text-indigo-600 hover:underline">Back to sign in</a>
        </p>
      </div>
    </div>
  );
}
