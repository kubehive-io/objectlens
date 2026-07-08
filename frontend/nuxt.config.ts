export default defineNuxtConfig({
  compatibilityDate: "2026-07-08",
  css: ["~/app/assets/css/main.css"],
  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
    },
  },
  routeRules: {
    "/": { prerender: false },
  },
});
