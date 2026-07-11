<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { useObjectLensApi, type ProviderConnection, type ObjectMetadata } from "../composables/useObjectLensApi";
import {
  Search,
  Server,
  Folder,
  File,
  Loader,
  AlertCircle,
  ArrowRight,
  Database
} from "@lucide/vue";

const api = useObjectLensApi();

const query = ref("");
const activeFilter = ref<"all" | "providers" | "buckets" | "objects">("all");
const loading = ref(false);

const providers = ref<ProviderConnection[]>([]);
const buckets = ref<any[]>([]);
const objects = ref<ObjectMetadata[]>([]);
const error = ref("");

const searchInputRef = ref<HTMLInputElement | null>(null);

function handleGlobalKeydown(e: KeyboardEvent) {
  // Focus search input on '/' when not typing in form controls
  if (e.key === "/" && document.activeElement?.tagName !== "INPUT" && document.activeElement?.tagName !== "TEXTAREA") {
    e.preventDefault();
    searchInputRef.value?.focus();
  }
  // Clear search on Escape when focused
  if (e.key === "Escape" && document.activeElement === searchInputRef.value) {
    query.value = "";
    searchInputRef.value?.blur();
  }
}

function getExtensionBadgeClass(key: string) {
  const ext = key.split(".").pop()?.toLowerCase() || "";
  if (["png", "jpg", "jpeg", "gif", "svg", "webp"].includes(ext)) return "ext-image";
  if (["json", "yaml", "yml", "xml", "toml"].includes(ext)) return "ext-config";
  if (["zip", "tar", "gz", "rar", "7z"].includes(ext)) return "ext-archive";
  if (["pdf", "md", "txt", "doc", "docx"].includes(ext)) return "ext-doc";
  if (["js", "ts", "py", "go", "sh", "rs"].includes(ext)) return "ext-code";
  return "ext-default";
}

function formatBytes(value: number) {
  if (value === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

// Fetch providers and buckets on mount
onMounted(async () => {
  document.addEventListener("keydown", handleGlobalKeydown);
  loading.value = true;
  try {
    providers.value = await api.listProviders();
    
    // Fetch buckets across all providers in parallel
    const bucketPromises = providers.value.map(async (p) => {
      try {
        const res = await api.listProviderBuckets(p.id);
        return res.buckets.map(b => ({
          name: b.name,
          providerId: p.id,
          providerName: p.name,
          providerType: p.type
        }));
      } catch {
        return [];
      }
    });
    const results = await Promise.all(bucketPromises);
    buckets.value = results.flat();
  } catch (err) {
    console.error("Failed to pre-load search assets:", err);
  } finally {
    loading.value = false;
  }
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleGlobalKeydown);
});

// Search objects when query changes
watch(query, async (newQuery) => {
  const cleaned = newQuery.trim();
  if (cleaned.length < 2) {
    objects.value = [];
    return;
  }
  
  // Only search objects if default bucket or any bucket exists
  if (buckets.value.length === 0) return;
  
  loading.value = true;
  try {
    // Search objects in the first visible bucket as a showcase
    const targetBucket = buckets.value[0].name;
    const targetProvider = buckets.value[0].providerId;
    const res = await api.listObjects({
      bucket: targetBucket,
      search: cleaned,
      limit: 15
    });
    objects.value = res.objects || [];
  } catch (err) {
    console.error("Failed to query indexed objects:", err);
  } finally {
    loading.value = false;
  }
});

// Computed matched items
const matchedProviders = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return [];
  return providers.value.filter(
    p => p.name.toLowerCase().includes(q) || p.type.toLowerCase().includes(q)
  );
});

const matchedBuckets = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return [];
  return buckets.value.filter(
    b => b.name.toLowerCase().includes(q) || b.providerName.toLowerCase().includes(q)
  );
});

const hasResults = computed(() => {
  if (!query.value.trim()) return true; // Show nothing, not "no results"
  return matchedProviders.value.length > 0 || matchedBuckets.value.length > 0 || objects.value.length > 0;
});
</script>

