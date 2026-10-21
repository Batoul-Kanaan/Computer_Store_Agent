import { useEffect } from "react";
import { Link } from "react-router";
import Admin from "../components/Admin.jsx";

export default function AdminPage() {
  useEffect(() => {
    const previousTitle = document.title;
    document.title = "Store management — Circuit & Co.";
    return () => {
      document.title = previousTitle;
    };
  }, []);

  return (
    <div className="admin-shell">
      <header className="site-header admin-header">
        <Link className="brand" to="/">
          <span className="brand-symbol">◈</span> CIRCUIT<span>&</span>CO
          <span className="brand-period">.</span>
        </Link>
        <span className="admin-site-label">Store management</span>
        <Link className="quiet-button" to="/">
          View storefront ↗
        </Link>
      </header>
      <Admin />
    </div>
  );
}
