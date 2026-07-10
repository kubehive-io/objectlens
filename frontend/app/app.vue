<script setup lang="ts">
type ThemeMode = "light" | "dark" | "auto";

const themeMode = ref<ThemeMode>("auto");
let darkModeQuery: MediaQueryList | null = null;

function resolvedTheme(mode: ThemeMode) {
  if (mode !== "auto") return mode;
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(mode: ThemeMode) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = resolvedTheme(mode);
  document.documentElement.dataset.themeMode = mode;
  localStorage.setItem("objectlens-theme", mode);
}

function setTheme(mode: ThemeMode) {
  themeMode.value = mode;
  applyTheme(mode);
}

onMounted(() => {
  const stored = localStorage.getItem("objectlens-theme") as ThemeMode | null;
  if (stored === "light" || stored === "dark" || stored === "auto") {
    themeMode.value = stored;
  }
  darkModeQuery = window.matchMedia("(prefers-color-scheme: dark)");
  darkModeQuery.addEventListener("change", () => {
    if (themeMode.value === "auto") applyTheme("auto");
  });
  applyTheme(themeMode.value);
});
</script>

<template>
  <div class="theme-switcher-container" aria-label="Theme mode">
    <button class="theme-switcher-current" type="button">
      <span v-if="themeMode === 'light'">☀️ Light</span>
      <span v-else-if="themeMode === 'dark'">🌙 Dark</span>
      <span v-else-if="themeMode === 'auto'">🌓 Auto</span>
    </button>
    <div class="theme-switcher-dropdown">
      <button
        :class="{ active: themeMode === 'light' }"
        type="button"
        title="Light Mode"
        aria-label="Light Mode"
        @click="setTheme('light')"
      >
        ☀️ Light
      </button>
      <button
        :class="{ active: themeMode === 'dark' }"
        type="button"
        title="Dark Mode"
        aria-label="Dark Mode"
        @click="setTheme('dark')"
      >
        🌙 Dark
      </button>
      <button
        :class="{ active: themeMode === 'auto' }"
        type="button"
        title="System Auto Mode"
        aria-label="System Auto Mode"
        @click="setTheme('auto')"
      >
        🌓 Auto
      </button>
    </div>
  </div>
  <NuxtPage />
</template>
