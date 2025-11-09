import { useState } from "react";

type QRType = "URL" | "WIFI" | "VCARD" | "TEXT";
type GradientType = "vertical" | "horizontal" | "radial";

interface QRPayload {
  title: string;
  type: QRType;
  note: string;
  target_url?: string;
  data?: Record<string, string>;
}

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

  // 🎨 Color + Gradient settings
  const [darkColor, setDarkColor] = useState("#000000");
  const [lightColor, setLightColor] = useState("#ffffff");
  const [useGradient, setUseGradient] = useState(false);
  const [gradType, setGradType] = useState<GradientType>("vertical");

  const [qrSrc, setQrSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = import.meta.env.VITE_API_BASE as string;

  const handleGenerate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload: QRPayload = { title, type, note: "" };

    switch (type) {
      case "URL":
        payload.target_url = url;
        break;
      case "WIFI":
        payload.data = { ssid, password, encryption };
        break;
      case "VCARD":
        payload.data = { name, phone, email };
        break;
      case "TEXT":
        payload.data = { content };
        break;
    }

    try {
      const res = await fetch(`${API_BASE}/api/qr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Request failed (${res.status})`);

      const data: { slug: string } = await res.json();

      const params = new URLSearchParams({
        slug: data.slug,
        dark_color: darkColor,
        light_color: lightColor,
        gradient: useGradient ? "true" : "false",
        grad_type: gradType,
      });

      setQrSrc(`${API_BASE}/qr.png?${params.toString()}`);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("QR generation failed");
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-gray-50 text-gray-800">
      {/* Left Form Pane */}
      <aside className="w-full md:w-1/3 bg-white p-6 shadow-md border-r border-gray-100 overflow-y-auto">
        <h1 className="text-2xl font-bold mb-6 text-blue-700">Kyu-AR Kowd</h1>

        <form onSubmit={handleGenerate} className="space-y-4">
          {/* QR Type Selector */}
          <div>
            <label className="block text-sm font-medium mb-1">QR Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value as QRType)}
              className="w-full border rounded p-2 bg-gray-50"
            >
              <option value="URL">Website / URL</option>
              <option value="WIFI">Wi-Fi Login</option>
              <option value="VCARD">Contact Card</option>
              <option value="TEXT">Plain Text</option>
            </select>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full border rounded p-2"
              placeholder="My QR Code"
              required
            />
          </div>

          {/* Dynamic Fields */}
          {type === "URL" && (
            <div>
              <label className="block text-sm font-medium mb-1">Target URL</label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full border rounded p-2"
                placeholder="https://example.com"
                required
              />
            </div>
          )}

          {type === "WIFI" && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">Wi-Fi Name (SSID)</label>
                <input
                  type="text"
                  value={ssid}
                  onChange={(e) => setSsid(e.target.value)}
                  className="w-full border rounded p-2"
                  placeholder="HomeNetwork"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Password</label>
                <input
                  type="text"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full border rounded p-2"
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Encryption</label>
                <select
                  value={encryption}
                  onChange={(e) => setEncryption(e.target.value)}
                  className="w-full border rounded p-2 bg-gray-50"
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
                <label className="block text-sm font-medium mb-1">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full border rounded p-2"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Phone</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full border rounded p-2"
                  placeholder="+1 555 123 4567"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full border rounded p-2"
                  placeholder="you@example.com"
                />
              </div>
            </>
          )}

          {type === "TEXT" && (
            <div>
              <label className="block text-sm font-medium mb-1">Text Content</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full border rounded p-2"
                rows={3}
                placeholder="Write your message..."
              />
            </div>
          )}

          {/* 🎨 Color Options */}
          <div className="pt-4 border-t border-gray-200">
            <h2 className="font-semibold mb-2">Customize QR Colors</h2>

            <div className="flex items-center gap-3 mb-2">
              <input type="color" value={darkColor} onChange={(e) => setDarkColor(e.target.value)} />
              <label className="text-sm">Dark Color</label>
            </div>

            <div className="flex items-center gap-3 mb-2">
              <input type="color" value={lightColor} onChange={(e) => setLightColor(e.target.value)} />
              <label className="text-sm">Light Color</label>
            </div>

            <div className="flex items-center mt-3">
              <input
                type="checkbox"
                checked={useGradient}
                onChange={() => setUseGradient(!useGradient)}
                className="mr-2"
              />
              <label className="text-sm font-medium">Use Gradient Mode</label>
            </div>

            {useGradient && (
              <div className="mt-3">
                <label className="block text-sm font-medium mb-1">Gradient Type</label>
                <select
                  value={gradType}
                  onChange={(e) => setGradType(e.target.value as GradientType)}
                  className="w-full border rounded p-2 bg-gray-50"
                >
                  <option value="vertical">Vertical </option>
                  <option value="horizontal">Horizontal </option>
                  <option value="radial">Radial</option>
                </select>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 mt-6"
          >
            {loading ? "Generating..." : "Generate QR"}
          </button>

          {error && <p className="text-red-600 text-sm font-medium">{error}</p>}
        </form>
      </aside>

      {/* Right — QR Preview */}
      <main className="flex-1 flex flex-col items-center justify-center p-10">
        {qrSrc ? (
          <img src={qrSrc} alt="Generated QR" className="w-64 h-64 border rounded-lg shadow-lg mb-4" />
        ) : (
          <div className="w-64 h-64 flex items-center justify-center border-2 border-dashed rounded-lg text-gray-400 mb-4">
            Placeholder QR Preview
          </div>
        )}
        {qrSrc && (
          <button
            onClick={() => window.open(qrSrc, "_blank")}
            className="text-blue-600 hover:underline text-sm"
          >
            Open QR Image
          </button>
        )}
      </main>
    </div>
  );
}
