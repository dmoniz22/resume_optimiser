"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

export default function UploadPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) {
      if (f.size > 5 * 1024 * 1024) {
        setError("File too large (max 5MB)");
        return;
      }
      if (!["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"].includes(f.type)) {
        setError("Only PDF, DOCX, and TXT files are accepted");
        return;
      }
      setFile(f);
      setError("");
      if (!title) setTitle(f.name.replace(/\.[^/.]+$/, ""));
    }
  }, [title]);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title || file.name);

    try {
      const res = await fetch("/api/v1/resumes", {
        method: "POST",
        headers: { Authorization: `Bearer ${(session as any)?.accessToken || ""}` },
        body: formData,
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Upload Resume</h1>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      <form onSubmit={handleUpload}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Resume Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full max-w-md rounded-md border px-3 py-2"
            placeholder="My Software Engineer Resume"
          />
        </div>

        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          className="mb-4 flex h-48 w-full max-w-md cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-white hover:border-indigo-400"
        >
          {file ? (
            <div className="text-center">
              <p className="text-sm font-medium text-gray-900">{file.name}</p>
              <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-600">Drag and drop your resume here</p>
              <p className="mt-1 text-xs text-gray-400">PDF, DOCX, or TXT (max 5MB)</p>
              <label className="mt-4 cursor-pointer rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">
                Browse Files
                <input
                  type="file"
                  className="hidden"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) {
                      setFile(f);
                      setError("");
                      if (!title) setTitle(f.name.replace(/\.[^/.]+$/, ""));
                    }
                  }}
                />
              </label>
            </>
          )}
        </div>

        <button
          type="submit"
          disabled={!file || uploading}
          className="rounded-md bg-indigo-600 px-6 py-2 text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Upload Resume"}
        </button>
      </form>
    </div>
  );
}
