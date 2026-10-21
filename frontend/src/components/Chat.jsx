import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { money } from "../lib/product.js";

export default function Chat({ onOpen }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesContainer = useRef(null);
  useEffect(() => {
    const container = messagesContainer.current;
    if (container) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, busy, open]);
  async function send(event, suggested, retry = false) {
    event?.preventDefault();
    const question = (suggested || draft).trim();
    if (!question || busy) return;
    const previous = retry ? messages.slice(0, -1) : messages;
    const history = previous
      .map((m) => ({ role: m.role, content: m.content }))
      .slice(-8);
    if (!retry)
      setMessages((prev) => [...prev, { role: "user", content: question }]);
    setDraft("");
    setError("");
    setBusy(true);
    setOpen(true);
    try {
      const result = await api.chat(question, history);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.answer,
          products: result.products,
        },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button
        className="chat-launch"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label="Open product assistant"
      >
        <span className="spark">✦</span> Ask our AI{" "}
        <span className="launch-arrow">{open ? "×" : "↗"}</span>
      </button>
      {open && (
        <section className="chat-panel" aria-label="Product assistant">
          <header>
            <div>
              <span className="spark">✦</span>
              <div>
                <strong>Product specialist</strong>
                <small>Ask about the live catalog</small>
              </div>
            </div>
            <button
              className="icon-button"
              onClick={() => setOpen(false)}
              aria-label="Close chat"
            >
              ×
            </button>
          </header>
          <div
            className="chat-messages"
            aria-live="polite"
            ref={messagesContainer}
          >
            {messages.length === 0 && (
              <div className="chat-intro">
                <span className="spark">✦</span>
                <h3>What are you looking for?</h3>
                <p>
                  Find a laptop, compare components, or check what’s in stock.
                </p>
                <div className="suggestions">
                  {[
                    "Laptops under $900",
                    "Compare gaming laptops",
                    "AM5 compatible parts",
                  ].map((prompt) => (
                    <button key={prompt} onClick={() => send(null, prompt)}>
                      {prompt} ↗
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div className={`chat-bubble ${m.role}`} key={i}>
                <span>{m.role === "assistant" ? "SPECIALIST" : "YOU"}</span>
                <p>{m.content}</p>
                {m.products?.length > 0 && (
                  <div className="chat-products">
                    {m.products.map((p) => (
                      <button key={p.sku} onClick={() => onOpen(p)}>
                        {p.name}
                        <strong>{money(p.price_cents)} ↗</strong>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {busy && (
              <div className="chat-bubble assistant">
                <span>SPECIALIST</span>
                <p>Checking the catalog…</p>
              </div>
            )}
            {error && (
              <p className="form-error">
                {error}{" "}
                <button
                  onClick={() => send(null, messages.at(-1)?.content, true)}
                >
                  Retry
                </button>
              </p>
            )}
          </div>
          <form onSubmit={send} className="chat-compose">
            <input
              aria-label="Ask about products"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about a product…"
              maxLength={1000}
            />
            <button disabled={!draft.trim() || busy} aria-label="Send question">
              ↑
            </button>
          </form>
          <footer>
            Answers use current public product data. Verify compatibility before
            buying.
          </footer>
        </section>
      )}
    </>
  );
}
