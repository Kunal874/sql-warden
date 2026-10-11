import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Ask } from "./Ask";
import { AttackLab } from "./AttackLab";
import { Benchmark } from "./Benchmark";
import "./style.css";

const PAGES = { ask: "Ask", attacks: "Attack Lab", benchmark: "Benchmark" } as const;
type Page = keyof typeof PAGES;

function current(): Page {
  const hash = window.location.hash.slice(1);
  return hash in PAGES ? (hash as Page) : "ask";
}

function App() {
  const [page, setPage] = useState<Page>(current);
  useEffect(() => {
    const onHash = () => setPage(current());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  return (
    <>
      <header className="top">
        <div className="brand">
          SQLWarden <span className="muted">read-only text-to-SQL, measured</span>
        </div>
        <nav aria-label="Pages">
          {Object.entries(PAGES).map(([id, label]) => (
            <a key={id} href={`#${id}`} aria-current={page === id ? "page" : undefined}>
              {label}
            </a>
          ))}
        </nav>
      </header>
      <main>
        {page === "ask" && <Ask />}
        {page === "attacks" && <AttackLab />}
        {page === "benchmark" && <Benchmark />}
      </main>
    </>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
