/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: "#07090d",
          900: "#0b0e14",
          850: "#10141d",
          800: "#141926",
          700: "#1c2334",
        },
        ember: {
          400: "#ffb15c",
          500: "#f5943a",
          600: "#e0742a",
        },
        crimson: {
          400: "#ff6b6b",
          500: "#ef4444",
          600: "#dc2626",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "system-ui", "sans-serif"],
        body: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 40px -10px rgba(245, 148, 58, 0.35)",
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 24px -8px rgba(0,0,0,0.6)",
      },
      backgroundImage: {
        "radial-fade": "radial-gradient(circle at 20% -10%, rgba(245,148,58,0.12), transparent 60%)",
      },
    },
  },
  plugins: [],
};
