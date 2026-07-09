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
  <div class="theme-switcher" aria-label="Theme mode">
    <button
      :class="{ active: themeMode === 'light' }"
      type="button"
      @click="setTheme('light')"
    >
      Light
    </button>
    <button
      :class="{ active: themeMode === 'dark' }"
      type="button"
      @click="setTheme('dark')"
    >
      Dark
    </button>
    <button
      :class="{ active: themeMode === 'auto' }"
      type="button"
      @click="setTheme('auto')"
    >
      Auto
    </button>
  </div>
  <NuxtPage />
</template>
