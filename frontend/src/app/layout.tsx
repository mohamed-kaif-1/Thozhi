import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopNav } from "@/components/layout/TopNav";
import { BottomNav } from "@/components/layout/BottomNav";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || "https://thozhi.ai"),
  title: "THOZHI (தோழி) — Multilingual AI-Powered Personal Planning Assistant",
  description: "The AI proposes. The user decides. Sovereign AI personal planning assistant powered by Gnani AI Prisma v3.",
  icons: {
    icon: [
      { url: "/brand/favicon.ico", sizes: "any" },
      { url: "/brand/favicon.png", type: "image/png" },
    ],
    apple: [
      { url: "/brand/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
  manifest: "/manifest.json",
  openGraph: {
    title: "THOZHI (தோழி) — Multilingual AI Personal Planning Assistant",
    description: "The AI proposes. The user decides. Powered by Gnani AI Prisma v3.",
    images: [{ url: "/brand/thozhi-logo.png", width: 333, height: 515, alt: "THOZHI Brand Logo" }],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="antialiased min-h-screen bg-canvas text-slate-800 dark:text-slate-100 flex flex-col md:flex-row selection:bg-sky-500 selection:text-white pb-16 md:pb-0 transition-colors duration-200">
        <ThemeProvider>
          <AuthProvider>
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0">
              <TopNav />
              <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
                <ProtectedRoute>{children}</ProtectedRoute>
              </main>
            </div>
            <BottomNav />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
