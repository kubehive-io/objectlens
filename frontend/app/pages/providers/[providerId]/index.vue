<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import type {
  Bucket,
  ProviderConnection,
  ProviderStatus,
} from "../../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../../composables/useObjectLensApi";
import {
  Server,
  ShieldCheck,
  AlertCircle,
  Database,
  PlusCircle,
  FolderOpen,
  ArrowRight,
  Settings,
  Calendar,
  Activity,
  HardDrive,
  Cloud,
  Globe,
  Upload,
  Info
} from "@lucide/vue";

const route = useRoute();
const router = useRouter();
const api = useObjectLensApi();

const providerId = computed(() => String(route.params.providerId || ""));
const provider = ref<ProviderConnection | null>(null);
const status = ref<ProviderStatus | null>(null);
const buckets = ref<Bucket[]>([]);
const loading = ref(true);
const error = ref("");

function formatDate(value?: string | null) {
  if (!value) return "Creation date unavailable";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(
    new Date(value),
  );
}

onMounted(async () => {
  loading.value = true;
  try {
    provider.value = await api.providerConnection(providerId.value);
    status.value = await api.providerStatus(providerId.value);
    buckets.value = (await api.listProviderBuckets(providerId.value)).buckets;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load provider.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="provider-explore-page">
    <!-- Header -->
    <header class="page-title-section">
      <div class="header-text-block">
        <div class="title-with-icon-row">
          <Cloud v-if="provider?.type === 'aws'" :size="24" class="text-accent" />
          <Database v-else-if="provider?.type === 'ceph'" :size="24" class="text-accent" />
          <Server v-else :size="24" class="text-accent" />
          <h1>{{ provider?.name || providerId }}</h1>
        </div>
        <p class="subtitle">{{ provider?.description || `${provider?.display_name || 'Storage Endpoint'} · ${provider?.region || 'us-east-1'}` }}</p>
      </div>
      <div class="header-actions">
        <NuxtLink class="btn btn-secondary flex-center" :to="`/providers/${encodeURIComponent(providerId)}/details`">
          <Info :size="14" />
          <span>Details</span>
        </NuxtLink>
        <NuxtLink class="btn btn-secondary flex-center" :to="`/providers/${encodeURIComponent(providerId)}/details#settings`">
          <Settings :size="14" />
          <span>Settings</span>
        </NuxtLink>
      </div>
    </header>

    <!-- Error Alert Panel -->
    <section v-if="error" class="error-panel mt-24" aria-label="Error feedback">
      <div class="error-panel-icon"><AlertCircle :size="32" class="text-danger" /></div>
      <div class="error-panel-text">
        <h3>Provider Connection Failed</h3>
        <p>ObjectLens was unable to connect to this storage provider. Please verify your keys and endpoint settings.</p>
        <code class="error-log">{{ error }}</code>
      </div>
    </section>

    <template v-else>
      <!-- Metrics Grid -->
      <section class="metrics-card-grid" aria-label="Provider metrics summary">
        <!-- Metric 1: Provider type -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Provider Connection</span>
            <Server :size="16" class="metric-icon muted" />
          </div>
          <div class="metric-content">
            <strong class="uppercase-text">{{ provider?.type || "object" }}</strong>
            <span class="metric-trend">{{ provider?.region }}</span>
          </div>
          <p class="metric-caption text-ellipsis" :title="provider?.endpoint_url || 'Global Storage Endpoint'">
            {{ provider?.endpoint_url || "Global Storage Endpoint" }}
          </p>
        </article>

        <!-- Metric 2: status -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Health Status</span>
            <Activity :size="16" class="metric-icon muted" />
          </div>
          <div class="metric-content">
            <strong :class="status?.status === 'healthy' ? 'text-success' : 'text-danger'">
              {{ status?.status === 'healthy' ? 'Healthy' : 'Error' }}
            </strong>
            <span class="metric-trend success" v-if="status?.status === 'healthy'">Connected</span>
            <span class="metric-trend danger" v-else>Offline</span>
          </div>
          <p class="metric-caption text-ellipsis" :title="status?.message || 'Checking status...'">
            {{ status?.message || "Checking status..." }}
          </p>
        </article>

        <!-- Metric 3: buckets -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Visible Buckets</span>
            <FolderOpen :size="16" class="metric-icon muted" />
          </div>
          <div class="metric-content">
            <strong>{{ loading ? "..." : buckets.length }}</strong>
            <span class="metric-trend">Authorized</span>
          </div>
          <p class="metric-caption">Number of buckets returned by credentials.</p>
        </article>
      </section>

      <!-- Buckets catalog list -->
      <section class="dashboard-content-block mt-32">
        <div class="block-header border-bottom pb-12 mb-24">
          <div>
            <h2>Discovered Buckets</h2>
            <p>Only buckets available under these credentials are shown below.</p>
          </div>
        </div>

        <div v-if="loading" class="dashboard-skeleton-loader">
          <div class="skeleton-card" v-for="i in 2" :key="i" />
        </div>

        <div v-else-if="buckets.length === 0" class="empty-dashboard-state">
          <FolderOpen :size="48" class="muted" />
          <h3>No Buckets Discovered</h3>
          <p>This storage connection returned 0 visible buckets. Try creating a bucket using your provider console or Settings.</p>
        </div>

        <div v-else class="bucket-grid">
          <article
            v-for="bucket in buckets"
            :key="bucket.name"
            class="modern-provider-card bucket-explore-card"
          >
            <div class="card-top-row">
              <span class="provider-type-badge">bucket</span>
              <span class="provider-status-badge healthy">
                <span class="status-dot-indicator" />
                <span>Authorized</span>
              </span>
            </div>

            <div class="card-main-info">
              <div class="bucket-title-block">
                <FolderOpen :size="18" class="text-accent flex-shrink-0" />
                <h3>{{ bucket.name }}</h3>
              </div>
              <p class="description">{{ provider?.description || "Active storage bucket. Explore folders, files, and edit metadata indices." }}</p>
              <div class="connection-meta">
                <span class="endpoint"><Calendar :size="11" /> Created: {{ formatDate(bucket.creation_date) }}</span>
              </div>
            </div>

            <!-- Action buttons footer -->
            <div class="card-actions-footer">
              <NuxtLink
                class="btn btn-primary flex-center"
                :to="`/providers/${encodeURIComponent(providerId)}/buckets/${encodeURIComponent(bucket.name)}`"
              >
                <span>Browse Files</span>
                <ArrowRight :size="14" />
              </NuxtLink>
              <NuxtLink
                class="btn btn-secondary"
                :to="`/providers/${encodeURIComponent(providerId)}/buckets/${encodeURIComponent(bucket.name)}/details`"
              >
                Details
              </NuxtLink>
              <NuxtLink
                class="btn btn-secondary icon-only"
                :to="`/providers/${encodeURIComponent(providerId)}/buckets/${encodeURIComponent(bucket.name)}/upload`"
                title="Upload files"
              >
                <Upload :size="14" />
              </NuxtLink>
            </div>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.provider-explore-page {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.title-with-icon-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-with-icon-row h1 {
  margin: 0 !important;
}

.bucket-explore-card {
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

.uppercase-text {
  text-transform: uppercase;
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pb-12 {
  padding-bottom: 12px;
}

.mb-24 {
  margin-bottom: 24px;
}

.border-bottom {
  border-bottom: 1px solid var(--border-soft);
}

.mt-32 {
  margin-top: 32px;
}

.flex-shrink-0 {
  flex-shrink: 0;
}
</style>
