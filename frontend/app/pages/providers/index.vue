<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import type { ProviderConnection, ProviderStatus } from "../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../composables/useObjectLensApi";
import {
  Server,
  ShieldCheck,
  AlertCircle,
  ArrowRight,
  Database,
  PlusCircle,
  HelpCircle,
  Activity,
  Settings,
  Search,
  Globe,
  HardDrive,
  Cpu,
  Cloud,
  FolderOpen
} from "@lucide/vue";

const api = useObjectLensApi();

const providers = ref<ProviderConnection[]>([]);
const bucketCounts = ref<Record<string, number>>({});
const statuses = ref<Record<string, ProviderStatus>>({});
const loading = ref(true);
const search = ref("");
const error = ref("");

const filteredProviders = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return providers.value;
  return providers.value.filter(
    p =>
      p.name.toLowerCase().includes(query) ||
      p.type.toLowerCase().includes(query) ||
      (p.description && p.description.toLowerCase().includes(query)) ||
      (p.endpoint_url && p.endpoint_url.toLowerCase().includes(query))
  );
});

// Calculate metric overviews
const healthyCount = computed(() => {
  return Object.values(statuses.value).filter(s => s.status === "healthy").length;
});

const totalVisibleBuckets = computed(() => {
  return Object.values(bucketCounts.value).reduce((sum, count) => sum + count, 0);
});

