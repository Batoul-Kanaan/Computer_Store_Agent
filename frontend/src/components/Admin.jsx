import { useEffect, useState } from "react";
import { api } from "../api.js";
import { categories, money } from "../lib/product.js";

const blank = {
  sku: "",
  name: "",
  brand: "",
  category: "laptop",
  description: "",
  price: "",
  stock_quantity: 0,
  image_url: "",
  specifications: "",
  status: "draft",
};
function toForm(p) {
  return {
    ...p,
    price: (p.price_cents / 100).toFixed(2),
    image_url: p.image_url || "",
    specifications: Object.entries(p.specifications)
      .map(([k, v]) => `${k}: ${v}`)
      .join("\n"),
  };
}
function fromForm(form) {
  const price = Number(form.price);
  if (
    !Number.isFinite(price) ||
    price < 0 ||
    !/^\d+(\.\d{1,2})?$/.test(String(form.price))
  )
    throw new Error(
      "Price must be a non-negative amount with at most two decimal places.",
    );
  const specifications = {};
  for (const row of form.specifications.split("\n").filter((s) => s.trim())) {
    const colon = row.indexOf(":");
    if (colon < 1 || !row.slice(colon + 1).trim())
      throw new Error("Write each specification as Name: Value.");
    specifications[row.slice(0, colon).trim()] = row.slice(colon + 1).trim();
  }
  return {
    sku: form.sku.trim().toUpperCase(),
    name: form.name.trim(),
    brand: form.brand.trim(),
    category: form.category,
    description: form.description.trim(),
    price_cents: Math.round(price * 100),
    stock_quantity: Number(form.stock_quantity),
    image_url: form.image_url.trim() || null,
    specifications,
    status: form.status,
  };
}

