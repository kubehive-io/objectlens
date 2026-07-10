<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useObjectLensApi, type ProviderConnection } from "../../composables/useObjectLensApi";
import {
  LayoutDashboard,
  Server,
  FolderOpen,
  Search,
  Upload,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  User,
  ExternalLink,
  Laptop,
  Moon,
  Sun
} from "@lucide/vue";

const api = useObjectLensApi();
const router = useRouter();
const route = useRoute();

const isCollapsed = ref(false);
const providers = ref<ProviderConnection[]>([]);
const currentProviderId = ref<string>("");

onMounted(async () => {
  try {
    providers.value = await api.listProviders();
    // Pre-select provider if route has it
    if (route.params.providerId) {
      currentProviderId.value = route.params.providerId as string;
    } else {
      const first = providers.value[0];
      if (first) {
        currentProviderId.value = first.id;
      }
    }
  } catch (err) {
    console.error("Failed to load providers for sidebar:", err);
  }
});

// Watch route for active provider changes
watch(
  () => route.params.providerId,
  (newId) => {
    if (newId) {
      currentProviderId.value = newId as string;
    }
  }
);

function selectProvider(providerId: string) {
  if (!providerId) return;
  router.push(`/providers/${encodeURIComponent(providerId)}`);
}

function toggleSidebar() {
  isCollapsed.value = !isCollapsed.value;
}

const themeMode = ref<"light" | "dark" | "auto">("auto");
let darkModeQuery: MediaQueryList | null = null;

function resolvedTheme(mode: typeof themeMode.value) {
  if (mode !== "auto") return mode;
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(mode: typeof themeMode.value) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = resolvedTheme(mode);
  document.documentElement.dataset.themeMode = mode;
  localStorage.setItem("objectlens-theme", mode);
}

function setTheme(mode: typeof themeMode.value) {
  themeMode.value = mode;
  applyTheme(mode);
}

onMounted(() => {
  const stored = localStorage.getItem("objectlens-theme") as typeof themeMode.value | null;
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
  <aside class="sidebar-container" :class="{ collapsed: isCollapsed }" aria-label="Main Navigation">
    <div class="sidebar-header">
      <NuxtLink to="/" class="brand-link" title="ObjectLens Dashboard">
        <span class="brand-icon">⚓</span>
        <span v-if="!isCollapsed" class="brand-name">ObjectLens</span>
      </NuxtLink>
      <button class="toggle-button" type="button" :title="isCollapsed ? 'Expand' : 'Collapse'" @click="toggleSidebar">
        <ChevronLeft v-if="!isCollapsed" :size="16" />
        <ChevronRight v-else :size="16" />
      </button>
    </div>

    <nav class="sidebar-nav" aria-label="Global links">
      <NuxtLink to="/" class="nav-item" :class="{ active: route.path === '/' }" data-tooltip="Overview">
        <LayoutDashboard :size="18" />
        <span v-if="!isCollapsed">Overview</span>
      </NuxtLink>

      <NuxtLink to="/providers" class="nav-item" :class="{ active: route.path.startsWith('/providers') }" data-tooltip="Providers">
        <Server :size="18" />
        <span v-if="!isCollapsed">Providers</span>
      </NuxtLink>

      <NuxtLink to="/buckets" class="nav-item" :class="{ active: route.path.startsWith('/buckets') }" data-tooltip="Buckets">
        <FolderOpen :size="18" />
        <span v-if="!isCollapsed">Buckets</span>
      </NuxtLink>

      <NuxtLink to="/search" class="nav-item" :class="{ active: route.path === '/search' }" data-tooltip="Search">
        <Search :size="18" />
        <span v-if="!isCollapsed">Search</span>
      </NuxtLink>

      <NuxtLink
        v-if="currentProviderId && route.params.bucket"
        :to="`/providers/${encodeURIComponent(currentProviderId)}/buckets/${encodeURIComponent(route.params.bucket as string)}/upload`"
        class="nav-item"
        :class="{ active: route.path.endsWith('/upload') }"
        data-tooltip="Uploads"
      >
        <Upload :size="18" />
        <span v-if="!isCollapsed">Uploads</span>
      </NuxtLink>

      <NuxtLink to="/activity" class="nav-item" :class="{ active: route.path === '/activity' }" data-tooltip="Activity">
        <Activity :size="18" />
        <span v-if="!isCollapsed">Activity</span>
      </NuxtLink>

      <NuxtLink to="/settings" class="nav-item" :class="{ active: route.path === '/settings' }" data-tooltip="Settings">
        <Settings :size="18" />
        <span v-if="!isCollapsed">Settings</span>
      </NuxtLink>
    </nav>

    <div class="sidebar-footer">
      <!-- Quick provider switch dropdown -->
      <div v-if="!isCollapsed && providers.length > 0" class="provider-quick-switcher">
        <label for="provider-select" class="visually-hidden">Quick Switch Provider</label>
        <select
          id="provider-select"
          v-model="currentProviderId"
          class="provider-select"
          @change="selectProvider(currentProviderId)"
        >
          <option v-for="p in providers" :key="p.id" :value="p.id">
            {{ p.name }}
          </option>
        </select>
      </div>

      <!-- Theme Select Hover Dropdown -->
      <div class="theme-menu-container">
        <button class="theme-menu-current" type="button" data-tooltip="Theme Mode">
          <span v-if="themeMode === 'light'"><Sun :size="16" /><span v-if="!isCollapsed"> Light</span></span>
          <span v-else-if="themeMode === 'dark'"><Moon :size="16" /><span v-if="!isCollapsed"> Dark</span></span>
          <span v-else-if="themeMode === 'auto'"><Laptop :size="16" /><span v-if="!isCollapsed"> Auto</span></span>
        </button>
        <div class="theme-menu-dropdown">
          <button :class="{ active: themeMode === 'light' }" type="button" @click="setTheme('light')">
            <Sun :size="14" /> Light
          </button>
          <button :class="{ active: themeMode === 'dark' }" type="button" @click="setTheme('dark')">
            <Moon :size="14" /> Dark
          </button>
          <button :class="{ active: themeMode === 'auto' }" type="button" @click="setTheme('auto')">
            <Laptop :size="14" /> Auto
          </button>
        </div>
      </div>

      <!-- User Info & Version -->
      <div class="user-block" data-tooltip="v0.1.0">
        <User :size="18" class="user-avatar" />
        <div v-if="!isCollapsed" class="user-info">
          <span class="username">Developer</span>
          <span class="version">v0.1.0</span>
        </div>
      </div>
    </div>
  </aside>
</template>
