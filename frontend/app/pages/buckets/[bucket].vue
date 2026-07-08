<script setup lang="ts">
import type {
  BucketDetails,
  BucketObjectListing,
  BucketSummary,
  ObjectMetadata,
  ProviderInfo,
} from "../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../composables/useObjectLensApi";

const route = useRoute();
const api = useObjectLensApi();

const bucket = computed(() => String(route.params.bucket || ""));
const provider = ref<ProviderInfo | null>(null);
const details = ref<BucketDetails | null>(null);
const summary = ref<BucketSummary | null>(null);
const listing = ref<BucketObjectListing | null>(null);
const currentPrefix = ref("");
const search = ref("");
const pageSize = ref(50);
const offset = ref(0);
const loading = ref(true);
const loadingObjects = ref(false);
const scanning = ref(false);
const error = ref("");
const notice = ref("");

const objects = computed(() => listing.value?.objects || []);
const prefixes = computed(() => listing.value?.prefixes || []);
const isSearchMode = computed(() => Boolean(search.value.trim()));
const objectRange = computed(() => {
  const total = listing.value?.total_objects || 0;
  if (!total) return "0 objects";
  const start = (listing.value?.offset || 0) + 1;
  const end = (listing.value?.offset || 0) + objects.value.length;
  return `${start}-${end} of ${total}`;
});
const breadcrumbs = computed(() => {
  const parts = currentPrefix.value.split("/").filter(Boolean);
  const items = [{ label: "root", prefix: "" }];
  let path = "";
  for (const part of parts) {
    path += `${part}/`;
    items.push({ label: part, prefix: path });
  }
  return items;
});

function displayName(key: string) {
  if (!currentPrefix.value || isSearchMode.value) return key;
  return key.slice(currentPrefix.value.length) || key;
}

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
    listing.value = await api.listBucketObjects(bucket.value, {
      prefix: currentPrefix.value,
      search: search.value.trim() || undefined,
      limit: pageSize.value,
      offset: offset.value,
      delimiter: "/",
    });
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

function enterPrefix(prefix: string) {
  currentPrefix.value = prefix;
  offset.value = 0;
  void loadObjects();
}

function nextPage() {
  if (listing.value?.pagination.next_offset === null || listing.value?.pagination.next_offset === undefined) return;
  offset.value = listing.value.pagination.next_offset;
  void loadObjects();
}

function previousPage() {
  if (listing.value?.pagination.previous_offset === null || listing.value?.pagination.previous_offset === undefined) return;
  offset.value = listing.value.pagination.previous_offset;
  void loadObjects();
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

watch(search, () => {
  offset.value = 0;
  void loadObjects();
});

watch(pageSize, () => {
  offset.value = 0;
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
        <p>Scan bucket to build local search index before browsing large buckets.</p>
      </div>
      <button class="primary" :disabled="scanning" @click="scanBucket">
        <span :class="{ spin: scanning }">↻</span>
        {{ scanning ? "Scanning" : "Scan bucket" }}
      </button>
    </section>

    <div v-if="error" class="alert error">{{ error }}</div>
    <div v-if="notice" class="alert success">{{ notice }}</div>
    <div v-if="!loading && (details?.indexed_object_count ?? 0) === 0" class="alert warning">
      Scan this bucket to build a local index before browsing.
    </div>

    <section class="status-grid">
      <article class="status-card">
        <span class="label">Provider</span>
        <strong>{{ provider?.display_name || summary?.provider || details?.provider || "Ceph RGW" }}</strong>
        <p>{{ provider?.endpoint_url || "Endpoint not configured" }}</p>
      </article>
      <article class="status-card">
        <span class="label">Indexed objects</span>
        <strong>{{ details?.indexed_object_count ?? summary?.indexed_object_count ?? 0 }}</strong>
        <p>{{ formatBytes(details?.indexed_total_size ?? summary?.indexed_total_size) }} indexed</p>
      </article>
      <article class="status-card">
        <span class="label">Last indexed</span>
        <strong>{{ formatDate(details?.last_indexed_at ?? summary?.last_indexed_at) }}</strong>
        <p>Default page size is 50 objects.</p>
      </article>
    </section>

    <nav class="breadcrumb" aria-label="Prefix breadcrumb">
      <button
        v-for="item in breadcrumbs"
        :key="item.prefix"
        class="breadcrumb-button"
        @click="enterPrefix(item.prefix)"
      >
        {{ item.label }}
      </button>
    </nav>

    <section class="toolbar">
      <label>
        Search inside bucket
        <input v-model="search" placeholder="snapshot, metrics, .json" />
      </label>
      <label>
        Page size
        <select v-model.number="pageSize">
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </label>
    </section>

    <section v-if="!isSearchMode" class="section-block">
      <div class="section-heading">
        <div>
          <h2>Folders</h2>
          <p>AWS S3-style prefixes. Nested objects appear after you enter a folder.</p>
        </div>
      </div>
      <div v-if="loadingObjects" class="empty-panel">Loading folders...</div>
      <div v-else-if="prefixes.length === 0" class="empty-panel">No folders under this prefix.</div>
      <div v-else class="prefix-grid">
        <button
          v-for="item in prefixes"
          :key="item.prefix"
          class="prefix-card"
          @click="enterPrefix(item.prefix)"
        >
          <span class="folder-icon">▣</span>
          <strong>{{ item.name }}</strong>
          <small>{{ item.object_count }} objects</small>
        </button>
      </div>
    </section>

    <section class="table-wrap">
      <div class="table-header">
        <div>
          <span class="label">{{ listing?.mode || "browse" }} mode</span>
          <p>{{ isSearchMode ? "Search results are paginated." : "Showing direct objects only for the current prefix." }}</p>
        </div>
        <div class="pagination-controls">
          <span>{{ objectRange }}</span>
          <button :disabled="!listing?.pagination.has_previous || loadingObjects" @click="previousPage">
            Previous
          </button>
          <button :disabled="!listing?.pagination.has_next || loadingObjects" @click="nextPage">
            Next
          </button>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Key/name</th>
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
              <td class="key-cell">{{ displayName(object.key) }}</td>
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
              No direct objects found for this prefix and page.
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
