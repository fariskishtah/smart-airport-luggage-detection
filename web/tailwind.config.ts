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
        background: "#080E1E",
        surface: "#0F1A30",
        surfaceBorder: "#1E2F52",
        brandRed: "#E63946",
        brandCyan: "#00E5FF",
        brandEmerald: "#10B981",
        brandAmber: "#F59E0B",
      },
    },
  },
  plugins: [],
};

export default config;
