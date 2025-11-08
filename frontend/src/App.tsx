import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE;

export default function App() {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [fg1, setFg1] = useState("#000000");
  const [fg2, setFg2] = useState("#000000");
  const [bg, setBg] = useState("#ffffff");
  const [gradient, setGradient] = useState(false);
  const [direction, setDirection] = useState("horizontal");
  const [qrSrc, setQrSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Step 1: Create QR entry in DB
      const res = await fetch(`${API_BASE}/api/qr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          target_url: url,
          note: "",
        }),
      });

      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      const data = await res.json();

      // Step 2: Generate QR image with color settings
      const qrUrl = `${API_BASE}/qr.png?data=${encodeURIComponent(
        `${API_BASE}/r/${data.slug}`
      )}&fg1=${encodeURIComponent(fg1)}&fg2=${encodeURIComponent(
        fg2
      )}&bg=${encodeURIComponent(bg)}&gradient=${gradient}&direction=${direction}`;

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
      {/* Left Form Pane */}
      <aside className="w-full md:w-1/3 bg-white p-6 shadow-md space-y-4">
        <h1 className="text-2xl font-bold text-indigo-700 mb-2">
          Kyu-AR Kowd <span className="text-sm text-gray-400">✨</span>
        </h1>
        <p className="text-xs text-gray-500 mb-4">
          Generate stylish QR codes with gradients & colors.
        </p>

        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full border rounded p-2 mt-1"
              placeholder="My Project QR"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Target URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full border rounded p-2 mt-1"
              placeholder="https://example.com"
              required
            />
          </div>

          {/* Foreground Options */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Foreground Color
            </label>
            <div className="flex items-center space-x-2">
              <label className="flex items-center space-x-1 text-sm">
                <input
                  type="radio"
                  checked={!gradient}
                  onChange={() => setGradient(false)}
                />
                <span>Single</span>
              </label>
              <label className="flex items-center space-x-1 text-sm">
                <input
                  type="radio"
                  checked={gradient}
                  onChange={() => setGradient(true)}
                />
                <span>Gradient</span>
              </label>
            </div>

            <div className="flex items-center space-x-2 mt-2">
              <input
                type="color"
                value={fg1}
                onChange={(e) => setFg1(e.target.value)}
                className="w-10 h-8"
              />
              {gradient && (
                <>
                  <input
                    type="color"
                    value={fg2}
                    onChange={(e) => setFg2(e.target.value)}
                    className="w-10 h-8"
                  />
                  <select
                    value={direction}
                    onChange={(e) => setDirection(e.target.value)}
                    className="border rounded p-1 text-sm"
                  >
                    <option value="horizontal">Horizontal</option>
                    <option value="vertical">Vertical</option>
                    <option value="radial">Radial</option>
                    <option value="square">Square</option>
                  </select>
                </>
              )}
            </div>
          </div>

          {/* Background */}
          <div>
            <label className="block text-sm font-medium">Background Color</label>
            <input
              type="color"
              value={bg}
              onChange={(e) => setBg(e.target.value)}
              className="w-10 h-8 mt-1"
            />
          </div>

          {/* Generate Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white py-2 rounded hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate QR"}
          </button>
        </form>

        {error && (
          <p className="mt-3 text-red-600 text-sm font-medium">{error}</p>
        )}
      </aside>

      {/* Right Preview Pane */}
      <main className="flex-1 flex flex-col items-center justify-center p-10">
        {qrSrc ? (
          <div className="flex flex-col items-center">
            <img
              src={qrSrc}
              alt="Generated QR"
              className="w-64 h-64 border rounded-lg shadow-lg"
            />
            <p className="text-xs text-gray-500 mt-2">
              Scan the code to test redirect.
            </p>
          </div>
        ) : (
          <div className="w-64 h-64 flex flex-col items-center justify-center border-2 border-dashed rounded-lg text-gray-400">
            <p className="text-sm text-gray-400">Placeholder QR Preview</p>
            <p className="text-[10px] mt-1">Fill the form and generate</p>
          </div>
        )}
      </main>
    </div>
  );
}
