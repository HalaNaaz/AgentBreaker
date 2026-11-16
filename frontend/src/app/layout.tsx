import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "AgentBreaker — AI Security Research & Red Teaming Platform",
  description:
    "Modular adversarial security evaluation framework for LLMs and autonomous AI agents by AshlynxCyber.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans bg-brand-grey text-navy min-h-screen">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
