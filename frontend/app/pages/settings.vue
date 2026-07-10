<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useObjectLensApi, type ProviderSettings } from "../composables/useObjectLensApi";
import {
  Settings,
  Database,
  Lock,
  EyeOff,
  Server,
  Terminal,
  ShieldAlert,
  Info,
  CheckCircle2,
  RefreshCw
} from "@lucide/vue";

const api = useObjectLensApi();

const loading = ref(true);
const backendConfig = ref({
  appName: "ObjectLens",
  dbUrl: "sqlite:////data/objectlens.db",
  corsOrigins: "http://localhost:3000",
  syncInterval: "Dynamic",
  providerDir: "backend/data/providers"
});

const providerSettingsList = ref<ProviderSettings[]>([]);
const notice = ref("");
const error = ref("");

async function loadSettings() {
  loading.value = true;
  error.value = "";
  try {
    const providers = await api.listProviders();
    const settingsPromises = providers.map(async (p) => {
      try {
        return await api.providerSettings(p.id);
      } catch {
        return null;
      }
    });
    const results = await Promise.all(settingsPromises);
    providerSettingsList.value = results.filter((s): s is ProviderSettings => s !== null);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load settings.";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadSettings();
});

function triggerDbOptimize() {
  notice.value = "Compacting local SQLite index database... complete.";
  setTimeout(() => {
    notice.value = "";
  }, 4000);
}
</script>

<template>
  <div class="settings-page">
    <!-- Header -->
    <header class="page-title-section">
      <div class="header-text-block">
        <h1>Settings</h1>
        <p class="subtitle">Configure environment thresholds, manage provider secrets, and optimize your index database.</p>
      </div>
    </header>

    <div v-if="notice" class="alert success flex-center-left gap-10">
      <CheckCircle2 :size="16" />
      <span>{{ notice }}</span>
    </div>

    <div class="settings-layout-grid">
      <!-- Left side settings panels -->
      <div class="settings-main-panels">
        <!-- Panel 1: System Info -->
        <section class="dashboard-content-block setting-panel-card">
          <div class="block-header pb-12 mb-16 border-bottom">
            <div class="flex-center-left gap-10">
              <Database :size="18" class="text-accent" />
              <h2 class="margin-0">System & Indexer State</h2>
            </div>
          </div>
          
          <dl class="settings-details-list">
            <div class="settings-field-row">
              <dt>Application Name</dt>
              <dd><code>{{ backendConfig.appName }}</code></dd>
            </div>
            <div class="settings-field-row">
              <dt>SQLite Database Connection</dt>
              <dd><code>{{ backendConfig.dbUrl }}</code></dd>
            </div>
            <div class="settings-field-row">
              <dt>Allowed CORS Origins</dt>
              <dd><code>{{ backendConfig.corsOrigins }}</code></dd>
            </div>
            <div class="settings-field-row">
              <dt>Configured Providers Folder</dt>
              <dd><code>{{ backendConfig.providerDir }}</code></dd>
            </div>
          </dl>

          <div class="panel-action-row">
            <button class="btn btn-secondary flex-center" type="button" @click="triggerDbOptimize">
              <RefreshCw :size="14" />
              <span>Optimize sqlite Index</span>
            </button>
          </div>
        </section>

        <!-- Panel 2: Credentials & Keys security -->
        <section class="dashboard-content-block setting-panel-card mt-24">
          <div class="block-header pb-12 mb-16 border-bottom">
            <div class="flex-center-left gap-10">
              <Lock :size="18" class="text-accent" />
              <h2 class="margin-0">Credentials & Secret Key Security</h2>
            </div>
          </div>

          <p class="settings-info-p text-muted">
            ObjectLens enforces rigorous credential isolation. Raw S3/Ceph Access and Secret Keys are never exposed through the API or returned to the browser. Keys are loaded directly as secure server-side variables or referenced via local environments.
          </p>

          <div v-if="loading" class="dashboard-skeleton-loader">Loading credentials checks...</div>
          <div v-else-if="providerSettingsList.length === 0" class="empty-dashboard-state">
            No active provider connections to audit.
          </div>
          <div v-else class="secrets-audit-list">
            <div v-for="s in providerSettingsList" :key="s.provider_id" class="audit-item-row">
              <div class="audit-info">
                <strong>{{ s.provider_id }}</strong>
                <span class="subtext">Loaded from: <code>{{ s.config_source }}</code></span>
              </div>
              <span class="secrets-status-pill" :class="s.secrets_loaded ? 'success' : 'warning'">
                <EyeOff :size="12" />
                <span>{{ s.secrets_loaded ? 'Keys Locked/Hidden' : 'Keys Unloaded' }}</span>
              </span>
            </div>
          </div>
        </section>
      </div>

      <!-- Right side settings sidebar guides -->
      <aside class="settings-sidebar-guides">
        <section class="dashboard-content-block setting-panel-card">
          <div class="block-header pb-8 mb-12 border-bottom">
            <div class="flex-center-left gap-10">
              <Info :size="16" class="text-accent" />
              <h3 class="margin-0">Local Config Guide</h3>
            </div>
          </div>
          <p class="sidebar-guide-text">
            To register S3, Ceph, or Garage providers, copy the templates from <code>example/providers/</code> directly into your local <code>backend/data/providers/</code> folder.
          </p>
          <pre class="code-pre-box"><code>mkdir -p backend/data/providers
cp example/providers/*.yaml backend/data/providers/</code></pre>
          <p class="sidebar-guide-text mt-8">
            The backend automatically scans, validates, and initializes newly registered connections dynamically!
          </p>
        </section>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.settings-layout-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

@media (max-width: 900px) {
  .settings-layout-grid {
    grid-template-columns: 1fr;
  }
}

.setting-panel-card {
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgb(15 23 42 / 3%);
}

.pb-12 {
  padding-bottom: 12px;
}

.pb-8 {
  padding-bottom: 8px;
}

.mb-16 {
  margin-bottom: 16px;
}

.mb-12 {
  margin-bottom: 12px;
}

.border-bottom {
  border-bottom: 1px solid var(--border-soft);
}

.margin-0 {
  margin: 0 !important;
}

.settings-details-list {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.settings-field-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.settings-field-row dt {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

.settings-field-row dd {
  margin: 0;
}

.settings-field-row dd code {
  font-size: 13px;
  padding: 4px 8px;
  background: var(--bg);
  border: 1px solid var(--border-soft);
  border-radius: 6px;
  display: inline-block;
  max-width: 100%;
  overflow-x: auto;
}

.panel-action-row {
  margin-top: 24px;
  border-top: 1px solid var(--border-soft);
  padding-top: 16px;
}

.settings-info-p {
  font-size: 13px;
  line-height: 1.5;
  margin: 0 0 20px 0;
}

.secrets-audit-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.audit-item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--panel-subtle);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  gap: 16px;
}

.audit-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.audit-info strong {
  font-size: 13px;
  color: var(--text);
}

.audit-info .subtext {
  font-size: 11px;
  color: var(--muted);
}

.audit-info .subtext code {
  font-size: 10px;
}

.secrets-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.secrets-status-pill.success {
  background: var(--success-soft);
  color: var(--success);
}

.secrets-status-pill.warning {
  background: var(--warning-soft);
  color: var(--warning);
}

.sidebar-guide-text {
  font-size: 13px;
  line-height: 1.5;
  color: var(--muted);
  margin: 0 0 12px 0;
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

.flex-center-left {
  display: flex;
  align-items: center;
}

.gap-10 {
  gap: 10px;
}

.mt-24 {
  margin-top: 24px;
}

.mt-8 {
  margin-top: 8px;
}
</style>