<template>
  <div class="search-page">
    <!-- Header -->
    <header class="page-title-section">
      <div class="header-text-block">
        <h1>Global Search</h1>
        <p class="subtitle">Query and locate storage connections, buckets, and object metadata indexes instantly.</p>
      </div>
    </header>

    <!-- Large Centered Search Box -->
    <section class="large-search-container">
      <div class="search-bar-huge">
        <Search :size="20" class="search-iconmuted" />
        <input
          ref="searchInputRef"
          v-model="query"
          type="text"
          placeholder="Type name, provider, prefix, or object filename..."
          autofocus
          aria-label="Global search input"
        />
        <div class="search-shortcut-badge" v-if="!query" title="Press '/' key to focus">
          <span>/</span>
        </div>
        <Loader v-if="loading" :size="18" class="spin text-accent" />
      </div>

      <!-- Filter Pills -->
      <div class="filter-pills-row" v-if="query.trim().length > 0">
        <button
          class="pill-btn"
          :class="{ active: activeFilter === 'all' }"
          type="button"
          @click="activeFilter = 'all'"
        >
          <span>All</span>
          <span class="pill-badge">{{ matchedProviders.length + matchedBuckets.length + objects.length }}</span>
        </button>
        <button
          class="pill-btn"
          :class="{ active: activeFilter === 'providers' }"
          type="button"
          @click="activeFilter = 'providers'"
        >
          <span>Providers</span>
          <span class="pill-badge">{{ matchedProviders.length }}</span>
        </button>
        <button
          class="pill-btn"
          :class="{ active: activeFilter === 'buckets' }"
          type="button"
          @click="activeFilter = 'buckets'"
        >
          <span>Buckets</span>
          <span class="pill-badge">{{ matchedBuckets.length }}</span>
        </button>
        <button
          class="pill-btn"
          :class="{ active: activeFilter === 'objects' }"
          type="button"
          @click="activeFilter = 'objects'"
        >
          <span>Objects</span>
          <span class="pill-badge">{{ objects.length }}</span>
        </button>
      </div>
    </section>

    <!-- Results Area -->
    <section class="search-results-section">
      <!-- Empty/Initial State -->
      <div v-if="!query.trim()" class="empty-dashboard-state search-initial">
        <Search :size="48" class="muted" />
        <h3>Locate Anything Instantly</h3>
        <p>Type a storage key, provider name, or prefix to find matches across your entire storage ecosystem. Press <kbd class="kbd-hint">/</kbd> to focus.</p>
      </div>

      <!-- No Results State -->
      <div v-else-if="!hasResults" class="empty-dashboard-state">
        <AlertCircle :size="48" class="text-danger" />
        <h3>No Matches Found</h3>
        <p>We couldn't find any providers, buckets, or objects matching "{{ query }}".</p>
      </div>

      <!-- Results Grid / Lists -->
      <div v-else class="results-layout-container">
        <!-- ALL FILTERS: Symmetrical 3-Column Workspace Grid -->
        <div v-if="activeFilter === 'all'" class="results-workspace-grid">
          <!-- Column 1: Storage Providers -->
          <div class="results-workspace-column" v-if="matchedProviders.length > 0">
            <div class="results-block-header">
              <Server :size="15" class="text-accent" />
              <h3>Providers ({{ matchedProviders.length }})</h3>
            </div>
            <div class="search-results-grid">
              <div v-for="p in matchedProviders" :key="p.id" class="search-result-card">
                <div class="card-main-row">
                  <div class="result-avatar provider-avatar-tint">
                    <Server :size="15" class="text-accent" />
                  </div>
                  <div class="card-left-info">
                    <strong>{{ p.name }}</strong>
                    <span class="subtext">
                      <span class="badge-type">{{ p.type.toUpperCase() }}</span>
                    </span>
                  </div>
                </div>
                <NuxtLink :to="`/providers/${encodeURIComponent(p.id)}`" class="btn btn-secondary btn-icon-round" title="View provider details">
                  <ArrowRight :size="14" />
                </NuxtLink>
              </div>
            </div>
          </div>

          <!-- Column 2: Buckets -->
          <div class="results-workspace-column" v-if="matchedBuckets.length > 0">
            <div class="results-block-header">
              <Folder :size="15" class="text-success" />
              <h3>Buckets ({{ matchedBuckets.length }})</h3>
            </div>
            <div class="search-results-grid">
              <div v-for="b in matchedBuckets" :key="`${b.providerId}-${b.name}`" class="search-result-card">
                <div class="card-main-row">
                  <div class="result-avatar bucket-avatar-tint">
                    <Folder :size="15" class="text-accent" />
                  </div>
                  <div class="card-left-info">
                    <strong>{{ b.name }}</strong>
                    <span class="subtext">On {{ b.providerName }}</span>
                  </div>
                </div>
                <NuxtLink
                  :to="`/providers/${encodeURIComponent(b.providerId)}/buckets/${encodeURIComponent(b.name)}`"
                  class="btn btn-secondary btn-icon-round"
                  title="Explore bucket"
                >
                  <ArrowRight :size="14" />
                </NuxtLink>
              </div>
            </div>
          </div>

          <!-- Column 3: Indexed Objects -->
          <div class="results-workspace-column" v-if="objects.length > 0">
            <div class="results-block-header">
              <File :size="15" class="text-warning" />
              <h3>Objects ({{ objects.length }})</h3>
            </div>
            <div class="search-results-grid">
              <div v-for="obj in objects" :key="obj.key" class="search-result-card">
                <div class="card-main-row">
                  <div class="result-avatar object-avatar-tint">
                    <File :size="15" class="text-accent" />
                  </div>
                  <div class="card-left-info">
                    <strong :title="obj.key">{{ obj.key.split('/').pop() }}</strong>
                    <span class="subtext font-mono" :title="obj.key">
                      {{ obj.key.substring(0, obj.key.lastIndexOf('/') + 1) || '/' }}
                    </span>
                  </div>
                </div>
                <NuxtLink
                  :to="`/providers/${encodeURIComponent(obj.provider)}/buckets/${encodeURIComponent(obj.bucket)}?prefix=${encodeURIComponent(obj.key.substring(0, obj.key.lastIndexOf('/') + 1))}`"
                  class="btn btn-secondary btn-icon-round"
                  title="Go to file path"
                >
                  <ArrowRight :size="14" />
                </NuxtLink>
              </div>
            </div>
          </div>
        </div>

        <!-- SPECIFIC FILTER VIEW: Full-Width Detailed List with Richer Metadata -->
        <div v-else class="results-detailed-view">
          <!-- Providers Only -->
          <div v-if="activeFilter === 'providers'" class="results-block">
            <div class="results-block-header">
              <Server :size="16" />
              <h3>Matching Storage Providers</h3>
            </div>
            <div class="search-results-grid">
              <div v-for="p in matchedProviders" :key="p.id" class="search-result-card detailed-card">
                <div class="card-main-row">
                  <div class="result-avatar provider-avatar-tint larger-avatar">
                    <Server :size="18" class="text-accent" />
                  </div>
                  <div class="card-left-info">
                    <strong>{{ p.name }}</strong>
                    <div class="details-meta-row mt-4">
                      <span class="badge-type">{{ p.type.toUpperCase() }}</span>
                      <span class="meta-dot">·</span>
                      <code class="meta-endpoint">{{ p.endpoint_url || 'AWS Edge' }}</code>
                    </div>
                  </div>
                </div>
                <NuxtLink :to="`/providers/${encodeURIComponent(p.id)}`" class="btn btn-secondary flex-center gap-6" title="View provider details">
                  <span>Manage</span>
                  <ArrowRight :size="14" />
                </NuxtLink>
              </div>
            </div>
          </div>

          <!-- Buckets Only -->
          <div v-if="activeFilter === 'buckets'" class="results-block">
            <div class="results-block-header">
              <Folder :size="16" />
              <h3>Matching Buckets</h3>
            </div>
            <div class="search-results-grid">
              <div v-for="b in matchedBuckets" :key="`${b.providerId}-${b.name}`" class="search-result-card detailed-card">
                <div class="card-main-row">
                  <div class="result-avatar bucket-avatar-tint larger-avatar">
                    <Folder :size="18" class="text-success" />
                  </div>
                  <div class="card-left-info">
                    <strong>{{ b.name }}</strong>
                    <div class="details-meta-row mt-4">
                      <span class="badge-type">{{ b.providerType.toUpperCase() }}</span>
                      <span class="meta-dot">·</span>
                      <span class="meta-label">Provider:</span>
                      <span class="meta-value">{{ b.providerName }}</span>
                    </div>
                  </div>
                </div>
                <NuxtLink
                  :to="`/providers/${encodeURIComponent(b.providerId)}/buckets/${encodeURIComponent(b.name)}`"
                  class="btn btn-secondary flex-center gap-6"
                  title="Explore bucket"
                >
                  <span>Explore</span>
                  <ArrowRight :size="14" />
                </NuxtLink>
              </div>
            </div>
          </div>

          <!-- Objects Only -->
          <div v-if="activeFilter === 'objects'" class="results-block">
            <div class="results-block-header">
              <File :size="16" />
              <h3>Matching Indexed Storage Objects</h3>
            </div>
            <div class="search-results-grid">
              <div v-for="obj in objects" :key="obj.key" class="search-result-card detailed-card">
                <div class="card-main-row">
                  <div class="result-avatar object-avatar-tint larger-avatar">
                    <File :size="18" class="text-warning" />
                  </div>
                  <div class="card-left-info">
                    <strong>{{ obj.key.split('/').pop() }}</strong>
                    <div class="details-meta-row mt-4 flex-wrap gap-8">
                      <span class="badge-ext" :class="getExtensionBadgeClass(obj.key)">
                        {{ obj.key.split('.').pop() || 'file' }}
                      </span>
                      <span class="meta-dot">·</span>
                      <span class="meta-label">Path:</span>
                      <span class="meta-value font-mono">{{ obj.key.substring(0, obj.key.lastIndexOf('/') + 1) || '/' }}</span>
                      <span class="meta-dot">·</span>
                      <span class="meta-label">Size:</span>
                      <span class="meta-value font-mono font-bold">{{ formatBytes(obj.size) }}</span>
                    </div>
                  </div>
                </div>
                <NuxtLink
                  :to="`/providers/${encodeURIComponent(obj.provider)}/buckets/${encodeURIComponent(obj.bucket)}?prefix=${encodeURIComponent(obj.key.substring(0, obj.key.lastIndexOf('/') + 1))}`"
                  class="btn btn-secondary flex-center gap-6"
                  title="Go to file path"
                >
                  <span>Locate</span>
                  <ArrowRight :size="14" />
                </NuxtLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.large-search-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  margin: 0 auto;
}

