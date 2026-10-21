import { lazy, Suspense } from "react";
import { Link, Route, Routes } from "react-router";
import Storefront from "./pages/Storefront.jsx";

const AdminPage = lazy(() => import("./pages/AdminPage.jsx"));

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Storefront />} />
      <Route
        path="/admin"
        element={
          <Suspense
            fallback={
              <main className="route-message" role="status">
                Loading store management…
              </main>
            }
          >
            <AdminPage />
          </Suspense>
        }
      />
      <Route
        path="*"
        element={
          <main className="route-message">
            <span className="eyebrow">404 / PAGE NOT FOUND</span>
            <h1>This page isn't here.</h1>
            <Link className="quiet-button" to="/">
              Return to the store →
            </Link>
          </main>
        }
      />
    </Routes>
  );
}
