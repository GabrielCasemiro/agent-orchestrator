import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Orchestrator",
  description: "Multi-agent coordination dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="noise-bg">{children}</body>
    </html>
  );
}
