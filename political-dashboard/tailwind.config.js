/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#1a365d", // Deep Blue
        secondary: "#e53e3e", // Red
        accent: "#38b2ac", // Teal
        background: "#f7fafc", // Light Gray
        surface: "#ffffff", // White
      },
    },
  },
  plugins: [],
}
