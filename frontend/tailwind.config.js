/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172026",
        graphite: "#2f3a40",
        mist: "#edf2f4",
        pulse: "#0e7c7b",
        ember: "#c75000",
        plum: "#6d3b73"
      },
      boxShadow: {
        panel: "0 1px 2px rgba(15, 23, 42, 0.08)"
      }
    }
  },
  plugins: []
};