export default function Admin() {
  const [identity, setIdentity] = useState(null);
  const [checking, setChecking] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState(blank);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);
  const refresh = () => api.adminProducts().then(setProducts);
  useEffect(() => {
    api
      .me()
      .then(async (me) => {
        setIdentity(me);
        await refresh();
      })
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);
  async function signIn(event) {
    event.preventDefault();
    setError("");
    setSaving(true);
    try {
      const me = await api.login(username, password);
      setIdentity(me);
      setPassword("");
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }
  async function signOut() {
    try {
      await api.logout(identity.csrf_token);
    } finally {
      setIdentity(null);
      setProducts([]);
      setEditing(null);
      setForm(blank);
    }
  }
  async function save(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    setSaving(true);
    try {
      const data = fromForm(form);
      if (editing) {
        const { sku, ...fields } = data;
        await api.update(editing, fields, identity.csrf_token);
      } else await api.create(data, identity.csrf_token);
      await refresh();
      setForm(blank);
      setEditing(null);
      setNotice(editing ? "Product updated." : "Product created.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }
  async function archive(p) {
    if (
      !window.confirm(
        `Archive ${p.name}? It will disappear from the public catalog.`,
      )
    )
      return;
    setError("");
    setNotice("");
    try {
      await api.archive(p.sku, identity.csrf_token);
      await refresh();
      setNotice(`${p.name} archived.`);
    } catch (err) {
      setError(err.message);
    }
  }
  if (checking)
    return (
      <main className="admin-page">
        <p>Checking admin session…</p>
      </main>
    );
  if (!identity)
    return (
      <main className="admin-page">
        <div className="admin-login">
          <span className="eyebrow">STORE OPERATIONS</span>
          <h1>Admin access</h1>
          <p>Sign in to manage products and availability.</p>
          <form onSubmit={signIn}>
            <label>
              Username
              <input
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />
            </label>
            <label>
              Password
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </label>
            {error && <p className="form-error">{error}</p>}
            <button className="primary-button" disabled={saving}>
              Sign in →
            </button>
          </form>
        </div>
      </main>
    );
  return (
    <main className="admin-page">
      <div className="admin-heading">
        <div>
          <span className="eyebrow">
            STORE OPERATIONS / {identity.username.toUpperCase()}
          </span>
          <h1>
            Product studio<span className="dot">.</span>
          </h1>
          <p>
            Publish, update, and archive what customers and the agent can see.
          </p>
        </div>
        <button className="quiet-button" onClick={signOut}>
          Sign out ↗
        </button>
      </div>
      {notice && <p className="success-banner">{notice}</p>}
      {error && <p className="form-error">{error}</p>}
      <div className="admin-layout">
        <section className="admin-list">
          <div className="section-title">
            <h2>Inventory</h2>
            <span>{products.length} PRODUCTS</span>
          </div>
          <button
            className="new-product"
            onClick={() => {
              setForm(blank);
              setEditing(null);
              setError("");
            }}
          >
            + New product
          </button>
          {products.map((p) => (
            <div
              className={`admin-row ${editing === p.sku ? "active" : ""}`}
              key={p.sku}
            >
              <button
                onClick={() => {
                  setForm(toForm(p));
                  setEditing(p.sku);
                  setError("");
                }}
              >
                <strong>{p.name}</strong>
                <small>
                  {p.sku} · {money(p.price_cents)} · {p.stock_quantity} units
                </small>
              </button>
              <span className={`pill ${p.status}`}>{p.status}</span>
              {p.status !== "archived" && (
                <button
                  className="archive"
                  onClick={() => archive(p)}
                  aria-label={`Archive ${p.name}`}
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </section>
        <section className="editor">
          <div className="section-title">
            <h2>{editing ? `Edit ${editing}` : "Add a product"}</h2>
            <span>{editing ? "EDITING" : "NEW"}</span>
          </div>
          <form onSubmit={save}>
            <div className="field-pair">
              <label>
                SKU
                <input
                  required
                  disabled={!!editing}
                  value={form.sku}
                  onChange={(e) =>
                    setForm({ ...form, sku: e.target.value.toUpperCase() })
                  }
                  placeholder="LAP-MODEL-14"
                />
              </label>
              <label>
                Category
                <select
                  value={form.category}
                  onChange={(e) =>
                    setForm({ ...form, category: e.target.value })
                  }
                >
                  {Object.entries(categories).map(([key, label]) => (
                    <option value={key} key={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="field-pair">
              <label>
                Product name
                <input
                  required
                  minLength={2}
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </label>
              <label>
                Brand
                <input
                  required
                  minLength={2}
                  value={form.brand}
                  onChange={(e) => setForm({ ...form, brand: e.target.value })}
                />
              </label>
            </div>
            <label>
              Description
              <textarea
                required
                minLength={10}
                rows={3}
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
              />
            </label>
            <div className="field-pair">
              <label>
                Price (USD)
                <input
                  required
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                />
              </label>
              <label>
                Units in stock
                <input
                  required
                  type="number"
                  min="0"
                  step="1"
                  value={form.stock_quantity}
                  onChange={(e) =>
                    setForm({ ...form, stock_quantity: e.target.value })
                  }
                />
              </label>
            </div>
            <label>
              Image URL (optional)
              <input
                type="url"
                value={form.image_url}
                onChange={(e) =>
                  setForm({ ...form, image_url: e.target.value })
                }
                placeholder="https://…"
              />
            </label>
            <label>
              Specifications <small>one per line, for example RAM: 16 GB</small>
              <textarea
                rows={5}
                value={form.specifications}
                onChange={(e) =>
                  setForm({ ...form, specifications: e.target.value })
                }
                placeholder={"RAM: 16 GB\nStorage: 512 GB SSD"}
              />
            </label>
            <label>
              Visibility
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              >
                <option value="draft">Draft — admin only</option>
                <option value="published">
                  Published — customers and agent
                </option>
                <option value="archived">Archived — admin only</option>
              </select>
            </label>
            <button className="primary-button" disabled={saving}>
              {saving
                ? "Saving…"
                : editing
                  ? "Save changes →"
                  : "Create product →"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
