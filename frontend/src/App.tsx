import { useState } from "react";

export default function App() {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [qrSrc, setQrSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/qr", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          target_url: url,
          note: "",
          type: "url",
        }),
      });

      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      const data = await res.json();

      const qrUrl = `http://127.0.0.1:8000/qr.png?data=http://127.0.0.1:8000/r/${data.slug}`;

      setQrSrc(qrUrl);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "QR generation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50 text-gray-800">
      {/* Left Pane */}
      <aside className="w-full md:w-1/3 bg-white p-6 shadow-md">
        <h1 className="text-2xl font-bold mb-4">Kyu-AR Kowd QR Generator</h1>
        <form onSubmit={handleGenerate} className="space-y-3">
          <div>
            <label className="block text-sm font-medium">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full border rounded p-2"
              placeholder="My QR Code"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Target URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full border rounded p-2"
              placeholder="https://example.com"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate QR"}
          </button>
        </form>

        {error && (
          <p className="mt-3 text-red-600 text-sm font-medium">{error}</p>
        )}
      </aside>

      {/* Right Pane */}
      <main className="flex-1 flex items-center justify-center p-10">
        {qrSrc ? (
          <img
            src={qrSrc}
            alt="Generated QR"
            className="w-64 h-64 border rounded-lg shadow-lg"
          />
        ) : (
          <div className="w-64 h-64 flex items-center justify-center border-2 border-dashed rounded-lg text-gray-400">
            Placeholder QR Preview
          </div>
        )}
      </main>
    </div>
  );
}
