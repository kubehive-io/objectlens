<script setup lang="ts">
import type { BucketDetails, BucketSummary, ObjectMetadata, ProviderInfo } from "../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../composables/useObjectLensApi";

const route = useRoute();
const api = useObjectLensApi();

const bucket = computed(() => String(route.params.bucket || ""));
const provider = ref<ProviderInfo | null>(null);
const details = ref<BucketDetails | null>(null);
const summary = ref<BucketSummary | null>(null);
const objects = ref<ObjectMetadata[]>([]);
const prefix = ref("");
const search = ref("");
const loading = ref(true);
const loadingObjects = ref(false);
const scanning = ref(false);
const error = ref("");
const notice = ref("");

function formatBytes(value?: number | null) {
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

async function loadObjects() {
  loadingObjects.value = true;
  error.value = "";
  try {
    const response = await api.listBucketObjects(bucket.value, {
      prefix: prefix.value.trim() || undefined,
      search: search.value.trim() || undefined,
      limit: 200,
    });
    objects.value = response.objects;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load indexed objects.";
  } finally {
    loadingObjects.value = false;
  }
}

async function refreshBucket() {
  loading.value = true;
  error.value = "";
  try {
    provider.value = await api.provider();
    details.value = await api.bucketDetails(bucket.value);
    summary.value = await api.bucketSummary(bucket.value);
    await loadObjects();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Bucket access denied or backend unavailable.";
  } finally {
    loading.value = false;
  }
}

async function scanBucket() {
  scanning.value = true;
  error.value = "";
  notice.value = "";
  try {
    const response = await api.scanBucket(bucket.value);
    notice.value = `Scan complete: ${response.scanned} objects scanned, ${response.indexed} indexed.`;
    await refreshBucket();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Scan failed.";
  } finally {
    scanning.value = false;
  }
}

async function downloadObject(object: ObjectMetadata) {
  try {
    const response = await api.presignDownload(object.bucket, object.key);
    window.open(response.url, "_blank", "noopener,noreferrer");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to create download URL.";
  }
}

watch([prefix, search], () => {
  void loadObjects();
});

onMounted(() => {
  void refreshBucket();
});
</script>

<template>
  <main class="app-shell">
    <section class="topbar">
      <div>
        <NuxtLink class="back-link" to="/">Visible buckets</NuxtLink>
        <h1>{{ bucket }}</h1>
        <p>Scan bucket to build local search index.</p>
      </div>
      <button class="primary" :disabled="scanning" @click="scanBucket">
        <span :class="{ spin: scanning }">↻</span>
        {{ scanning ? "Scanning" : "Scan bucket" }}
      </button>
    </section>

    <div v-if="error" class="alert error">{{ error }}</div>
    <div v-if="notice" class="alert success">{{ notice }}</div>

    <section class="status-grid">
      <article class="status-card">
        <span class="label">Provider</span>
        <strong>{{ provider?.display_name || details?.provider || "Ceph RGW" }}</strong>
        <p>{{ provider?.endpoint_url || "Endpoint not configured" }}</p>
      </article>
      <article class="status-card">
        <span class="label">Indexed objects</span>
        <strong>{{ details?.indexed_object_count ?? 0 }}</strong>
        <p>{{ formatBytes(details?.indexed_total_size) }} indexed</p>
      </article>
      <article class="status-card">
        <span class="label">Last indexed</span>
        <strong>{{ formatDate(details?.last_indexed_at) }}</strong>
        <p>Preview reads only a limited amount of the object.</p>
      </article>
    </section>

    <section class="toolbar">
      <label>
        Prefix
        <input v-model="prefix" placeholder="logs/2026/" />
      </label>
      <label>
        Search inside bucket
        <input v-model="search" placeholder="snapshot, metrics, .json" />
      </label>
    </section>

    <section class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Key</th>
            <th>Size</th>
            <th>Last modified</th>
            <th>Content type</th>
            <th>Storage class</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading || loadingObjects">
            <td colspan="6" class="empty">Loading indexed objects...</td>
          </tr>
          <template v-else>
            <tr v-for="object in objects" :key="`${object.provider}/${object.bucket}/${object.key}`">
              <td class="key-cell">{{ object.key }}</td>
              <td>{{ formatBytes(object.size) }}</td>
              <td>{{ formatDate(object.last_modified) }}</td>
              <td>{{ object.content_type || "-" }}</td>
              <td>{{ object.storage_class || "-" }}</td>
              <td class="actions multi-actions">
                <NuxtLink
                  class="icon-link"
                  title="Preview object"
                  :to="`/objects/preview?bucket=${encodeURIComponent(object.bucket)}&key=${encodeURIComponent(object.key)}`"
                >
                  ◱
                </NuxtLink>
                <button class="icon-button" title="Download object" @click="downloadObject(object)">↓</button>
              </td>
            </tr>
          </template>
          <tr v-if="!loading && !loadingObjects && objects.length === 0">
            <td colspan="6" class="empty">
              No objects indexed yet. Scan bucket to build local search index.
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="insight-grid">
      <article class="status-card">
        <span class="label">Recent objects</span>
        <ul class="object-list">
          <li v-for="object in summary?.recent_objects || []" :key="`recent-${object.key}`">
            <span>{{ object.key }}</span>
            <small>{{ formatDate(object.last_modified) }}</small>
          </li>
          <li v-if="!summary?.recent_objects?.length" class="muted">No recent indexed objects.</li>
        </ul>
      </article>
      <article class="status-card">
        <span class="label">Largest objects</span>
        <ul class="object-list">
          <li v-for="object in summary?.largest_objects || []" :key="`large-${object.key}`">
            <span>{{ object.key }}</span>
            <small>{{ formatBytes(object.size) }}</small>
          </li>
          <li v-if="!summary?.largest_objects?.length" class="muted">No indexed object sizes yet.</li>
        </ul>
      </article>
      <article class="status-card">
        <span class="label">Top prefixes</span>
        <ul class="object-list">
          <li v-for="item in summary?.top_prefixes || []" :key="item.prefix">
            <span>{{ item.prefix }}</span>
            <small>{{ item.object_count }} objects · {{ formatBytes(item.total_size) }}</small>
          </li>
          <li v-if="!summary?.top_prefixes?.length" class="muted">No prefixes indexed yet.</li>
        </ul>
      </article>
    </section>
  </main>
</template>