onMounted(async () => {
  loading.value = true;
  error.value = "";
  try {
    providers.value = await api.listProviders();
    for (const provider of providers.value) {
      try {
        const status = await api.providerStatus(provider.id);
        statuses.value[provider.id] = status;
        bucketCounts.value[provider.id] = status.visible_bucket_count;
      } catch {
        bucketCounts.value[provider.id] = 0;
      }
    }
  } catch (err) {
    error.value =
      err instanceof Error
        ? err.message
        : "Failed to load provider connections. Check your API backend.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="providers-page">
    <!-- Header -->
    <header class="page-title-section">
      <div class="header-text-block">
        <h1>Storage Providers</h1>
        <p class="subtitle">Register, monitor, and explore S3-compatible, Ceph RGW, and Garage endpoints.</p>
      </div>
      <div class="header-actions" v-if="!loading && providers.length > 0">
        <NuxtLink to="/settings" class="btn btn-secondary flex-center">
          <PlusCircle :size="16" />
          <span>Add Connection</span>
        </NuxtLink>
      </div>
    </header>

    <!-- Error state feedback -->
    <section v-if="error" class="error-panel mt-24" aria-label="Error feedback">
      <div class="error-panel-icon"><AlertCircle :size="32" class="text-danger" /></div>
      <div class="error-panel-text">
        <h3>Failed to Retrieve Providers</h3>
        <p>ObjectLens encountered an issue while communicating with the backend registry API.</p>
        <code class="error-log">{{ error }}</code>
      </div>
    </section>

    <!-- Loading Skeleton state -->
    <div v-else-if="loading" class="dashboard-skeleton-loader mt-24">
      <div class="skeleton-card" v-for="i in 3" :key="i" />
    </div>

    <!-- DEDICATED EMPTY ONBOARDING HERO (When total connections is 0) -->
    <section v-else-if="providers.length === 0" class="empty-onboarding-hero">
      <div class="hero-icon-container">
        <Server :size="40" class="text-accent" />
      </div>
      <h2>Connect Your First Storage Provider</h2>
      <p class="hero-desc">
        ObjectLens coordinates and indexes storage nodes dynamically. Get started by placing a single <code>Provider</code> manifest in your backend directory or importing development templates.
      </p>

      <div class="onboarding-guide-box">
        <h4>Quick Onboarding Guide</h4>
        <p class="small-muted-text mb-8">Run this terminal command at your project root to copy all mock local-dev templates:</p>
        <pre class="code-pre-box"><code>mkdir -p backend/data/providers
cp example/providers/*.yaml backend/data/providers/</code></pre>
      </div>

      <div class="hero-actions-row">
        <NuxtLink to="/settings" class="btn btn-primary flex-center">
          <PlusCircle :size="14" />
          <span>Configure Connection</span>
        </NuxtLink>
        <a href="https://github.com/google/gemini-cli" target="_blank" class="btn btn-secondary flex-center">
          <HelpCircle :size="14" />
          <span>Read Documentation</span>
        </a>
      </div>
    </section>

    <!-- FULL SAAS LAYOUT (When connections exist) -->
    <template v-else>
      <!-- Metrics Cards Row -->
      <section class="metrics-card-grid mt-24" aria-label="Providers metrics summary">
        <!-- Metric 1: Total Providers count -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Registered Connections</span>
            <Server :size="16" class="metric-icon muted" />
          </div>
          <div class="metric-content">
            <strong>{{ providers.length }}</strong>
            <span class="metric-trend">{{ healthyCount }} healthy</span>
          </div>
          <p class="metric-caption">Storage nodes active in <code>providers/</code> directory.</p>
        </article>

        <!-- Metric 2: Primary types -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Active Technologies</span>
            <Activity :size="16" class="metric-icon muted" />
          </div>
          <div class="metric-content">
            <strong>S3 / Ceph</strong>
            <span class="metric-trend success">Multi-cloud</span>
          </div>
          <p class="metric-caption">Unified access layer for multiple RGW backends.</p>
        </article>

        <!-- Metric 3: visible buckets -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Discovered Buckets</span>
            <FolderOpen :size="16" class="metric-icon muted" />
          </div>
          <div class="metric-content">
            <strong>{{ totalVisibleBuckets }}</strong>
            <span class="metric-trend">Aggregate total</span>
          </div>
          <p class="metric-caption">Total buckets visible under current auth scope.</p>
        </article>
      </section>

      <!-- Filter Toolbar -->
      <section class="toolbar mt-24">
        <div class="toolbar-search-box">
          <Search :size="15" class="search-icon" />
          <input v-model="search" placeholder="Search connections by name, endpoint, type, or region..." />
        </div>
        <div class="toolbar-controls-right">
          <span class="range-indicator">{{ filteredProviders.length }} connection{{ filteredProviders.length === 1 ? '' : 's' }}</span>
        </div>
      </section>

      <!-- Providers Grid -->
      <section class="dashboard-content-block">
        <!-- Search filter yields no results -->
        <div v-if="filteredProviders.length === 0" class="empty-dashboard-state">
          <Search :size="48" class="muted" />
          <h3>No Connections Match Your Search</h3>
          <p>No providers match the keyword "{{ search }}". Try checking your spelling or filters.</p>
          <button class="btn btn-secondary mt-12" @click="search = ''">Clear Search</button>
        </div>

        <div v-else class="provider-grid">
          <article
            v-for="provider in filteredProviders"
            :key="provider.id"
            class="modern-provider-card provider-dashboard-card"
            :class="statuses[provider.id]?.status === 'healthy' ? 'healthy-border' : 'unhealthy-border'"
          >
            <div class="card-top-row">
              <span class="provider-type-badge">{{ provider.type }}</span>
              <span
                class="provider-status-badge"
                :class="statuses[provider.id]?.status === 'healthy' ? 'healthy' : 'unhealthy'"
              >
                <span class="status-dot-indicator" />
                <span>{{ statuses[provider.id]?.status === 'healthy' ? 'Healthy' : 'Offline' }}</span>
              </span>
            </div>

            <div class="card-main-info">
              <div class="provider-title-row">
                <Cloud v-if="provider.type === 'aws'" :size="20" class="text-accent flex-shrink-0" />
                <Database v-else-if="provider.type === 'ceph'" :size="20" class="text-accent flex-shrink-0" />
                <Cpu v-else :size="20" class="text-accent flex-shrink-0" />
                <h3 class="margin-0">{{ provider.name }}</h3>
              </div>
              
              <p class="description">{{ provider.description || "No description provided." }}</p>
              
              <dl class="provider-card-meta-list">
                <div class="meta-row">
                  <dt><Globe :size="12" /> Endpoint URL</dt>
                  <dd :title="provider.endpoint_url || 'AWS S3 Edge'">
                    <code>{{ provider.endpoint_url || "AWS S3 Edge" }}</code>
                  </dd>
                </div>
                <div class="meta-row" v-if="provider.region">
                  <dt><HardDrive :size="12" /> Active Region</dt>
                  <dd>{{ provider.region }}</dd>
                </div>
              </dl>

              <p class="bucket-indicator">
                <strong>{{ bucketCounts[provider.id] ?? 0 }}</strong> buckets visible
              </p>
            </div>

            <!-- Tag row -->
            <div class="tag-row" v-if="provider.tags && provider.tags.length > 0">
              <span v-for="tag in provider.tags" :key="tag" class="tag-pill">{{ tag }}</span>
            </div>

            <!-- Action buttons footer -->
            <div class="card-actions-footer">
              <NuxtLink class="btn btn-primary flex-center" :to="`/providers/${encodeURIComponent(provider.id)}`">
                <span>Explore</span>
                <ArrowRight :size="14" />
              </NuxtLink>
              <NuxtLink class="btn btn-secondary" :to="`/providers/${encodeURIComponent(provider.id)}/details`">
                Details
              </NuxtLink>
              <NuxtLink class="btn btn-secondary icon-only" :to="`/providers/${encodeURIComponent(provider.id)}/details#settings`" title="Settings">
                <Settings :size="14" />
              </NuxtLink>
            </div>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.empty-onboarding-hero {
  max-width: 600px;
  margin: 64px auto 0 auto;
  text-align: center;
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 12px 36px rgb(15 23 42 / 6%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.hero-icon-container {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--accent-soft);
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-onboarding-hero h2 {
  font-size: 22px;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.5px;
}

.hero-desc {
  font-size: 14px;
  color: var(--muted);
  line-height: 1.5;
  margin: 0;
}

.onboarding-guide-box {
  width: 100%;
  text-align: left;
  background: var(--panel-subtle);
  border: 1px solid var(--border-soft);
  border-radius: 10px;
  padding: 16px;
}

.onboarding-guide-box h4 {
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 8px 0;
}

.code-pre-box {
  background: var(--code-bg);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 12px;
  margin: 0;
  overflow-x: auto;
}

.code-pre-box code {
  font-family: monospace;
  font-size: 11px;
  color: var(--text);
  white-space: pre;
}

.hero-actions-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.provider-dashboard-card {
  border-top: 3px solid var(--border-soft);
}

.provider-dashboard-card.healthy-border:hover {
  border-top-color: var(--success);
}

.provider-dashboard-card.unhealthy-border:hover {
  border-top-color: var(--danger);
}

.provider-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.provider-title-row h3 {
  margin: 0 !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.provider-card-meta-list {
  margin: 0 0 16px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-row dt {
  font-size: 11px;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-row dd {
  font-size: 12px;
  font-weight: 600;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta-row dd code {
  font-size: 11px;
}

.margin-0 {
  margin: 0 !important;
}

.mt-24 {
  margin-top: 24px;
}

.flex-shrink-0 {
  flex-shrink: 0;
}
</style>
