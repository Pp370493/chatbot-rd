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
        gov: {
          navy: "#0F2C59",      // Deep Navy Blue (Thai Gov Official Theme)
          blue: "#1E4E8C",      // Accent Medium Blue
          light: "#F0F4F8",     // Soft Grayish Blue for background surfaces
          gold: "#D4A373",      // Premium Gold Accent for warning borders or badges
          accent: "#38bdf8",    // Active light blue
          glass: "rgba(255, 255, 255, 0.8)",
        }
      },
      fontFamily: {
        sans: ["var(--font-sara)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        premium: "0 8px 30px rgb(0, 0, 0, 0.08)",
        glow: "0 0 15px rgba(30, 78, 140, 0.15)",
      }
    },
  },
  plugins: [],
};
export default config;
