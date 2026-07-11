<script setup lang="ts">
import { ref, onMounted } from "vue";
import type { ProviderConnection } from "../composables/useObjectLensApi";
import { useObjectLensApi } from "../composables/useObjectLensApi";
import {
  Server,
  ShieldCheck,
  AlertCircle,
  ArrowRight,
  Database,
  FolderOpen,
  PlusCircle,
  HelpCircle,
  Activity,
  ChevronRight,
  Settings,
  BookOpen
} from "@lucide/vue";

const api = useObjectLensApi();

const providers = ref<ProviderConnection[]>([]);
const totalBucketsCount = ref(0);
const backendHealthy = ref(false);
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  loading.value = true;
  error.value = "";
  try {
    const health = await api.health();
    backendHealthy.value = health.status === "ok";
    providers.value = await api.listProviders();
    
    // Aggregate bucket counts quickly
    const bucketPromises = providers.value.map(async (p) => {
      try {
        const res = await api.listProviderBuckets(p.id);
        return res.buckets.length;
      } catch {
        return 0;
      }
    });
    const counts = await Promise.all(bucketPromises);
    totalBucketsCount.value = counts.reduce((sum, val) => sum + val, 0);
  } catch (err) {
    backendHealthy.value = false;
    error.value =
      err instanceof Error
        ? err.message
        : "ObjectLens backend is unavailable. Please verify your connection.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="dashboard-page">
    <!-- Header -->
    <header class="page-title-section">
      <div class="header-text-block">
        <h1>Dashboard</h1>
        <p class="subtitle">Unified overview of your cloud-native storage nodes and indexing health.</p>
      </div>
      <div class="header-actions">
        <a href="https://github.com/google/gemini-cli" target="_blank" class="btn btn-secondary flex-center">
          <HelpCircle :size="16" />
          <span>Documentation</span>
        </a>
      </div>
    </header>

    <!-- Metrics Grid -->
    <section class="metrics-card-grid" aria-label="Quick metrics">
      <!-- Metric 1: Backend API Health -->
      <article class="metric-card">
        <div class="metric-header">
          <span class="metric-title">Backend API Health</span>
          <Activity :size="16" class="metric-icon muted" />
        </div>
        <div class="metric-content">
          <strong :class="backendHealthy ? 'text-success' : 'text-danger'">
            {{ backendHealthy ? "Active" : "Offline" }}
          </strong>
          <span class="metric-trend success" v-if="backendHealthy">Reachable</span>
          <span class="metric-trend danger" v-else>Check logs</span>
        </div>
        <p class="metric-caption">
          {{ backendHealthy ? "FastAPI server is responding normally." : "Start the FastAPI backend with 'just dev'." }}
        </p>
      </article>

      <!-- Metric 2: Total Providers -->
      <article class="metric-card">
        <div class="metric-header">
          <span class="metric-title">Storage Providers</span>
          <Server :size="16" class="metric-icon muted" />
        </div>
        <div class="metric-content">
          <strong>{{ loading ? "..." : providers.length }}</strong>
          <span class="metric-trend" v-if="!loading">Connections</span>
        </div>
        <p class="metric-caption">Configured active storage connections.</p>
      </article>

      <!-- Metric 3: Total Buckets -->
      <article class="metric-card">
        <div class="metric-header">
          <span class="metric-title">Visible Buckets</span>
          <FolderOpen :size="16" class="metric-icon muted" />
        </div>
        <div class="metric-content">
          <strong>{{ loading ? "..." : totalBucketsCount }}</strong>
          <span class="metric-trend">Total catalog</span>
        </div>
        <p class="metric-caption">Discovered buckets across active keys.</p>
      </article>
    </section>

    <!-- Backend Error Panel -->
    <section v-if="error" class="error-panel" aria-label="Error feedback">
      <div class="error-panel-icon"><AlertCircle :size="32" class="text-danger" /></div>
      <div class="error-panel-text">
        <h3>Backend API Connection Refused</h3>
        <p>
          The dashboard loaded successfully, but it is unable to establish an API connection. Please ensure that the ObjectLens backend is running on the configured port.
        </p>
        <code class="error-log">{{ error }}</code>
      </div>
    </section>

    <!-- Getting Started Guides -->
    <section v-else class="dashboard-content-block">
      <div class="block-header section-block-header">
        <div>
          <h2 class="section-title-large">Explore ObjectLens</h2>
          <p class="subtitle">Quick shortcuts to browse, connect, and configure your object storage ecosystem.</p>
        </div>
      </div>

      <div class="provider-grid">
        <!-- Shortcut 1: Explore Buckets -->
        <article class="modern-provider-card landing-shortcut-card">
          <div class="card-top-row">
            <span class="provider-type-badge">explore</span>
          </div>
          <div class="card-main-info">
            <div class="flex-center-left gap-10">
              <FolderOpen :size="20" class="text-accent" />
              <h3 class="margin-0">Global Buckets Catalog</h3>
            </div>
            <p class="description mt-12">
              Browse, filter, search, and upload files to Ceph RGW, Garage, or other object storage containers from a single unified list.
            </p>
          </div>
          <div class="card-actions-footer">
            <NuxtLink class="btn btn-primary flex-center" to="/buckets">
              <span>Open Catalog</span>
              <ArrowRight :size="14" />
            </NuxtLink>
          </div>
        </article>

        <!-- Shortcut 2: Configure Provider -->
        <article class="modern-provider-card landing-shortcut-card">
          <div class="card-top-row">
            <span class="provider-type-badge">setup</span>
          </div>
          <div class="card-main-info">
            <div class="flex-center-left gap-10">
              <Server :size="20" class="text-accent" />
              <h3 class="margin-0">Storage Providers</h3>
            </div>
            <p class="description mt-12">
              Monitor provider latency, list registered connections, and explore metadata indexes for Ceph, Garage, and other endpoints.
            </p>
          </div>
          <div class="card-actions-footer">
            <NuxtLink class="btn btn-secondary flex-center" to="/providers">
              <span>View Providers</span>
              <ArrowRight :size="14" />
            </NuxtLink>
          </div>
        </article>

        <!-- Shortcut 3: App Settings -->
        <article class="modern-provider-card landing-shortcut-card">
          <div class="card-top-row">
            <span class="provider-type-badge">settings</span>
          </div>
          <div class="card-main-info">
            <div class="flex-center-left gap-10">
              <Settings :size="20" class="text-accent" />
              <h3 class="margin-0">App Settings</h3>
            </div>
            <p class="description mt-12">
              Configure local environment variables, databases, and metadata auto-sync intervals for active buckets.
            </p>
          </div>
          <div class="card-actions-footer">
            <NuxtLink class="btn btn-secondary flex-center" to="/settings">
              <span>Open Settings</span>
              <ArrowRight :size="14" />
            </NuxtLink>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.landing-shortcut-card {
  border-top: 3px solid var(--border-soft);
}

.landing-shortcut-card:hover {
  border-top-color: var(--accent);
}

.section-title-large {
  font-size: 26px;
  font-weight: 800;
  margin: 0 0 6px 0;
  letter-spacing: -0.5px;
}

.section-block-header {
  margin-bottom: 24px;
}

.flex-center-left {
  display: flex;
  align-items: center;
}

.gap-10 {
  gap: 10px;
}

.margin-0 {
  margin: 0 !important;
}

.mt-12 {
  margin-top: 12px;
}
</style>
