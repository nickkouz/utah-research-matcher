import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";


export const metadata: Metadata = {
  title: "Utah Research Matcher",
  description: "Company-to-researcher discovery across the University of Utah.",
};


export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="page-shell">
          <header className="topbar">
            <div className="topbar-inner">
              <Link href="/" className="brand-mark">
                <span className="brand-badge">U</span>
                <span>Utah Research Matcher</span>
              </Link>
              <nav className="topnav">
                <Link href="/">Search</Link>
                <Link href="/results">Results</Link>
              </nav>
            </div>
          </header>
          <main className="content-shell">{children}</main>
        </div>
      </body>
    </html>
  );
}

