import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          grey: "var(--color-brand-grey)",
          olive: "var(--color-brand-olive)",
          deepOlive: "var(--color-brand-deep-olive)",
          maroon: "var(--color-brand-maroon)",
        },
        navy: "var(--color-navy)",
        blue: {
          DEFAULT: "var(--color-blue)",
          muted: "var(--color-blue)",
        },
        mint: {
          DEFAULT: "var(--color-mint)",
          soft: "var(--color-mint-soft)",
        },
        surface: {
          DEFAULT: "var(--color-surface)",
          secondary: "var(--color-surface-secondary)",
          subtle: "var(--color-surface-subtle)",
        },
        text: {
          primary: "var(--color-text-primary)",
          secondary: "var(--color-text-secondary)",
          muted: "var(--color-text-muted)",
        },
        border: {
          tactical: "var(--color-border)",
          dark: "var(--color-navy)",
        },
        status: {
          success: "var(--color-status-success)",
          warning: "var(--color-status-warning)",
          error: "var(--color-status-error)",
          info: "var(--color-status-info)",
        },
      },
      fontFamily: {
        heading: ["var(--font-space-grotesk)", "sans-serif"],
        sans: ["var(--font-inter)", "sans-serif"],
      },
      boxShadow: {
        tactical: "3px 3px 0px #203653",
        "tactical-sm": "2px 2px 0px #203653",
        "tactical-lg": "4px 4px 0px #203653",
        "tactical-inset": "inset 2px 2px 0px rgba(32, 54, 83, 0.2)",
      },
      borderRadius: {
        tactical: "10px",
        "tactical-sm": "6px",
        "tactical-lg": "14px",
      },
      borderWidth: {
        tactical: "1.5px",
        "tactical-thick": "2px",
      },
    },
  },
  plugins: [],
};

export default config;

