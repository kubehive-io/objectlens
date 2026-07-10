<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useObjectLensApi } from "../../composables/useObjectLensApi";
import { Search, HelpCircle, Activity, ShieldCheck, AlertCircle } from "@lucide/vue";

const api = useObjectLensApi();
const route = useRoute();
const router = useRouter();

const backendHealthy = ref(true);
const isSearchOpen = ref(false);

const breadcrumbs = computed(() => {
  const parts = route.path.split("/").filter(Boolean);
  const list = [{ name: "Home", path: "/" }];
  
  let currentPath = "";
  parts.forEach((part, index) => {
    currentPath += `/${part}`;
    
    // Clean up names for display
    let name = decodeURIComponent(part);
    if (name === "providers") name = "Providers";
    if (name === "buckets") name = "Buckets";
    if (name === "details") name = "Details";
    if (name === "upload") name = "Upload Queue";
    
    list.push({
      name,
      path: currentPath
    });
  });
  
  return list;
});

async function checkHealth() {
  try {
    const res = await api.health();
    backendHealthy.value = res.status === "ok";
  } catch {
    backendHealthy.value = false;
  }
}

let healthTimer: ReturnType<typeof setInterval>;

onMounted(() => {
  checkHealth();
  healthTimer = setInterval(checkHealth, 10000); // Check every 10s
  
  // Bind global keyboard shortcut: Ctrl/Cmd + K or /
  window.addEventListener("keydown", handleKeyDown);
});

onUnmounted(() => {
  clearInterval(healthTimer);
  window.removeEventListener("keydown", handleKeyDown);
});

function handleKeyDown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === "k") {
    e.preventDefault();
    triggerSearch();
  }
}

function triggerSearch() {
  router.push("/search");
}
</script>

<template>
  <header class="topnav-container" aria-label="Breadcrumbs and Status">
    <!-- Breadcrumbs -->
    <nav class="breadcrumbs" aria-label="Breadcrumb navigation">
      <span v-for="(crumb, idx) in breadcrumbs" :key="crumb.path" class="breadcrumb-item">
        <NuxtLink :to="crumb.path" class="breadcrumb-link">
          {{ crumb.name }}
        </NuxtLink>
        <span v-if="idx < breadcrumbs.length - 1" class="breadcrumb-separator">/</span>
      </span>
    </nav>

    <!-- Right Side Tools -->
    <div class="topnav-actions">
      <!-- Search Input box trigger -->
      <button class="topnav-search-trigger" type="button" @click="triggerSearch">
        <Search :size="15" class="search-icon" />
        <span class="search-placeholder">Quick search...</span>
        <kbd class="search-kbd">⌘K</kbd>
      </button>

      <!-- Live health check status -->
      <div class="health-status-pills">
        <span class="health-status-badge" :class="backendHealthy ? 'healthy' : 'unhealthy'">
          <ShieldCheck v-if="backendHealthy" :size="14" />
          <AlertCircle v-else :size="14" />
          <span>{{ backendHealthy ? 'API Active' : 'API Offline' }}</span>
        </span>
      </div>

      <!-- Docs / Help link -->
      <a href="https://github.com/google/gemini-cli" target="_blank" class="topnav-icon-btn" title="Documentation">
        <HelpCircle :size="18" />
      </a>
    </div>
  </header>
</template>
