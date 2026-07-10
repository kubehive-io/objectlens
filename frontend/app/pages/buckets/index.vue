<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useObjectLensApi } from "../../composables/useObjectLensApi";
import {
  Folder,
  Search,
  Server,
  Calendar,
  ExternalLink,
  PlusCircle,
  HelpCircle,
  FolderOpen,
  ArrowRight,
  Database,
  Upload
} from "@lucide/vue";

interface UnifiedBucket {
  name: string;
  creation_date?: string | null;
  providerId: string;
  providerName: string;
  providerType: string;
}

const api = useObjectLensApi();

const buckets = ref<UnifiedBucket[]>([]);
const loading = ref(true);
const search = ref("");

const filteredBuckets = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return buckets.value;
  return buckets.value.filter(
    (b) =>
      b.name.toLowerCase().includes(query) ||
      b.providerName.toLowerCase().includes(query) ||
      b.providerType.toLowerCase().includes(query)
  );
});

onMounted(async () => {
  loading.value = true;
  try {
    const providers = await api.listProviders();
    const fetchPromises = providers.map(async (p) => {
      try {
        const res = await api.listProviderBuckets(p.id);
        return res.buckets.map((b) => ({
          name: b.name,
          creation_date: b.creation_date,
          providerId: p.id,
          providerName: p.name,
          providerType: p.type
        }));
      } catch (err) {
        console.error(`Failed to load buckets for provider ${p.id}:`, err);
        return [];
      }
    });
    
    const results = await Promise.all(fetchPromises);
    buckets.value = results.flat();
  } catch (err) {
    console.error("Failed to load providers / buckets:", err);
  } finally {
    loading.value = false;
  }
});

function formatDate(value?: string | null) {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(value));
}
</script>

<template>
  <div class="buckets-dashboard-page">
    <!-- Header -->
    <header class="page-title-section">
      <div class="header-text-block">
        <h1>Global Buckets</h1>
        <p class="subtitle">Unified catalog of all discoverable buckets across your active S3, Ceph, and Garage providers.</p>
      </div>
      <div class="header-actions">
        <NuxtLink to="/settings" class="btn btn-secondary flex-center">
          <PlusCircle :size="16" />
          <span>Configure Provider</span>
        </NuxtLink>
      </div>
    </header>

    <!-- Toolbar Filters -->
    <section class="toolbar">
      <div class="toolbar-search-box">
        <Search :size="15" class="search-icon" />
        <input v-model="search" placeholder="Search buckets by name, provider, or type..." />
      </div>
      <div class="toolbar-controls-right">
        <span class="range-indicator">{{ filteredBuckets.length }} bucket{{ filteredBuckets.length === 1 ? '' : 's' }}</span>
      </div>
    </section>

    <!-- Buckets Catalog List -->
    <section class="dashboard-content-block">
      <div v-if="loading" class="dashboard-skeleton-loader">
        <div class="skeleton-card" v-for="i in 3" :key="i" />
      </div>

      <div v-else-if="filteredBuckets.length === 0" class="empty-dashboard-state">
        <FolderOpen :size="48" class="muted" />
        <h3>No Buckets Found</h3>
        <p v-if="search">No buckets match your search query. Try typing something else.</p>
        <p v-else>No active provider connections yielded visible buckets. Check your credentials in settings.</p>
        <button class="btn btn-secondary mt-12" v-if="search" @click="search = ''">Clear Search</button>
      </div>

      <div v-else class="bucket-grid">
        <article
          v-for="bucket in filteredBuckets"
          :key="`${bucket.providerId}-${bucket.name}`"
          class="modern-provider-card bucket-catalog-card"
        >
          <div class="card-top-row">
            <span class="provider-type-badge">{{ bucket.providerType }}</span>
            <span class="provider-status-badge healthy">
              <span class="status-dot-indicator" />
              <span>{{ bucket.providerName }}</span>
            </span>
          </div>

          <div class="card-main-info">
            <div class="bucket-title-block">
              <Folder :size="20" class="text-accent flex-shrink-0" />
              <h3>{{ bucket.name }}</h3>
            </div>
            <p class="description">Global catalog bucket. Access folders, files, prefixes, and edit lifecycle settings.</p>
            <div class="connection-meta">
              <span class="endpoint"><Calendar :size="11" /> Created: {{ formatDate(bucket.creation_date) }}</span>
            </div>
          </div>

          <!-- Action buttons footer -->
          <div class="card-actions-footer">
            <NuxtLink
              class="btn btn-primary flex-center"
              :to="`/providers/${encodeURIComponent(bucket.providerId)}/buckets/${encodeURIComponent(bucket.name)}`"
            >
              <span>Explore</span>
              <ArrowRight :size="14" />
            </NuxtLink>
            <NuxtLink
              class="btn btn-secondary"
              :to="`/providers/${encodeURIComponent(bucket.providerId)}/buckets/${encodeURIComponent(bucket.name)}/details`"
            >
              Details
            </NuxtLink>
            <NuxtLink
              class="btn btn-secondary icon-only"
              :to="`/providers/${encodeURIComponent(bucket.providerId)}/buckets/${encodeURIComponent(bucket.name)}/upload`"
              title="Upload files"
            >
              <Upload :size="14" />
            </NuxtLink>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.bucket-catalog-card {
  border-left: 3px solid var(--accent);
}

.bucket-title-block {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.bucket-title-block h3 {
  margin: 0 !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.flex-shrink-0 {
  flex-shrink: 0;
}
</style>
