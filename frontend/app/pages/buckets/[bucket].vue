<script setup lang="ts">
import type {
  BucketBrowserItem,
  BucketDetails,
  BucketObjectListing,
  BucketSummary,
  ProviderInfo,
} from "../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../composables/useObjectLensApi";

const route = useRoute();
const router = useRouter();
const api = useObjectLensApi();

const bucket = computed(() => String(route.params.bucket || ""));
const provider = ref<ProviderInfo | null>(null);
const details = ref<BucketDetails | null>(null);
const summary = ref<BucketSummary | null>(null);
const listing = ref<BucketObjectListing | null>(null);
const search = ref("");
const pageSize = ref(50);
const offset = ref(0);
const loading = ref(true);
const loadingObjects = ref(false);
const scanning = ref(false);
const error = ref("");
const notice = ref("");

const currentPrefix = computed(() => String(route.query.prefix || ""));
const items = computed(() => listing.value?.items || []);
const isSearchMode = computed(() => Boolean(search.value.trim()));
const objectRange = computed(() => {
  const total = listing.value?.total_objects || 0;
  if (!total) return "0 objects";
  const objectCount = items.value.filter((item) => item.type === "object").length;
  const start = (listing.value?.offset || 0) + 1;
  const end = (listing.value?.offset || 0) + objectCount;
  return `${start}-${end} of ${total}`;
});
const breadcrumbs = computed(() => {
  const parts = currentPrefix.value.split("/").filter(Boolean);
  const crumbs = [
    { label: "Buckets", to: "/" },
    { label: bucket.value, to: `/buckets/${encodeURIComponent(bucket.value)}` },
  ];
  let prefix = "";
  for (const part of parts) {
    prefix += `${part}/`;
    crumbs.push({
      label: part,
      to: `/buckets/${encodeURIComponent(bucket.value)}?prefix=${encodeURIComponent(prefix)}`,
    });
  }
  return crumbs;
});

function iconFor(item: BucketBrowserItem) {
  const icons = {
    folder: "📁",
    json: "🧾",
    csv: "📊",
    parquet: "🧱",
    image: "🖼️",
    file: "📄",
  };
  return icons[item.icon] || icons.file;
}

function itemTypeLabel(item: BucketBrowserItem) {
  if (item.type === "prefix") return "Prefix";
  const labels = {
    folder: "Prefix",
    json: "JSON",
    csv: "CSV",
    parquet: "Parquet",
    image: "Image",
    file: "File",
  };
  return labels[item.icon] || "File";
}

function formatBytes(value?: number | null) {
  if (value === null || value === undefined) return "—";
  if (value === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value?: string | null) {
  if (!value) return "—";
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

async function openPrefix(prefix: string) {
  offset.value = 0;
  await router.push({
    path: `/buckets/${encodeURIComponent(bucket.value)}`,
    query: prefix ? { prefix } : {},
  });
}

function nextPage() {
  const next = listing.value?.pagination.next_offset;
  if (next === null || next === undefined) return;
  offset.value = next;
  void loadObjects();
}

function previousPage() {
  const previous = listing.value?.pagination.previous_offset;
  if (previous === null || previous === undefined) return;
  offset.value = previous;
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

async function downloadObject(item: BucketBrowserItem) {
  if (!item.key) return;
  try {
    const response = await api.presignDownload(bucket.value, item.key);
    window.open(response.url, "_blank", "noopener,noreferrer");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to create download URL.";
  }
}

watch(
  () => route.query.prefix,
  () => {
    offset.value = 0;
    void loadObjects();
  },
);

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
    <nav class="breadcrumb real-breadcrumb" aria-label="Bucket path">
      <NuxtLink v-for="(crumb, index) in breadcrumbs" :key="crumb.to" :to="crumb.to">
        {{ crumb.label }}<span v-if="index < breadcrumbs.length - 1">›</span>
      </NuxtLink>
    </nav>

    <section class="topbar compact-topbar">
      <div>
        <h1>{{ bucket }}</h1>
        <p>Browsing automatically indexes the current prefix. Use deep scan to index more of the bucket.</p>
      </div>
      <button class="primary" :disabled="scanning" @click="scanBucket">
        <span :class="{ spin: scanning }">↻</span>
        {{ scanning ? "Scanning" : "Deep scan bucket" }}
      </button>
    </section>

    <div v-if="error" class="alert error">{{ error }}</div>
    <div v-if="notice" class="alert success">{{ notice }}</div>

    <section class="status-grid compact-grid">
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
        <p>Current prefix loads automatically.</p>
      </article>
    </section>

    <section class="toolbar">
      <label>
        Search inside bucket
        <input v-model="search" placeholder="summary.json, metrics, parquet" />
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

    <section class="table-wrap browser-table">
      <div class="table-header">
        <div>
          <h2>Browser</h2>
          <p v-if="isSearchMode">Search results for: {{ search }}</p>
          <p v-else>Browsing: {{ currentPrefix || "bucket root" }}</p>
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
            <th>Name</th>
            <th>Type</th>
            <th>Size</th>
            <th>Last modified</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading || loadingObjects">
            <td colspan="5" class="empty">Loading current prefix...</td>
          </tr>
          <template v-else>
            <tr
              v-for="item in items"
              :key="item.prefix || item.key || item.name"
              :class="{ 'prefix-row': item.type === 'prefix' }"
            >
              <td class="name-cell">
                <span class="item-icon">{{ iconFor(item) }}</span>
                <button v-if="item.type === 'prefix' && item.prefix" class="row-link" @click="openPrefix(item.prefix)">
                  {{ item.name }}
                </button>
                <span v-else>{{ item.name }}</span>
              </td>
              <td>{{ itemTypeLabel(item) }}</td>
              <td>{{ item.type === "prefix" ? "—" : formatBytes(item.size) }}</td>
              <td>{{ item.type === "prefix" ? "—" : formatDate(item.last_modified) }}</td>
              <td class="actions multi-actions">
                <button
                  v-if="item.type === 'prefix' && item.prefix"
                  class="text-button"
                  @click="openPrefix(item.prefix)"
                >
                  Open
                </button>
                <template v-else>
                  <NuxtLink
                    v-if="item.key"
                    class="text-button"
                    :to="`/objects/preview?bucket=${encodeURIComponent(bucket)}&key=${encodeURIComponent(item.key)}`"
                  >
                    Preview
                  </NuxtLink>
                  <button class="text-button" @click="downloadObject(item)">Download</button>
                </template>
              </td>
            </tr>
          </template>
          <tr v-if="!loading && !loadingObjects && items.length === 0">
            <td colspan="5" class="empty">No folders or objects found in this prefix.</td>
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
