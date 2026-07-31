/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Material Design 3 color system (from HTML references)
        primary: "#6bd8cb",
        "primary-container": "#29a195",
        "primary-fixed": "#89f5e7",
        "primary-fixed-dim": "#6bd8cb",
        "on-primary": "#003732",
        "on-primary-container": "#00302b",
        "on-primary-fixed": "#00201d",
        "on-primary-fixed-variant": "#005049",

        secondary: "#b9c7e0",
        "secondary-container": "#3c4a5e",
        "secondary-fixed": "#d5e3fd",
        "secondary-fixed-dim": "#b9c7e0",
        "on-secondary": "#233144",
        "on-secondary-container": "#abb9d2",
        "on-secondary-fixed": "#0d1c2f",
        "on-secondary-fixed-variant": "#3a485c",

        tertiary: "#bec6e0",
        "tertiary-container": "#8990a8",
        "tertiary-fixed": "#dae2fd",
        "tertiary-fixed-dim": "#bec6e0",
        "on-tertiary": "#283044",
        "on-tertiary-container": "#22293d",
        "on-tertiary-fixed": "#131b2e",
        "on-tertiary-fixed-variant": "#3f465c",

        error: "#ffb4ab",
        "error-container": "#93000a",
        "on-error": "#690005",
        "on-error-container": "#ffdad6",

        background: "#051424",
        "on-background": "#d4e4fa",

        surface: "#051424",
        "surface-dim": "#051424",
        "surface-bright": "#2c3a4c",
        "surface-container-lowest": "#010f1f",
        "surface-container-low": "#0d1c2d",
        "surface-container": "#122131",
        "surface-container-high": "#1c2b3c",
        "surface-container-highest": "#273647",
        "on-surface": "#d4e4fa",
        "on-surface-variant": "#bcc9c6",

        "surface-variant": "#273647",
        outline: "#879391",
        "outline-variant": "#3d4947",

        "inverse-surface": "#d4e4fa",
        "inverse-on-surface": "#233143",
        "inverse-primary": "#006a61",

        "surface-tint": "#6bd8cb",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["monospace"],
      },
      fontSize: {
        "display-lg": ["32px", { lineHeight: "40px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "headline-md": ["24px", { lineHeight: "32px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "headline-sm": ["20px", { lineHeight: "28px", fontWeight: "600" }],
        "title-lg": ["22px", { lineHeight: "28px", fontWeight: "500" }],
        "title-md": ["16px", { lineHeight: "24px", fontWeight: "500" }],
        "title-sm": ["14px", { lineHeight: "20px", fontWeight: "500" }],
        "body-lg": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "body-md": ["14px", { lineHeight: "20px", fontWeight: "400" }],
        "body-sm": ["13px", { lineHeight: "18px", fontWeight: "400" }],
        "label-lg": ["14px", { lineHeight: "20px", fontWeight: "500" }],
        "label-md": ["12px", { lineHeight: "16px", fontWeight: "500" }],
        "label-sm": ["11px", { lineHeight: "16px", fontWeight: "500" }],
        "label-bold": ["12px", { lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "600" }],
        "code-sm": ["12px", { lineHeight: "16px", fontWeight: "400" }],
      },
      spacing: {
        "container-padding": "24px",
        "element-gap": "8px",
        "table-cell-padding": "12px 16px",
        "gutter": "16px",
        "unit": "4px",
      },
      borderRadius: {
        DEFAULT: "0.125rem",
        lg: "0.25rem",
        xl: "0.5rem",
        full: "0.75rem",
      },
    },
  },
  plugins: [],
}