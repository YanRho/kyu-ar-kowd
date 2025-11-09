import { useState } from "react";

type QRType = "URL" | "WIFI" | "VCARD" | "TEXT";
type GradientType = "vertical" | "horizontal" | "radial";

export default function App() {
  const [type, setType] = useState<QRType>("URL");
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [ssid, setSsid] = useState("");
  const [password, setPassword] = useState("");
  const [encryption, setEncryption] = useState("WPA");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [content, setContent] = useState("");

  // 🎨 Color + gradient controls
  const [darkColor, setDarkColor] = useState("#00f6ff");
  const [lightColor, setLightColor] = useState("#ff005e");
  const [useGradient, setUseGradient] = useState(false);
  const [gradType, setGradType] = useState<GradientType>("vertical");

  const [qrSrc, setQrSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = import.meta.env.VITE_API_BASE;

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload: Record<string, unknown> = { title, type };

    if (type === "URL") payload.target_url = url;
    else if (type === "WIFI") payload.data = { ssid, password, encryption };
    else if (type === "VCARD") payload.data = { name, phone, email };
    else if (type === "TEXT") payload.data = { content };

    try {
      const res = await fetch(`${API_BASE}/api/qr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Request failed (${res.status})`);

      const data = (await res.json()) as { slug: string };

      const params = new URLSearchParams({
        slug: data.slug,
        dark_color: darkColor,
        light_color: lightColor,
        gradient: useGradient ? "true" : "false",
        grad_type: gradType,
      });
      setQrSrc(`${API_BASE}/qr.png?${params.toString()}`);
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
      else setError("QR generation failed");
    } finally {
      setLoading(false);
    }
  };

  // 🎨 Live gradient preview style
  const gradientStyle = {
    background: useGradient
      ? gradType === "horizontal"
        ? `linear-gradient(to right, ${darkColor}, ${lightColor})`
        : gradType === "radial"
        ? `radial-gradient(circle, ${darkColor}, ${lightColor})`
        : `linear-gradient(to bottom, ${darkColor}, ${lightColor})`
      : darkColor,
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-linear-to-b from-slate-900 to-slate-950 text-gray-200 font-sans">
      {/* LEFT: Form */}
      <aside className="w-full md:w-1/3 p-8 backdrop-blur-lg bg-white/5 border-r border-white/10 shadow-xl">
        <h1 className="text-3xl font-extrabold mb-6 bg-linear-to-r from-cyan-400 to-pink-500 bg-clip-text text-transparent">
          QR Generator
        </h1>

        <form onSubmit={handleGenerate} className="space-y-4">
          {/* QR Type */}
          <div>
            <label className="text-sm font-semibold text-gray-400">QR Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value as QRType)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200 focus:ring-2 focus:ring-cyan-500 outline-none"
            >
              <option value="URL">Website / URL</option>
              <option value="WIFI">Wi-Fi Login</option>
              <option value="VCARD">Contact Card (vCard)</option>
              <option value="TEXT">Plain Text</option>
            </select>
          </div>

          {/* Title */}
          <div>
            <label className="text-sm font-semibold text-gray-400">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200 focus:ring-2 focus:ring-cyan-500 outline-none"
              placeholder="My QR Code"
              required
            />
          </div>

          {/* Dynamic Fields */}
          {type === "URL" && (
            <div>
              <label className="text-sm font-semibold text-gray-400">Target URL</label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200 focus:ring-2 focus:ring-cyan-500 outline-none"
                placeholder="https://example.com"
                required
              />
            </div>
          )}

          {type === "WIFI" && (
            <>
              <div>
                <label className="text-sm font-semibold text-gray-400">Wi-Fi SSID</label>
                <input
                  type="text"
                  value={ssid}
                  onChange={(e) => setSsid(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200"
                  placeholder="HomeNetwork"
                />
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-400">Password</label>
                <input
                  type="text"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200"
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-400">Encryption</label>
                <select
                  value={encryption}
                  onChange={(e) => setEncryption(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200"
                >
                  <option value="WPA">WPA/WPA2</option>
                  <option value="WEP">WEP</option>
                  <option value="nopass">None</option>
                </select>
              </div>
            </>
          )}

          {type === "VCARD" && (
            <>
              <div>
                <label className="text-sm font-semibold text-gray-400">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-400">Phone</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200"
                  placeholder="+1 555 123 4567"
                />
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-400">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200"
                  placeholder="you@example.com"
                />
              </div>
            </>
          )}

          {type === "TEXT" && (
            <div>
              <label className="text-sm font-semibold text-gray-400">Text Content</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200"
                rows={3}
                placeholder="Write your message..."
              />
            </div>
          )}

          {/* 🎨 Colors */}
          <div className="pt-4 border-t border-slate-700">
            <h2 className="font-semibold mb-3 text-gray-300">Customize Colors</h2>

            <div className="flex items-center gap-3 mb-2">
              <input type="color" value={darkColor} onChange={(e) => setDarkColor(e.target.value)} />
              <label className="text-sm">Dark Color</label>
            </div>

            <div className="flex items-center gap-3 mb-3">
              <input
                type="color"
                value={lightColor}
                onChange={(e) => setLightColor(e.target.value)}
              />
              <label className="text-sm">Light Color</label>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={useGradient}
                onChange={() => setUseGradient(!useGradient)}
              />
              <label className="text-sm font-medium">Enable Gradient Mode</label>
            </div>

            {useGradient && (
              <div className="mt-3">
                <label className="text-sm text-gray-400 font-medium">Gradient Type</label>
                <select
                  value={gradType}
                  onChange={(e) => setGradType(e.target.value as GradientType)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 mt-1 text-gray-200"
                >
                  <option value="vertical">Vertical</option>
                  <option value="horizontal">Horizontal</option>
                  <option value="radial">Radial</option>
                </select>
              </div>
            )}

            {useGradient && (
              <div
                className="w-full h-6 mt-3 rounded-md border border-slate-700 shadow-inner transition-all"
                style={gradientStyle}
              ></div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-6 bg-linear-to-r from-cyan-500 to-pink-500 text-white font-semibold py-2 rounded-lg shadow-lg hover:opacity-90 transition"
          >
            {loading ? "Generating..." : "Generate QR"}
          </button>

          {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
        </form>
      </aside>

      {/* RIGHT: Preview */}
      <main className="flex-1 flex flex-col items-center justify-center p-10">
        {qrSrc ? (
          <div className="p-4 rounded-2xl bg-slate-800/50 border border-slate-700 shadow-2xl hover:scale-105 transition-transform">
            <img
              src={qrSrc}
              alt="Generated QR"
              className="w-64 h-64 rounded-lg shadow-[0_0_20px_-5px_rgba(0,255,255,0.3)]"
            />
            <button
              onClick={() => window.open(qrSrc, "_blank")}
              className="mt-3 text-sm text-cyan-400 hover:text-pink-400 transition"
            >
              Open QR Image
            </button>
          </div>
        ) : (
          <div className="w-64 h-64 flex items-center justify-center border-2 border-dashed border-slate-600 rounded-lg text-gray-500">
            Placeholder QR Preview
          </div>
        )}
      </main>
    </div>
  );
}
