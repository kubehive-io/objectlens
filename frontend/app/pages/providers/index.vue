<script setup lang="ts">
import { ref, onMounted } from "vue";
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
  Settings
} from "@lucide/vue";

const api = useObjectLensApi();

const providers = ref<ProviderConnection[]>([]);
const bucketCounts = ref<Record<string, number>>({});
const statuses = ref<Record<string, ProviderStatus>>({});
const loading = ref(true);
const error = ref("");

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
      <div class="header-actions">
        <NuxtLink to="/settings" class="btn btn-secondary flex-center">
          <PlusCircle :size="16" />
          <span>Add Provider</span>
        </NuxtLink>
      </div>
    </header>

    <!-- Error state feedback -->
    <section v-if="error" class="error-panel" aria-label="Error feedback">
      <div class="error-panel-icon"><AlertCircle :size="32" class="text-danger" /></div>
      <div class="error-panel-text">
        <h3>Failed to Retrieve Providers</h3>
        <p>ObjectLens encountered an issue while communicating with the backend registry API.</p>
        <code class="error-log">{{ error }}</code>
      </div>
    </section>

    <!-- Providers list block -->
    <section v-else class="dashboard-content-block">
      <div v-if="loading" class="dashboard-skeleton-loader">
        <div class="skeleton-card" v-for="i in 3" :key="i" />
      </div>

      <div v-else-if="providers.length === 0" class="empty-dashboard-state">
        <Server :size="48" class="muted" />
        <h3>No Provider Connections Configured</h3>
        <p>Add individual provider manifest files in your <code>backend/data/providers/</code> folder to configure them.</p>
        <NuxtLink to="/settings" class="btn btn-primary mt-12">Configure Provider</NuxtLink>
      </div>

      <div v-else class="provider-grid">
        <article
          v-for="provider in providers"
          :key="provider.id"
          class="modern-provider-card"
        >
          <div class="card-top-row">
            <span class="provider-type-badge">{{ provider.type }}</span>
            <span
              class="provider-status-badge"
              :class="statuses[provider.id]?.status === 'healthy' ? 'healthy' : 'unhealthy'"
            >
              <span class="status-dot-indicator" />
              <span>{{ statuses[provider.id]?.status === 'healthy' ? 'Healthy' : 'Error' }}</span>
            </span>
          </div>

          <div class="card-main-info">
            <h3>{{ provider.name }}</h3>
            <p class="description">{{ provider.description || "No description provided." }}</p>
            <div class="connection-meta">
              <span class="endpoint">{{ provider.endpoint_url || "AWS Global Edge" }}</span>
              <span class="region" v-if="provider.region && provider.endpoint_url">· {{ provider.region }}</span>
            </div>
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
              <span>Open</span>
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
  </div>
</template>