.search-bar-huge {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0 18px;
  height: 48px;
  box-shadow: 0 8px 32px rgb(15 23 42 / 6%);
}

.search-bar-huge:focus-within {
  border-color: var(--accent);
  box-shadow: 0 12px 30px rgba(23, 107, 135, 0.08), 0 0 0 3px var(--accent-soft);
}

.search-bar-huge input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 16px;
  font-weight: 500;
  color: var(--text);
  width: 100%;
}

.search-iconmuted {
  color: var(--muted);
}

.search-shortcut-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--border-soft);
  border: 1px solid var(--border);
  border-radius: 5px;
  width: 22px;
  height: 22px;
  font-size: 11px;
  font-weight: 700;
  color: var(--muted-strong);
  pointer-events: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.kbd-hint {
  font-family: inherit;
  background: var(--border-soft);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 11px;
  font-weight: 700;
  color: var(--muted-strong);
}

.filter-pills-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  padding: 0 14px;
  border-radius: 16px;
  background: var(--panel);
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  outline: none;
}

.pill-btn:hover {
  background: var(--panel-subtle);
  color: var(--text);
  border-color: var(--muted);
}

.pill-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #ffffff;
  box-shadow: 0 4px 12px rgb(23 107 135 / 15%);
}

.pill-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 700;
  border-radius: 10px;
  background: var(--border-soft);
  color: var(--muted-strong);
}

