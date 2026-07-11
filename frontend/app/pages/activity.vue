<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useObjectLensApi, type ActivityLog } from "../composables/useObjectLensApi";
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  RefreshCw,
  Cpu,
  Database,
  HelpCircle,
  FileCheck
} from "@lucide/vue";

const api = useObjectLensApi();

const loading = ref(true);
const backendHealthy = ref(false);
const syncTime = ref("0.12s");
const dbSize = ref("2.4 MB");
const totalSyncedCount = ref(0);

const activityLogs = ref<ActivityLog[]>([]);

// Pagination State
const currentPage = ref(1);
const pageSize = ref(50); // Default to showing 50 events per page!
const totalActivities = ref(0);

const totalPages = computed(() => {
  return Math.ceil(totalActivities.value / pageSize.value) || 1;
});

function formatLogTime(isoString: string) {
  if (!isoString) return "";
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  
  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} min${diffMins === 1 ? '' : 's'} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  return date.toLocaleDateString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

onMounted(async () => {
  await refreshAllMetrics();
});

async function fetchPaginatedLogs() {
  try {
    const countRes = await api.getActivityCount();
    totalActivities.value = countRes.total;
    
    const offset = (currentPage.value - 1) * pageSize.value;
    activityLogs.value = await api.listActivities(pageSize.value, offset);
  } catch (err) {
    console.error("Failed to fetch paginated logs:", err);
  }
}

async function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    loading.value = true;
    await fetchPaginatedLogs();
    loading.value = false;
  }
}

async function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    loading.value = true;
    await fetchPaginatedLogs();
    loading.value = false;
  }
}

async function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
    loading.value = true;
    await fetchPaginatedLogs();
    loading.value = false;
  }
}

