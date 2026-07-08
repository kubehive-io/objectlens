<script setup lang="ts">
import type { Bucket, ObjectMetadata, ProviderInfo } from "../composables/useObjectLensApi";
import { useObjectLensApi } from "../composables/useObjectLensApi";

const api = useObjectLensApi();

const buckets = ref<Bucket[]>([]);
const provider = ref<ProviderInfo | null>(null);
const selectedBucket = ref("");
const search = ref("");
const objects = ref<ObjectMetadata[]>([]);
const loadingBuckets = ref(true);
const loadingObjects = ref(false);
const scanning = ref(false);
const backendHealthy = ref(false);
const error = ref("");
const notice = ref("");

const hasBackendError = computed(() => !backendHealthy.value && Boolean(error.value));

function formatBytes(value: number) {
  if (value === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

async function refreshHealth() {
  const response = await api.health();
  backendHealthy.value = response.status === "ok";
}

async function loadProvider() {
  provider.value = await api.provider();
}

async function loadBuckets() {
  loadingBuckets.value = true;
  try {
    const response = await api.listBuckets();
    buckets.value = response.buckets;
    if (!selectedBucket.value) {
      selectedBucket.value = provider.value?.default_bucket || response.buckets[0]?.name || "";
    }
  } finally {
    loadingBuckets.value = false;
  }
}

async function loadObjects() {
  if (!selectedBucket.value) {
    objects.value = [];
    return;
  }
  loadingObjects.value = true;
  error.value = "";
  notice.value = "";
  try {
    const response = await api.listObjects({
      bucket: selectedBucket.value,
      search: search.value.trim() || undefined,
      limit: 200,
    });
    objects.value = response.objects;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load indexed objects";
  } finally {
    loadingObjects.value = false;
  }
}

async function scanBucket() {
  if (!selectedBucket.value) return;
  scanning.value = true;
  error.value = "";
  notice.value = "";
  try {
    const response = await api.scanBucket(selectedBucket.value);
    notice.value = `Scan complete: ${response.scanned} objects scanned, ${response.indexed} indexed.`;
    await loadObjects();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Scan failed";
  } finally {
    scanning.value = false;
  }
}

async function downloadObject(key: string) {
  if (!selectedBucket.value) return;
  error.value = "";
  try {
    const response = await api.presignDownload(selectedBucket.value, key);
    window.open(response.url, "_blank", "noopener,noreferrer");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to create download URL";
  }
}

watch([selectedBucket, search], () => {
  void loadObjects();
});

onMounted(async () => {
  try {
    await refreshHealth();
    await loadProvider();
    await loadBuckets();
    await loadObjects();
  } catch (err) {
    backendHealthy.value = false;
    error.value =
      err instanceof Error
        ? err.message
        : "ObjectLens backend is unavailable. Start it with `just backend` or `just dev`.";
  }
});
</script>

<template>
  <main class="app-shell">
    <section class="topbar">
      <div>
        <h1>ObjectLens</h1>
        <p>Fast object access for Kubernetes and Ceph</p>
      </div>
      <button class="primary" :disabled="!selectedBucket || scanning || !backendHealthy" @click="scanBucket">
        <span :class="{ spin: scanning }">↻</span>
        {{ scanning ? "Scanning" : "Scan bucket" }}
      </button>
    </section>

    <section class="status-grid">
      <article class="status-card">
        <span class="label">Provider</span>
        <strong>{{ provider?.display_name || "Ceph RGW" }}</strong>
        <dl>
          <div>
            <dt>Endpoint URL</dt>
            <dd>{{ provider?.endpoint_url || "Not configured" }}</dd>
          </div>
          <div>
            <dt>Default bucket</dt>
            <dd>{{ provider?.default_bucket || "Any accessible bucket" }}</dd>
          </div>
        </dl>
      </article>

      <article class="status-card">
        <span class="label">Backend health</span>
        <strong :class="backendHealthy ? 'healthy' : 'unhealthy'">
          {{ backendHealthy ? "Online" : "Unavailable" }}
        </strong>
        <p>
          {{ backendHealthy ? "FastAPI is reachable on the configured API URL." : "Start the backend with just dev." }}
        </p>
      </article>
    </section>

    <section v-if="hasBackendError" class="backend-empty">
      <h2>ObjectLens backend is not reachable</h2>
      <p>
        The dashboard is ready, but it cannot reach the API. Start the backend with
        <code>just backend</code> or run the full stack with <code>just dev</code>.
      </p>
      <p class="error-text">{{ error }}</p>
    </section>

    <template v-else>
      <section class="toolbar">
        <label>
          Bucket
          <select v-model="selectedBucket" :disabled="loadingBuckets || !backendHealthy">
            <option value="" disabled>Select a bucket</option>
            <option v-for="bucket in buckets" :key="bucket.name" :value="bucket.name">
              {{ bucket.name }}
            </option>
          </select>
        </label>

        <label>
          Search objects
          <input
            v-model="search"
            :disabled="!backendHealthy"
            placeholder="backup, logs/, snapshot.parquet"
          />
        </label>
      </section>

      <div v-if="error" class="alert error">{{ error }}</div>
      <div v-if="notice" class="alert success">{{ notice }}</div>

      <section class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Object key</th>
              <th>Size</th>
              <th>Last modified</th>
              <th>Storage class</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingObjects">
              <td colspan="5" class="empty">Loading indexed objects...</td>
            </tr>
            <template v-else>
              <tr v-for="object in objects" :key="`${object.provider}/${object.bucket}/${object.key}`">
                <td class="key-cell">{{ object.key }}</td>
                <td>{{ formatBytes(object.size) }}</td>
                <td>{{ formatDate(object.last_modified) }}</td>
                <td>{{ object.storage_class || "-" }}</td>
                <td class="actions">
                  <button class="icon-button" title="Download object" @click="downloadObject(object.key)">
                    ↓
                  </button>
                </td>
              </tr>
            </template>
            <tr v-if="!loadingObjects && objects.length === 0">
              <td colspan="5" class="empty">
                No indexed objects found. Scan a Ceph RGW bucket to populate the local metadata index.
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </main>
</template>
