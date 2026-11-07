import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopNav } from "@/components/layout/TopNav";

export const metadata: Metadata = {
  title: "THOZHI (தோழி) — Multilingual AI-Powered Personal Planning Assistant",
  description: "The AI proposes. The user decides. Sovereign AI personal planning assistant powered by Gnani AI Prisma v3.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen bg-canvas text-slate-100 flex selection:bg-sky-500 selection:text-white">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <TopNav />
          <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
