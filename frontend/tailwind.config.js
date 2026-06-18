/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Palette Adobe Color (cf. demande utilisateur)
        primary: {
          DEFAULT: "#0439D9",
          dark: "#011140",
          light: "#5086F2",
        },
        accent: "#5086F2",
        muted: "#758EBF",
        surface: "#F2F2F2",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(1, 17, 64, 0.08), 0 1px 2px -1px rgba(1, 17, 64, 0.08)",
      },
    },
  },
  plugins: [],
};