.pill-btn.active .pill-badge {
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.search-results-section {
  width: 100%;
  margin-top: 36px;
}

/* Polished empty dashboard panels */
.empty-dashboard-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 32px;
  background: var(--panel);
  border: 1px dashed var(--border);
  border-radius: 16px;
  max-width: 600px;
  margin: 32px auto 0 auto;
  box-shadow: 0 4px 12px rgb(15 23 42 / 1%);
}

.empty-dashboard-state h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin: 16px 0 6px 0;
}

.empty-dashboard-state p {
  font-size: 13px;
  color: var(--muted);
  max-width: 380px;
  margin: 0;
  line-height: 1.4;
}

.search-initial {
  margin-top: 48px;
}

/* Results Symmetrical Dashboard Columns */
.results-workspace-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(310px, 1fr));
  gap: 24px;
  margin-top: 16px;
  width: 100%;
}

.results-workspace-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: var(--panel-subtle);
  border: 1px solid var(--border-soft);
  border-radius: 14px;
  padding: 16px;
  min-width: 0;
}

.results-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.results-block-header {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  border-bottom: 1px solid var(--border-soft);
  padding-bottom: 12px;
  margin-bottom: 16px;
  margin-top: 8px;
}

.results-block-header h3 {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.search-results-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Polished Search Result Cards */
.search-result-card {
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  transition: all 0.15s ease;
}

.search-result-card:hover {
  border-color: var(--accent);
  background: var(--panel-subtle);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgb(15 23 42 / 2%);
}

.detailed-card {
  padding: 16px 20px;
}

.card-main-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  min-width: 0;
}

