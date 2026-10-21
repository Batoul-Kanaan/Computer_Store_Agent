import { useEffect, useState } from "react";
import { Link } from "react-router";
import { api } from "../api.js";
import { categories } from "../lib/product.js";
import { ProductCard, ProductDetail } from "../components/Product.jsx";
import Chat from "../components/Chat.jsx";

export default function Storefront() {
  const [identity, setIdentity] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [guest, setGuest] = useState(
    () => sessionStorage.getItem("circuit_guest") === "true",
  );
  const [authMode, setAuthMode] = useState("signin");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authSaving, setAuthSaving] = useState(false);
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [inStock, setInStock] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api
      .authMe()
      .then((me) => {
        setIdentity(me);
        sessionStorage.removeItem("circuit_guest");
        setGuest(false);
      })
      .catch(() => {})
      .finally(() => setAuthChecking(false));
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true);
      api
        .products({ query, category, in_stock: inStock })
        .then((data) => {
          if (!controller.signal.aborted) {
            setProducts(data);
            setError("");
          }
        })
        .catch((err) => {
          if (!controller.signal.aborted) setError(err.message);
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 180);
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [query, category, inStock]);

  async function submitAccount(event) {
    event.preventDefault();
    setAuthError("");
    setAuthSaving(true);
    try {
      const authenticate =
        authMode === "signup" ? api.authSignup : api.authLogin;
      const account = await authenticate(username, password);
      setIdentity(account);
      setGuest(false);
      sessionStorage.removeItem("circuit_guest");
      setPassword("");
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthSaving(false);
    }
  }

  function continueAsGuest() {
    sessionStorage.setItem("circuit_guest", "true");
    setGuest(true);
  }

  function returnToAccount() {
    sessionStorage.removeItem("circuit_guest");
    setGuest(false);
    setAuthMode("signin");
  }

  async function signOut() {
    try {
      await api.authLogout(identity.csrf_token);
    } finally {
      setIdentity(null);
      sessionStorage.removeItem("circuit_guest");
      setGuest(false);
    }
  }

  if (authChecking)
    return (
      <main className="access-loading" role="status">
        <span className="brand-symbol">◈</span> CIRCUIT&CO.
      </main>
    );

  if (!identity && !guest)
    return (
      <main className="access-shell">
        <div className="access-brand-row">
          <span className="access-brand">
            <span className="brand-symbol">◈</span> CIRCUIT<span>&</span>CO
            <span className="brand-period">.</span>
          </span>
          <span className="access-index">
            INDEPENDENT HARDWARE, WELL CHOSEN
          </span>
        </div>
        <div className="access-layout">
          <section className="access-intro">
            <span className="eyebrow">
              <span className="status-dot" /> YOUR NEXT SETUP STARTS HERE
            </span>
            <h1>
              Find the gear
              <br />
              that <em>fits you.</em>
            </h1>
            <p>
              Sign in, create an account, or browse the collection as a guest.
            </p>
            <div className="access-footnote">
              <span>01 / CONSIDERED TECH</span>
              <span>02 / HUMAN CHOICE</span>
            </div>
          </section>
          <section className="access-form-panel" aria-labelledby="access-title">
            <span className="eyebrow">WELCOME TO CIRCUIT&CO.</span>
            <h2 id="access-title">
              {authMode === "signup"
                ? "Create your account."
                : "Good to have you."}
            </h2>
            <div
              className="access-tabs"
              role="tablist"
              aria-label="Account access"
            >
              <button
                type="button"
                role="tab"
                aria-selected={authMode === "signin"}
                className={authMode === "signin" ? "active" : ""}
                onClick={() => {
                  setAuthMode("signin");
                  setAuthError("");
                }}
              >
                Sign in
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={authMode === "signup"}
                className={authMode === "signup" ? "active" : ""}
                onClick={() => {
                  setAuthMode("signup");
                  setAuthError("");
                }}
              >
                Sign up
              </button>
            </div>
            <form className="access-form" onSubmit={submitAccount}>
              <label>
                Username
                <input
                  required
                  minLength={3}
                  maxLength={80}
                  pattern="[A-Za-z0-9_.-]+"
                  autoComplete="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="Your username"
                />
              </label>
              <label>
                Password
                <input
                  required
                  minLength={authMode === "signup" ? 8 : 1}
                  maxLength={256}
                  type="password"
                  autoComplete={
                    authMode === "signup" ? "new-password" : "current-password"
                  }
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder={
                    authMode === "signup"
                      ? "At least 8 characters"
                      : "Your password"
                  }
                />
              </label>
              {authError && (
                <p className="form-error" role="alert">
                  {authError}
                </p>
              )}
              <button
                className="primary-button access-submit"
                disabled={authSaving}
              >
                {authSaving
                  ? "Please wait…"
                  : authMode === "signup"
                    ? "Create account →"
                    : "Sign in →"}
              </button>
            </form>
            <div className="guest-choice">
              <span>OR BROWSE WITHOUT AN ACCOUNT</span>
              <button type="button" onClick={continueAsGuest}>
                Continue as a guest <span aria-hidden="true">↗</span>
              </button>
            </div>
          </section>
        </div>
      </main>
    );

  return (
    <div className="site-shell">
      <header className="site-header">
        <button
          className="brand"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        >
          <span className="brand-symbol">◈</span> CIRCUIT<span>&</span>CO
          <span className="brand-period">.</span>
        </button>
        <nav aria-label="Main navigation">
          <button
            className="current"
            onClick={() =>
              document
                .getElementById("catalog")
                .scrollIntoView({ behavior: "smooth" })
            }
          >
            Shop
          </button>
          {identity?.role === "admin" && (
            <Link className="nav-admin" to="/admin">
              Admin
            </Link>
          )}
        </nav>
        {identity ? (
          <div className="header-account">
            <span>{identity.username}</span>
            <button onClick={signOut}>Sign out</button>
          </div>
        ) : guest ? (
          <div className="header-account">
            <span>Browsing as guest</span>
            <button onClick={returnToAccount}>Sign in</button>
          </div>
        ) : (
          <div className="header-note">
            HUMAN CHOICE. SMARTER TOOLS. <span>✦</span>
          </div>
        )}
      </header>
      <>
        <main>
          <section className="hero">
            <div className="hero-copy">
              <span className="eyebrow">
                <span className="status-dot" /> THE HARDWARE EDIT
              </span>
              <h1>
                Find your
                <br />
                <em>next move.</em>
              </h1>
              <p>
                Good tech starts with the right questions. Browse considered
                gear, compare the details, and find a setup that fits.
              </p>
              <button
                className="hero-cta"
                onClick={() =>
                  document
                    .getElementById("catalog")
                    .scrollIntoView({ behavior: "smooth" })
                }
              >
                Explore the collection <span>↗</span>
              </button>
              <div className="hero-foot">
                01 — LAPTOPS <span>02 — COMPONENTS</span> 03 — DEVICES
              </div>
            </div>
            <div className="hero-visual" aria-hidden="true">
              <div className="orb orb-one" />
              <div className="orb orb-two" />
              <div className="hero-device">
                <div className="hero-screen">
                  <span>◈</span>
                  <strong>
                    BETTER
                    <br />
                    BY DESIGN.
                  </strong>
                  <small>
                    THE RIGHT TOOL
                    <br />
                    CHANGES EVERYTHING.
                  </small>
                </div>
                <div className="hero-base" />
              </div>
              <span className="visual-label">CURATED FOR YOUR NEXT BUILD</span>
            </div>
          </section>
          <section className="catalog" id="catalog">
            <div className="catalog-heading">
              <div>
                <span className="eyebrow">01 / THE COLLECTION</span>
                <h2>
                  Explore the good stuff<span className="dot">.</span>
                </h2>
              </div>
              <p>
                Every detail matters.
                <br />
                Find yours here.
              </p>
            </div>
            <div className="filters">
              <div
                className="category-tabs"
                role="group"
                aria-label="Product category"
              >
                <button
                  className={!category ? "active" : ""}
                  onClick={() => setCategory("")}
                >
                  All products
                </button>
                {Object.entries(categories).map(([key, label]) => (
                  <button
                    key={key}
                    className={category === key ? "active" : ""}
                    onClick={() => setCategory(key)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <div className="filter-actions">
                <label className="search-field">
                  <span>⌕</span>
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search gear..."
                    aria-label="Search products"
                  />
                </label>
                <label className="stock-filter">
                  <input
                    type="checkbox"
                    checked={inStock}
                    onChange={(e) => setInStock(e.target.checked)}
                  />{" "}
                  In stock
                </label>
              </div>
            </div>
            <div className="results-meta">
              <span>{loading ? "LOADING" : `${products.length} PRODUCTS`}</span>
              <span>DISCOVER YOUR FIT ↘</span>
            </div>
            {error ? (
              <div className="empty-state">Catalog unavailable: {error}</div>
            ) : loading ? (
              <div className="empty-state">Loading the collection…</div>
            ) : products.length ? (
              <div className="product-grid">
                {products.map((p) => (
                  <ProductCard key={p.sku} product={p} onOpen={setSelected} />
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <h3>No products found.</h3>
                <p>Try another search or category.</p>
              </div>
            )}
          </section>
          <section className="help-banner">
            <div>
              <span className="eyebrow">NEED A SECOND OPINION?</span>
              <h2>
                Questions welcome.
                <br />
                <em>Good answers follow.</em>
              </h2>
            </div>
            <p>
              Our AI specialist checks the current product catalog to help you
              compare and choose. Tap “Ask our AI” to get started.
            </p>
            <span className="banner-mark">✦</span>
          </section>
        </main>
        <footer className="site-footer">
          <strong>◈ CIRCUIT&CO.</strong>
          <span>Computer store demo · Prices shown in USD · No checkout</span>
          <span>BUILT FOR BETTER DECISIONS ↗</span>
        </footer>
        <Chat onOpen={setSelected} />
      </>
      {selected && (
        <ProductDetail product={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
