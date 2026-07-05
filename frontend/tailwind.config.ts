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
        background: "#0A0A0A",
        surface: "#171717",
        border: "#262626",
        primary: {
          DEFAULT: "#3B82F6",
          foreground: "#FFFFFF",
        },
        amd: {
          DEFAULT: "#ED1C24",
        },
        muted: "#A3A3A3"
      },
    },
  },
  plugins: [],
};
export default config;