.result-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  flex-shrink: 0;
}

.larger-avatar {
  width: 42px;
  height: 42px;
  border-radius: 10px;
}

.provider-avatar-tint {
  background: var(--accent-soft);
}

.bucket-avatar-tint {
  background: var(--success-soft);
}

.bucket-avatar-tint svg {
  color: var(--success) !important;
}

.object-avatar-tint {
  background: var(--warning-soft);
}

.object-avatar-tint svg {
  color: var(--warning) !important;
}

.badge-type {
  font-size: 9px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--border-soft);
  color: var(--muted-strong);
}

.btn-icon-round {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50% !important;
  padding: 0 !important;
  border: 1px solid var(--border) !important;
  background: var(--panel) !important;
  color: var(--muted) !important;
  transition: all 0.12s ease !important;
  cursor: pointer;
}

.btn-icon-round:hover {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 10px rgba(23, 107, 135, 0.2);
}

.card-left-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.card-left-info strong {
  font-size: 13px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-left-info .subtext {
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Detailed card metadata rows */
.details-meta-row {
  display: flex;
  align-items: center;
  font-size: 11px;
  color: var(--muted);
  gap: 6px;
}

.meta-dot {
  color: var(--border);
  font-weight: 700;
}

.meta-label {
  color: var(--muted-strong);
  font-weight: 500;
}

.meta-value {
  color: var(--text);
  font-weight: 600;
}

.meta-endpoint {
  font-family: monospace;
  background: var(--border-soft);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--muted-strong);
}

/* File extension badges */
.badge-ext {
  font-size: 9px;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.ext-image { background: rgba(59, 130, 246, 0.1); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.15); }
.ext-config { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.15); }
.ext-archive { background: rgba(139, 92, 246, 0.1); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.15); }
.ext-doc { background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.15); }
.ext-code { background: rgba(236, 72, 153, 0.1); color: #ec4899; border: 1px solid rgba(236, 72, 153, 0.15); }
.ext-default { background: var(--border-soft); color: var(--muted-strong); border: 1px solid var(--border); }

.font-mono {
  font-family: monospace;
}

.mt-24 {
  margin-top: 24px;
}
</style>