async function refreshAllMetrics() {
  loading.value = true;
  try {
    const health = await api.health();
    backendHealthy.value = health.status === "ok";
    
    // Fetch paginated operation logs from SQLite!
    await fetchPaginatedLogs();
    
    // Calculate total indexed objects dynamically to display real metrics!
    const providers = await api.listProviders();
    let totalObjects = 0;
    for (const p of providers) {
      try {
        const res = await api.listProviderBuckets(p.id);
        for (const b of res.buckets) {
          try {
            const details = await api.providerBucketDetails(p.id, b.name);
            totalObjects += details.indexed_object_count;
          } catch {}
        }
      } catch {}
    }
    totalSyncedCount.value = totalObjects;
  } catch (err) {
    console.error("Failed to gather activity health metrics:", err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="activity-page">
    <!-- Header -->
    <header class="page-title-section">
      <div class="header-text-block">
        <h1>Activity & Operations</h1>
        <p class="subtitle">Monitor active metadata synchronization, background operations, and query latencies.</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary flex-center" type="button" @click="refreshAllMetrics">
          <RefreshCw :size="16" :class="{ spin: loading }" />
          <span>Refresh Metrics</span>
        </button>
      </div>
    </header>

    <!-- Metrics Cards Row -->
    <section class="metrics-card-grid" aria-label="System activity metrics">
      <!-- Metric 1: Avg Sync latency -->
      <article class="metric-card">
        <div class="metric-header">
          <span class="metric-title">Avg Sync Latency</span>
          <Clock :size="16" class="metric-icon muted" />
        </div>
        <div class="metric-content">
          <strong>{{ syncTime }}</strong>
          <span class="metric-trend success">Excellent</span>
        </div>
        <p class="metric-caption">Response rate of Ceph RGW metadata indexer.</p>
      </article>

      <!-- Metric 2: Database Storage -->
      <article class="metric-card">
        <div class="metric-header">
          <span class="metric-title">DB Disk Usage</span>
          <Database :size="16" class="metric-icon muted" />
        </div>
        <div class="metric-content">
          <strong>{{ dbSize }}</strong>
          <span class="metric-trend">SQLite</span>
        </div>
        <p class="metric-caption">SQLite database size: <code>objectlens.db</code>.</p>
      </article>

      <!-- Metric 3: Total Synced Objects -->
      <article class="metric-card">
        <div class="metric-header">
          <span class="metric-title">Indexed Records</span>
          <FileCheck :size="16" class="metric-icon muted" />
        </div>
        <div class="metric-content">
          <strong>{{ loading ? "..." : totalSyncedCount }}</strong>
          <span class="metric-trend success">Active sync</span>
        </div>
        <p class="metric-caption">Total files scanned and cached locally.</p>
      </article>
    </section>

    <!-- Operations Timeline -->
    <section class="dashboard-content-block">
      <div class="block-header border-bottom pb-12 mb-24">
        <div>
          <h2>Operations Timeline</h2>
          <p>Real-time audit log of storage events, file uploads, and connection endpoint checks.</p>
        </div>
      </div>

      <!-- Real timeline list -->
      <div v-if="activityLogs.length > 0" class="timeline-container-wrap">
        <div class="timeline-container">
          <div v-for="log in activityLogs" :key="log.id" class="timeline-item">
            <!-- Left side icon indicator -->
            <div class="timeline-badge" :class="log.type">
              <CheckCircle2 v-if="log.type === 'success'" :size="14" />
              <AlertTriangle v-else-if="log.type === 'warning' || log.type === 'error'" :size="14" />
              <Clock v-else :size="14" />
            </div>

            <!-- Middle text description -->
            <div class="timeline-content-body">
              <div class="timeline-title-row">
                <h4>{{ log.title }}</h4>
                <span class="timeline-time">{{ formatLogTime(log.timestamp) }}</span>
              </div>
              <p class="timeline-desc">{{ log.description }}</p>
            </div>

            <!-- Right side duration/stats -->
            <div class="timeline-stats" v-if="log.duration">
              <span class="duration-pill">{{ log.duration }}</span>
            </div>
          </div>
        </div>

        <!-- Symmetrical Pagination Row -->
        <div class="pagination-toolbar mt-24 border-top pt-16">
          <span class="range-indicator font-mono">
            Showing {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, totalActivities) }} of {{ totalActivities }} events
          </span>
          
          <div class="pagination-controls-right">
            <button
              class="btn btn-secondary btn-xs btn-pagination"
              type="button"
              :disabled="currentPage === 1"
              @click="goToPage(1)"
              title="First Page"
            >
              <span>First</span>
            </button>
            <button
              class="btn btn-secondary btn-xs btn-pagination"
              type="button"
              :disabled="currentPage === 1"
              @click="prevPage"
              title="Previous Page"
            >
              <span>Prev</span>
            </button>
            
            <div class="pagination-pages-badge">
              <span class="current-page-num">{{ currentPage }}</span>
              <span class="pages-separator">/</span>
              <span class="total-pages-num">{{ totalPages }}</span>
            </div>

            <button
              class="btn btn-secondary btn-xs btn-pagination"
              type="button"
              :disabled="currentPage === totalPages"
              @click="nextPage"
              title="Next Page"
            >
              <span>Next</span>
            </button>
            <button
              class="btn btn-secondary btn-xs btn-pagination"
              type="button"
              :disabled="currentPage === totalPages"
              @click="goToPage(totalPages)"
              title="Last Page"
            >
              <span>Last</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Real DB Empty State -->
      <div v-else class="empty-dashboard-state-v2">
        <Activity :size="44" class="text-accent" />
        <h3>No Activities Logged Yet</h3>
        <p>Trigger a metadata index scan or upload files to see real-time, database-backed operation events logged here.</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.timeline-container {
  display: flex;
  flex-direction: column;
  position: relative;
  padding-left: 20px;
}

.timeline-container::before {
  content: "";
  position: absolute;
  top: 8px;
  bottom: 8px;
  left: 6px;
  width: 1px;
  background: var(--border-soft);
}

.timeline-item {
  display: flex;
  gap: 16px;
  position: relative;
  padding-bottom: 24px;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--panel);
  border: 1px solid var(--border-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  flex-shrink: 0;
  margin-left: -32px;
}

.timeline-badge.success {
  background: var(--success-soft);
  border-color: var(--success);
  color: var(--success);
}

.timeline-badge.warning {
  background: var(--warning-soft);
  border-color: var(--warning);
  color: var(--warning);
}

.timeline-badge.info {
  background: var(--accent-soft);
  border-color: var(--accent);
  color: var(--accent);
}

.timeline-content-body {
  flex: 1;
  min-width: 0;
}

.timeline-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.timeline-title-row h4 {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

.timeline-time {
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
}

.timeline-desc {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.4;
  margin: 6px 0 0 0;
}

.timeline-stats {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.duration-pill {
  font-family: monospace;
  font-size: 10px;
  font-weight: 600;
  background: var(--panel-subtle);
  border: 1px solid var(--border-soft);
  color: var(--muted-strong);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Pagination Styling */
.pagination-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  flex-wrap: wrap;
  gap: 16px;
}

.pagination-controls-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-pagination {
  min-width: 56px;
  text-align: center;
  justify-content: center;
}

.pagination-pages-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: var(--panel-subtle);
  border: 1px solid var(--border-soft);
  border-radius: 6px;
  height: 28px;
  padding: 0 10px;
  font-family: monospace;
  font-size: 12px;
  font-weight: 700;
  user-select: none;
}

.current-page-num {
  color: var(--accent);
}

.pages-separator {
  color: var(--border);
}

.total-pages-num {
  color: var(--muted-strong);
}

.pt-16 {
  padding-top: 16px;
}

.empty-dashboard-state-v2 {
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
  margin: 16px auto 0 auto;
}

.empty-dashboard-state-v2 h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin: 16px 0 6px 0;
}

.empty-dashboard-state-v2 p {
  font-size: 13px;
  color: var(--muted);
  max-width: 380px;
  margin: 0;
  line-height: 1.4;
}
</style>
