<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import type {
  BucketDetails,
  BucketSettings,
  ProviderConnection,
} from "../../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../../composables/useObjectLensApi";
import {
  FolderOpen,
  Database,
  Calendar,
  Shield,
  HardDrive,
  FileText,
  ChevronRight,
  Info,
  Sliders,
  Copy,
  Check,
  Clock,
  ArrowRight,
  Activity,
  File,
  FileCode,
  FileSpreadsheet,
  FileImage,
  Server
} from "@lucide/vue";

const route = useRoute();
const api = useObjectLensApi();

const providerId = computed(() => String(route.query.provider || ""));
const bucket = computed(() => String(route.params.bucket || ""));
const provider = ref<ProviderConnection | null>(null);
const details = ref<BucketDetails | null>(null);
const settings = ref<BucketSettings | null>(null);
const loading = ref(true);
const error = ref("");

const activeTab = ref<"insights" | "config" | "overview">("overview");

// Clipboard copy state
const copied = ref(false);
function copyS3Uri() {
  const uri = `s3://${bucket.value}`;
  navigator.clipboard.writeText(uri);
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 2000);
}

function formatBytes(value?: number | null) {
  if (value === null || value === undefined) return "0 B";
  if (value === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value?: string | null) {
  if (!value) return "unknown";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

function getIconForFile(key: string) {
  const ext = key.split(".").pop()?.toLowerCase() || "";
  if (["png", "jpg", "jpeg", "gif", "svg", "webp"].includes(ext)) return FileImage;
  if (["json", "yaml", "yml", "xml", "csv", "tsv"].includes(ext)) return FileSpreadsheet;
  if (["js", "ts", "py", "go", "sh", "rs", "html", "css"].includes(ext)) return FileCode;
  if (["txt", "md", "log"].includes(ext)) return FileText;
  return File;
}

function getIconClass(key: string) {
  const ext = key.split(".").pop()?.toLowerCase() || "";
  if (["png", "jpg", "jpeg", "gif", "svg", "webp"].includes(ext)) return "ext-image";
  if (["json", "yaml", "yml", "xml", "csv", "tsv"].includes(ext)) return "ext-config";
  if (["js", "ts", "py", "go", "sh", "rs"].includes(ext)) return "ext-code";
  if (["txt", "md", "log"].includes(ext)) return "ext-doc";
  return "ext-default";
}

onMounted(async () => {
  try {
    provider.value = await api.providerConnection(providerId.value);
    details.value = await api.providerBucketDetails(providerId.value, bucket.value);
    settings.value = await api.providerBucketSettings(providerId.value, bucket.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load bucket details.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="bucket-details-page-new">
    <!-- Breadcrumb Path -->
    <nav class="breadcrumb real-breadcrumb" aria-label="Bucket details path">
      <NuxtLink to="/">Dashboard</NuxtLink>
      <span class="breadcrumb-separator">/</span>
      <NuxtLink :to="`/providers/${encodeURIComponent(providerId)}`">
        {{ provider?.name || providerId }}
      </NuxtLink>
      <span class="breadcrumb-separator">/</span>
      <NuxtLink :to="`/buckets/${encodeURIComponent(bucket)}?provider=${encodeURIComponent(providerId)}`">
        {{ bucket }}
      </NuxtLink>
      <span class="breadcrumb-separator">/</span>
      <span class="current">Details</span>
    </nav>

    <!-- Header Section -->
    <header class="page-title-section bucket-details-header">
      <div class="header-text-block">
        <div class="title-with-icon-row flex-wrap gap-10">
          <FolderOpen :size="24" class="text-accent flex-shrink-0" />
          <h1>{{ bucket }}</h1>
          <span class="provider-type-badge">{{ provider?.type || "s3" }}</span>
          <span class="provider-status-badge healthy">
            <span class="status-dot-indicator" />
            <span>Online</span>
          </span>
        </div>
        <p class="subtitle mt-4">
          Detailed metrics, index state, and S3 safe configuration for this storage bucket.
        </p>
      </div>
      <div class="header-actions">
        <NuxtLink
          class="btn btn-primary flex-center gap-6"
          :to="`/buckets/${encodeURIComponent(bucket)}?provider=${encodeURIComponent(providerId)}`"
        >
          <FolderOpen :size="14" />
          <span>Open Browser</span>
        </NuxtLink>
      </div>
    </header>

    <!-- Loading & Error States -->
    <div v-if="loading" class="dashboard-skeleton-loader mt-24">
      <div class="skeleton-card" style="height: 120px;" v-for="i in 3" :key="i" />
    </div>
    
    <div v-else-if="error" class="error-panel mt-24">
      <div class="error-panel-icon">
        <Sliders :size="32" class="text-danger" />
      </div>
      <div class="error-panel-text">
        <h3>Unable to Retrieve Bucket Details</h3>
        <p>The backend was unable to list configuration or stats details for this bucket.</p>
        <code class="error-log">{{ error }}</code>
      </div>
    </div>

    <!-- Active Details Body -->
    <template v-else>
      <!-- S3 URI Copy Block -->
      <section class="s3-uri-copy-banner mb-24">
        <div class="banner-left">
          <span class="meta-label">S3 URI:</span>
          <code class="font-mono">s3://{{ bucket }}</code>
        </div>
        <button class="btn btn-secondary flex-center gap-6" @click="copyS3Uri" type="button">
          <component :is="copied ? Check : Copy" :size="13" :class="{ 'text-success': copied }" />
          <span>{{ copied ? 'Copied!' : 'Copy URI' }}</span>
        </button>
      </section>

      <!-- Grid of Modern Metrics Cards -->
      <section class="metrics-card-grid" aria-label="Bucket properties summary">
        <!-- Metric 1: Total Objects -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Indexed Objects</span>
            <div class="metric-avatar-icon tint-accent">
              <Database :size="15" class="text-accent" />
            </div>
          </div>
          <div class="metric-content">
            <strong>{{ details?.indexed_object_count ?? 0 }}</strong>
            <span class="metric-trend">records</span>
          </div>
          <p class="metric-caption">Metadata cached in SQLite catalog.</p>
        </article>

        <!-- Metric 2: Total Size -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Catalog Storage Size</span>
            <div class="metric-avatar-icon tint-success">
              <HardDrive :size="15" class="text-success" />
            </div>
          </div>
          <div class="metric-content">
            <strong>{{ formatBytes(details?.indexed_total_size) }}</strong>
            <span class="metric-trend success">Indexed</span>
          </div>
          <p class="metric-caption">Aggregate storage space calculated.</p>
        </article>

        <!-- Metric 3: Index Sync State -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Last Catalog Scan</span>
            <div class="metric-avatar-icon tint-warning">
              <Calendar :size="15" class="text-warning" />
            </div>
          </div>
          <div class="metric-content text-ellipsis">
            <strong style="font-size: 16px; margin: 10px 0 16px;">{{ formatDate(details?.last_indexed_at) }}</strong>
          </div>
          <p class="metric-caption text-ellipsis">Created: {{ formatDate(details?.creation_date) }}</p>
        </article>
      </section>

      <!-- Tab Selectors -->
      <section class="details-section-wrapper mt-32">
        <!-- Insights & Lists Grid -->
        <div class="details-insights-container">
          <!-- Recent Objects List -->
          <article class="dashboard-content-block insight-column-card">
            <div class="block-header border-bottom pb-12 mb-16">
              <div class="flex-center-left gap-8">
                <Clock :size="16" class="text-accent" />
                <h3 class="margin-0">Recent Changes</h3>
              </div>
            </div>
            
            <ul v-if="details?.recent_objects?.length" class="insights-visual-list">
              <li v-for="object in details.recent_objects" :key="object.key" class="visual-list-item">
                <div class="item-visual-avatar">
                  <component :is="getIconForFile(object.key)" :size="14" :class="getIconClass(object.key)" />
                </div>
                <div class="item-info">
                  <span class="item-name font-mono" :title="object.key">{{ object.key.split('/').pop() }}</span>
                  <span class="item-meta">{{ formatDate(object.last_modified) }}</span>
                </div>
                <NuxtLink
                  :to="`/buckets/${encodeURIComponent(bucket)}?provider=${encodeURIComponent(providerId)}&prefix=${encodeURIComponent(object.key.substring(0, object.key.lastIndexOf('/') + 1))}`"
                  class="btn-arrow-link"
                  title="Locate file"
                >
                  <ArrowRight :size="12" />
                </NuxtLink>
              </li>
            </ul>
            <div v-else class="empty-list-state">
              <Info :size="24" class="muted" />
              <p>No recent files indexed.</p>
            </div>
          </article>

          <!-- Largest Objects List -->
          <article class="dashboard-content-block insight-column-card">
            <div class="block-header border-bottom pb-12 mb-16">
              <div class="flex-center-left gap-8">
                <HardDrive :size="16" class="text-success" />
                <h3 class="margin-0">Largest Files</h3>
              </div>
            </div>

            <ul v-if="details?.largest_objects?.length" class="insights-visual-list">
              <li v-for="object in details.largest_objects" :key="object.key" class="visual-list-item">
                <div class="item-visual-avatar">
                  <component :is="getIconForFile(object.key)" :size="14" :class="getIconClass(object.key)" />
                </div>
                <div class="item-info">
                  <span class="item-name font-mono" :title="object.key">{{ object.key.split('/').pop() }}</span>
                  <span class="item-meta">Size: {{ formatBytes(object.size) }}</span>
                </div>
                <NuxtLink
                  :to="`/buckets/${encodeURIComponent(bucket)}?provider=${encodeURIComponent(providerId)}&prefix=${encodeURIComponent(object.key.substring(0, object.key.lastIndexOf('/') + 1))}`"
                  class="btn-arrow-link"
                  title="Locate file"
                >
                  <ArrowRight :size="12" />
                </NuxtLink>
              </li>
            </ul>
            <div v-else class="empty-list-state">
              <Info :size="24" class="muted" />
              <p>No large files mapped.</p>
            </div>
          </article>

          <!-- Top Prefixes -->
          <article class="dashboard-content-block insight-column-card">
            <div class="block-header border-bottom pb-12 mb-16">
              <div class="flex-center-left gap-8">
                <FolderOpen :size="16" class="text-warning" />
                <h3 class="margin-0">Subdirectories</h3>
              </div>
            </div>

            <ul v-if="details?.top_prefixes?.length" class="insights-visual-list">
              <li v-for="item in details.top_prefixes" :key="item.prefix" class="visual-list-item">
                <div class="item-visual-avatar tint-warning-soft">
                  <FolderOpen :size="14" class="text-warning" />
                </div>
                <div class="item-info">
                  <span class="item-name font-mono" :title="item.prefix">{{ item.prefix }}</span>
                  <span class="item-meta">{{ item.object_count }} objects · {{ formatBytes(item.total_size) }}</span>
                </div>
                <NuxtLink
                  :to="`/buckets/${encodeURIComponent(bucket)}?provider=${encodeURIComponent(providerId)}&prefix=${encodeURIComponent(item.prefix)}`"
                  class="btn-arrow-link"
                  title="Open folder"
                >
                  <ArrowRight :size="12" />
                </NuxtLink>
              </li>
            </ul>
            <div v-else class="empty-list-state">
              <Info :size="24" class="muted" />
              <p>No nested directory indexes.</p>
            </div>
          </article>
        </div>

        <!-- S3 Configurations Section -->
        <article class="dashboard-content-block setting-panel-card mt-32">
          <div class="block-header border-bottom pb-12 mb-16">
            <div class="flex-center-left gap-10">
              <Shield :size="18" class="text-accent" />
              <h2 class="margin-0">S3 Safe Settings Manifest</h2>
            </div>
          </div>

          <div class="manifest-columns-grid">
            <div class="manifest-column">
              <h4>Properties</h4>
              <dl class="settings-details-list">
                <div class="settings-field-row">
                  <dt>Versioning Status</dt>
                  <dd>
                    <span class="status-indicator-badge" :class="settings?.versioning === 'Enabled' ? 'active' : 'inactive'">
                      {{ settings?.versioning || "Unknown" }}
                    </span>
                  </dd>
                </div>
                <div class="settings-field-row">
                  <dt>Lifecycle Configuration</dt>
                  <dd>
                    <span class="status-indicator-badge inactive">
                      {{ settings?.lifecycle || "Disabled/Unknown" }}
                    </span>
                  </dd>
                </div>
              </dl>
            </div>

            <div class="manifest-column">
              <h4>Security Policy</h4>
              <dl class="settings-details-list">
                <div class="settings-field-row">
                  <dt>Access Control List (ACL)</dt>
                  <dd><code>Private / Not Exposed</code></dd>
                </div>
                <div class="settings-field-row">
                  <dt>Bucket Policy Type</dt>
                  <dd><code>{{ settings?.policy || "Inherited / Default" }}</code></dd>
                </div>
              </dl>
            </div>
          </div>
        </article>
      </section>
    </template>
  </div>
</template>

<style scoped>
.bucket-details-page-new {
  display: flex;
  flex-direction: column;
  padding: 0 0 40px 0;
}

.bucket-details-header {
  margin-bottom: 24px;
}

.s3-uri-copy-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--panel-tint, #f8fafc);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 18px;
  gap: 12px;
}

[data-theme="dark"] .s3-uri-copy-banner {
  background: rgba(30, 41, 59, 0.5);
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.banner-left code {
  font-size: 13px;
  color: var(--accent);
  background: rgba(23, 107, 135, 0.06);
  padding: 4px 8px;
  border-radius: 4px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.metric-avatar-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px;
}

.tint-accent {
  background: rgba(23, 107, 135, 0.08);
}

.tint-success {
  background: rgba(34, 197, 94, 0.08);
}

.tint-warning {
  background: rgba(245, 158, 11, 0.08);
}

.details-insights-container {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

@media (max-width: 1024px) {
  .details-insights-container {
    grid-template-columns: 1fr;
  }
}

.insight-column-card {
  display: flex;
  flex-direction: column;
  min-height: 280px;
}

.insights-visual-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.visual-list-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel);
  gap: 12px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.visual-list-item:hover {
  border-color: var(--accent);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.item-visual-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  background: rgba(23, 107, 135, 0.05);
  flex-shrink: 0;
}

.tint-warning-soft {
  background: rgba(245, 158, 11, 0.05) !important;
}

.item-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.item-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.item-meta {
  font-size: 11px;
  color: var(--text-muted, #64748b);
  margin-top: 2px;
}

.btn-arrow-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--text-muted);
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.btn-arrow-link:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: rgba(23, 107, 135, 0.05);
}

.empty-list-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 32px 16px;
  text-align: center;
  gap: 8px;
  color: var(--text-muted);
}

.empty-list-state p {
  font-size: 13px;
  margin: 0;
}

.manifest-columns-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

@media (max-width: 768px) {
  .manifest-columns-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}

.manifest-column h4 {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin: 0 0 16px 0;
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
}

.status-indicator-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  text-transform: uppercase;
}

.status-indicator-badge.active {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.status-indicator-badge.inactive {
  background: var(--border);
  color: var(--text-muted);
}
</style>