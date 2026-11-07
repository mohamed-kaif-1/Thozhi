import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        canvas: {
          DEFAULT: "#080B11", // Deep Obsidian Black
          subtle: "#0B0F19",
          card: "#0F172A",   // Slate-Black Surface Card
          elevated: "#131D33",
        },
        cyber: {
          blue: {
            50: "#F0F9FF",
            100: "#E0F2FE",
            200: "#BAE6FD",
            300: "#7DD3FC",
            400: "#38BDF8", // Electric Sky Blue
            500: "#0EA5E9",
            600: "#0284C7",
            glow: "rgba(56, 189, 248, 0.2)",
          },
          amber: {
            400: "#FBBF24", // Radiant Gold
            500: "#F59E0B", // Primary Proposal / Attention Amber
            600: "#D97706",
            glow: "rgba(245, 158, 11, 0.2)",
          },
          emerald: {
            400: "#34D399",
            500: "#10B981", // Approved / Completed Task
            600: "#059669",
          },
          coral: {
            400: "#F87171",
            500: "#EF4444", // Capacity Deficit Alert
          }
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        tamil: ["var(--font-noto-tamil)", "sans-serif"],
      }
    },
  },
  plugins: [],
};
export default config;
