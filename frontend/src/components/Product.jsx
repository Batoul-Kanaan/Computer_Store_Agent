import { useEffect } from "react";
import { categories, money } from "../lib/product.js";

function Icon({ category }) {
  return (
    <div className={`product-art ${category}`} aria-hidden="true">
      {category === "laptop" ? (
        <svg viewBox="0 0 160 130">
          <rect x="23" y="18" width="114" height="78" rx="6" />
          <path d="M12 105h136l-10 9H22z" />
          <path d="M31 27h98v60H31z" className="screen" />
          <path d="M58 56h44" className="line" />
        </svg>
      ) : category === "component" ? (
        <svg viewBox="0 0 160 130">
          <rect x="40" y="24" width="80" height="80" rx="9" />
          <rect
            x="54"
            y="38"
            width="52"
            height="52"
            rx="5"
            className="screen"
          />
          <path
            d="M28 43h12m-12 17h12m-12 17h12m-12 17h12m80-51h12m-12 17h12m-12 17h12m-12 17h12M57 12v12m23-12v12m23-12v12M57 104v12m23-12v12m23-12v12"
            className="line"
          />
        </svg>
      ) : (
        <svg viewBox="0 0 160 130">
          <rect x="29" y="19" width="102" height="74" rx="7" />
          <path d="M80 93v17m-29 3h58" className="line" />
          <path d="M37 27h86v58H37z" className="screen" />
          <path d="M57 55h46" className="line" />
        </svg>
      )}
    </div>
  );
}

export function ProductCard({ product, onOpen }) {
  return (
    <button
      className="product-card"
      onClick={() => onOpen(product)}
      aria-label={`View ${product.name}`}
    >
      <div className="card-media">
        {product.image_url ? (
          <img src={product.image_url} alt="" loading="lazy" />
        ) : (
          <Icon category={product.category} />
        )}
        <span className="media-index">{product.category.toUpperCase()}</span>
      </div>
      <div className="card-copy">
        <div className="card-eyebrow">
          {product.brand} <span>·</span> {product.sku}
        </div>
        <h3>{product.name}</h3>
        <p>{product.description}</p>
        <div className="card-bottom">
          <strong>{money(product.price_cents)}</strong>
          <span className={product.stock_quantity ? "stock" : "stock out"}>
            {product.stock_quantity
              ? `${product.stock_quantity} in stock`
              : "Out of stock"}
          </span>
        </div>
      </div>
    </button>
  );
}

export function ProductDetail({ product, onClose }) {
  useEffect(() => {
    const onKey = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div
      className="overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className="detail-panel"
        role="dialog"
        aria-modal="true"
        aria-label={product.name}
      >
        <button
          className="icon-button close"
          onClick={onClose}
          aria-label="Close"
        >
          ×
        </button>
        <div className="detail-visual">
          {product.image_url ? (
            <img src={product.image_url} alt="" />
          ) : (
            <Icon category={product.category} />
          )}
        </div>
        <div className="detail-copy">
          <span className="eyebrow">
            {categories[product.category]} / {product.brand}
          </span>
          <h2>{product.name}</h2>
          <span className="muted">SKU {product.sku}</span>
          <p>{product.description}</p>
          <div className="detail-purchase">
            <strong>{money(product.price_cents)}</strong>
            <span className={product.stock_quantity ? "stock" : "stock out"}>
              {product.stock_quantity
                ? `${product.stock_quantity} available`
                : "Currently unavailable"}
            </span>
          </div>
          <h3>Specifications</h3>
          <dl className="spec-list">
            {Object.entries(product.specifications).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>
    </div>
  );
}
