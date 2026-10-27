/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {
    colors: { brand: { DEFAULT: "#8e2c48", dark: "#6f1f37", light: "#b64d6b" }, blush: "#f6e3e8", cream: "#fbf6f3",
              gold: "#c9973a", ink: "#3a2329", mut: "#7d6268", line: "#ecd9de" },
    fontFamily: { serif: ['"Playfair Display"', "Georgia", "serif"], sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
                  script: ['"Great Vibes"', "cursive"] },
    boxShadow: { soft: "0 10px 30px rgba(142,44,72,.08)", glow: "0 0 0 8px rgba(142,44,72,.08)" },
  } },
  plugins: [],
};
