<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
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

// Fetch providers and buckets on mount
onMounted(async () => {
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
        <p class="subtitle">Query and locate storage connections, buckets, and S3 metadata indexes instantly.</p>
      </div>
    </header>

    <!-- Large Centered Search Box -->
    <section class="large-search-container">
      <div class="search-bar-huge">
        <Search :size="24" class="search-iconmuted" />
        <input
          v-model="query"
          type="text"
          placeholder="Type name, provider, prefix, or S3 filename..."
          autofocus
          aria-label="Global search input"
        />
        <Loader v-if="loading" :size="20" class="spin text-accent" />
      </div>

      <!-- Filter Pills -->
      <div class="filter-pills-row" v-if="query.trim().length > 0">
        <button
          class="pill-btn"
          :class="{ active: activeFilter === 'all' }"
          type="button"
          @click="activeFilter = 'all'"
        >
          All ({{ matchedProviders.length + matchedBuckets.length + objects.length }})
        </button>
        <button
          class="pill-btn"
          :class="{ active: activeFilter === 'providers' }"
          type="button"
          @click="activeFilter = 'providers'"
        >
          Providers ({{ matchedProviders.length }})
        </button>
        <button
          class="pill-btn"
          :class="{ active: activeFilter === 'buckets' }"
          type="button"
          @click="activeFilter = 'buckets'"
        >
          Buckets ({{ matchedBuckets.length }})
        </button>
        <button
          class="pill-btn"
          :class="{ active: activeFilter === 'objects' }"
          type="button"
          @click="activeFilter = 'objects'"
        >
          Objects ({{ objects.length }})
        </button>
      </div>
    </section>

    <!-- Results Area -->
    <section class="search-results-section">
      <!-- Empty/Initial State -->
      <div v-if="!query.trim()" class="empty-dashboard-state search-initial">
        <Search :size="48" class="muted" />
        <h3>Locate Anything Instantly</h3>
        <p>Type a storage key, provider name, or prefix to find matches across your entire storage ecosystem.</p>
      </div>

      <!-- No Results State -->
      <div v-else-if="!hasResults" class="empty-dashboard-state">
        <AlertCircle :size="48" class="text-danger" />
        <h3>No Matches Found</h3>
        <p>We couldn't find any providers, buckets, or objects matching "{{ query }}".</p>
      </div>

      <!-- Results Grid / Lists -->
      <div v-else class="results-layout-container">
        <!-- 1. Match: Providers -->
        <div
          v-if="matchedProviders.length > 0 && (activeFilter === 'all' || activeFilter === 'providers')"
          class="results-block"
        >
          <div class="results-block-header">
            <Server :size="16" />
            <h3>Matching Storage Providers</h3>
          </div>
          <div class="search-results-grid">
            <div v-for="p in matchedProviders" :key="p.id" class="search-result-card">
              <div class="card-left-info">
                <strong>{{ p.name }}</strong>
                <span class="subtext">{{ p.type }} · {{ p.endpoint_url || 'AWS Edge' }}</span>
              </div>
              <NuxtLink :to="`/providers/${encodeURIComponent(p.id)}`" class="btn btn-secondary icon-only">
                <ArrowRight :size="14" />
              </NuxtLink>
            </div>
          </div>
        </div>

        <!-- 2. Match: Buckets -->
        <div
          v-if="matchedBuckets.length > 0 && (activeFilter === 'all' || activeFilter === 'buckets')"
          class="results-block mt-24"
        >
          <div class="results-block-header">
            <Folder :size="16" />
            <h3>Matching Buckets</h3>
          </div>
          <div class="search-results-grid">
            <div v-for="b in matchedBuckets" :key="`${b.providerId}-${b.name}`" class="search-result-card">
              <div class="card-left-info">
                <strong>{{ b.name }}</strong>
                <span class="subtext">On {{ b.providerName }} ({{ b.providerType }})</span>
              </div>
              <NuxtLink
                :to="`/providers/${encodeURIComponent(b.providerId)}/buckets/${encodeURIComponent(b.name)}`"
                class="btn btn-secondary icon-only"
              >
                <ArrowRight :size="14" />
              </NuxtLink>
            </div>
          </div>
        </div>

        <!-- 3. Match: Objects -->
        <div
          v-if="objects.length > 0 && (activeFilter === 'all' || activeFilter === 'objects')"
          class="results-block mt-24"
        >
          <div class="results-block-header">
            <File :size="16" />
            <h3>Matching Indexed S3 Objects</h3>
          </div>
          <div class="search-results-grid">
            <div v-for="obj in objects" :key="obj.key" class="search-result-card">
              <div class="card-left-info">
                <strong :title="obj.key">{{ obj.key.split('/').pop() }}</strong>
                <span class="subtext font-mono" :title="obj.key">{{ obj.key.substring(0, obj.key.lastIndexOf('/') + 1) || '/' }}</span>
              </div>
              <NuxtLink
                :to="`/providers/${encodeURIComponent(obj.provider)}/buckets/${encodeURIComponent(obj.bucket)}?prefix=${encodeURIComponent(obj.key.substring(0, obj.key.lastIndexOf('/') + 1))}`"
                class="btn btn-secondary icon-only"
                title="Go to file path"
              >
                <ArrowRight :size="14" />
              </NuxtLink>
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
  gap: 16px;
  max-width: 720px;
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

.filter-pills-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.pill-btn {
  height: 28px;
  padding: 0 12px;
  border-radius: 14px;
  background: var(--panel-subtle);
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.pill-btn:hover {
  background: var(--border-soft);
  color: var(--text);
}

.pill-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #ffffff;
}

.search-results-section {
  max-width: 720px;
  margin: 24px auto 0 auto;
}

.search-initial {
  margin-top: 48px;
}

.results-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.results-block-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  border-bottom: 1px solid var(--border-soft);
  padding-bottom: 8px;
  margin-bottom: 4px;
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

.search-result-card {
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  transition: border-color 0.15s ease;
}

.search-result-card:hover {
  border-color: var(--border);
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

.font-mono {
  font-family: monospace;
}

.mt-24 {
  margin-top: 24px;
}
</style>
