<script setup lang="ts">
import type {
  BucketBrowserItem,
  BucketDetails,
  BucketObjectListing,
  BucketSummary,
  OperationSummary,
  ProviderConnection,
  ProviderInfo,
} from "../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../composables/useObjectLensApi";
import { useUploadQueue } from "../../composables/useUploadQueue";

const route = useRoute();
const router = useRouter();
const api = useObjectLensApi();
const uploadQueue = useUploadQueue();

const bucket = computed(() => String(route.params.bucket || ""));
const providerId = computed(() => String(route.params.providerId || route.query.provider || ""));
const provider = ref<ProviderInfo | ProviderConnection | null>(null);
const details = ref<BucketDetails | null>(null);
const summary = ref<BucketSummary | null>(null);
const listing = ref<BucketObjectListing | null>(null);
const search = ref("");
const pageSize = ref(50);
const offset = ref(0);
const loading = ref(true);
const loadingObjects = ref(false);
const scanning = ref(false);
const dragActive = ref(false);
const error = ref("");
const notice = ref("");
const selectedIds = ref<string[]>([]);
const modal = ref<"" | "delete" | "rename" | "move" | "merge" | "progress">("");
const modalError = ref("");
const modalLoading = ref(false);
const operationResult = ref<OperationSummary | null>(null);
const renameTarget = ref("");
const moveTargetPrefix = ref("");
const mergeTargetPrefix = ref("");
const conflictStrategy = ref<"fail" | "skip" | "overwrite">("fail");
const overwrite = ref(false);

const currentPrefix = computed(() => String(route.query.prefix || ""));
const items = computed(() => listing.value?.items || []);
const selectedItems = computed(() => items.value.filter((item) => selectedIds.value.includes(itemId(item))));
const selectedObjects = computed(() => selectedItems.value.filter((item) => item.type === "object" && item.key));
const selectedPrefixes = computed(() => selectedItems.value.filter((item) => item.type === "prefix" && item.prefix));
const allVisibleSelected = computed(
  () => items.value.length > 0 && items.value.every((item) => selectedIds.value.includes(itemId(item))),
);
const canRename = computed(() => selectedItems.value.length === 1);
const canDownload = computed(() => selectedObjects.value.length > 0 && selectedPrefixes.value.length === 0);
const canDelete = computed(() => selectedItems.value.length > 0);
const canMove = computed(() => selectedItems.value.length > 0);
const canMerge = computed(() => selectedPrefixes.value.length > 0 && selectedObjects.value.length === 0);
const isSearchMode = computed(() => Boolean(search.value.trim()));
const objectRange = computed(() => {
  const total = listing.value?.total_objects || 0;
  if (!total) return "0 items";
  const start = (listing.value?.offset || 0) + 1;
  const end = (listing.value?.offset || 0) + items.value.length;
  return `${start}-${end} of ${total}`;
});
const breadcrumbs = computed(() => {
  const parts = currentPrefix.value.split("/").filter(Boolean);
  const crumbs = [
    { label: "Buckets", to: "/" },
        {
          label: provider.value?.name || provider.value?.display_name || "Provider",
          to: providerId.value ? `/providers/${encodeURIComponent(providerId.value)}` : "/",
        },
        {
          label: bucket.value,
          to: providerId.value
            ? `/buckets/${encodeURIComponent(bucket.value)}?provider=${encodeURIComponent(providerId.value)}`
            : `/buckets/${encodeURIComponent(bucket.value)}`,
        },
  ];
  let prefix = "";
  for (const part of parts) {
    prefix += `${part}/`;
    crumbs.push({
      label: part,
      to: providerId.value
        ? `/buckets/${encodeURIComponent(bucket.value)}?provider=${encodeURIComponent(providerId.value)}&prefix=${encodeURIComponent(prefix)}`
        : `/buckets/${encodeURIComponent(bucket.value)}?prefix=${encodeURIComponent(prefix)}`,
    });
  }
  return crumbs;
});

function itemId(item: BucketBrowserItem) {
  return item.type === "prefix" ? `prefix:${item.prefix}` : `object:${item.key}`;
}

function itemPath(item: BucketBrowserItem) {
  return item.type === "prefix" ? item.prefix || item.name : item.key || item.name;
}

function toggleItem(item: BucketBrowserItem) {
  const id = itemId(item);
  selectedIds.value = selectedIds.value.includes(id)
    ? selectedIds.value.filter((selectedId) => selectedId !== id)
    : [...selectedIds.value, id];
}

function toggleAllVisible() {
  selectedIds.value = allVisibleSelected.value ? [] : items.value.map((item) => itemId(item));
}

function clearSelection() {
  selectedIds.value = [];
}

function actionTitle(enabled: boolean, title: string, disabledReason: string) {
  return enabled ? title : disabledReason;
}

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
      providerId: providerId.value || undefined,
      search: search.value.trim() || undefined,
      limit: pageSize.value,
      offset: offset.value,
      delimiter: "/",
    });
    selectedIds.value = selectedIds.value.filter((id) =>
      listing.value?.items.some((item) => itemId(item) === id),
    );
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
    provider.value = providerId.value
      ? await api.providerConnection(providerId.value)
      : await api.provider();
    details.value = providerId.value
      ? await api.providerBucketDetails(providerId.value, bucket.value)
      : await api.bucketDetails(bucket.value);
    summary.value = providerId.value
      ? await api.providerBucketSummary(providerId.value, bucket.value)
      : await api.bucketSummary(bucket.value);
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
    query: { ...(providerId.value ? { provider: providerId.value } : {}), ...(prefix ? { prefix } : {}) },
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
    const response = await api.scanBucket(bucket.value, providerId.value || undefined);
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
    const response = await api.presignDownload(bucket.value, item.key, providerId.value || undefined);
    window.open(response.url, "_blank", "noopener,noreferrer");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to create download URL.";
  }
}

async function openUpload(files?: FileList) {
  if (files) uploadQueue.setFiles(files);
  await router.push({
    path: providerId.value
      ? `/providers/${encodeURIComponent(providerId.value)}/buckets/${encodeURIComponent(bucket.value)}/upload`
      : `/buckets/${encodeURIComponent(bucket.value)}/upload`,
    query: currentPrefix.value ? { prefix: currentPrefix.value } : {},
  });
}

function handleDragEnter(event: DragEvent) {
  event.preventDefault();
  dragActive.value = true;
}

function handleDragOver(event: DragEvent) {
  event.preventDefault();
  dragActive.value = true;
}

function handleDragLeave(event: DragEvent) {
  if (event.currentTarget === event.target) {
    dragActive.value = false;
  }
}

function handleDrop(event: DragEvent) {
  event.preventDefault();
  dragActive.value = false;
  void openUpload(event.dataTransfer?.files);
}

function openDeleteModal(targetItems: BucketBrowserItem[]) {
  selectedIds.value = targetItems.map((item) => itemId(item));
  modalError.value = "";
  operationResult.value = null;
  modal.value = "delete";
}

function openRenameModal(targetItems: BucketBrowserItem[]) {
  selectedIds.value = targetItems.map((item) => itemId(item));
  const item = targetItems[0];
  renameTarget.value = item ? itemPath(item) : "";
  overwrite.value = false;
  modalError.value = "";
  operationResult.value = null;
  modal.value = "rename";
}

function openMoveModal(targetItems: BucketBrowserItem[]) {
  selectedIds.value = targetItems.map((item) => itemId(item));
  moveTargetPrefix.value = currentPrefix.value;
  overwrite.value = false;
  modalError.value = "";
  operationResult.value = null;
  modal.value = "move";
}

function openMergeModal(targetItems: BucketBrowserItem[]) {
  selectedIds.value = targetItems.map((item) => itemId(item));
  const prefixes = targetItems.filter((item) => item.type === "prefix");
  mergeTargetPrefix.value = prefixes[1]?.prefix || "";
  conflictStrategy.value = "fail";
  modalError.value = "";
  operationResult.value = null;
  modal.value = "merge";
}

async function refreshAfterOperation(message: string) {
  notice.value = message;
  await loadObjects();
  summary.value = providerId.value
    ? await api.providerBucketSummary(providerId.value, bucket.value)
    : await api.bucketSummary(bucket.value);
  details.value = providerId.value
    ? await api.providerBucketDetails(providerId.value, bucket.value)
    : await api.bucketDetails(bucket.value);
  clearSelection();
}

async function confirmDelete() {
  modalLoading.value = true;
  modalError.value = "";
  notice.value = "";
  try {
    let deleted = 0;
    for (const item of selectedItems.value) {
      if (item.type === "object" && item.key) {
        await api.deleteObject(bucket.value, item.key, providerId.value || undefined);
        deleted += 1;
      }
      if (item.type === "prefix" && item.prefix) {
        const response = await api.deletePrefix(
          bucket.value,
          item.prefix,
          providerId.value || undefined,
        );
        deleted += response.deleted_count;
      }
    }
    modal.value = "";
    await refreshAfterOperation(`Deleted ${deleted} object${deleted === 1 ? "" : "s"}.`);
  } catch (err) {
    modalError.value = err instanceof Error ? err.message : "Delete failed.";
  } finally {
    modalLoading.value = false;
  }
}

async function confirmRename() {
  const item = selectedItems.value[0];
  if (!item) return;
  modalLoading.value = true;
  modalError.value = "";
  try {
    if (item.type === "object" && item.key) {
      await api.renameObject({
        bucket: bucket.value,
        source_key: item.key,
        target_key: renameTarget.value,
        overwrite: overwrite.value,
      }, providerId.value || undefined);
      modal.value = "";
      await refreshAfterOperation("Object renamed.");
    } else if (item.type === "prefix" && item.prefix) {
      operationResult.value = await api.renamePrefix({
        bucket: bucket.value,
        source_prefix: item.prefix,
        target_prefix: renameTarget.value,
        overwrite: overwrite.value,
      }, providerId.value || undefined);
      modal.value = "progress";
      await refreshAfterOperation(`Prefix rename ${operationResult.value.status}.`);
    }
  } catch (err) {
    modalError.value = err instanceof Error ? err.message : "Rename failed.";
  } finally {
    modalLoading.value = false;
  }
}

function selectedMoveItems() {
  return selectedItems.value.map((item) =>
    item.type === "object" ? { type: "object" as const, key: item.key || "" } : { type: "prefix" as const, prefix: item.prefix || "" },
  );
}

async function confirmMove() {
  modalLoading.value = true;
  modalError.value = "";
  try {
    operationResult.value = await api.moveObjects({
      bucket: bucket.value,
      items: selectedMoveItems(),
      target_prefix: moveTargetPrefix.value,
      overwrite: overwrite.value,
    }, providerId.value || undefined);
    modal.value = "progress";
    await refreshAfterOperation(`Move ${operationResult.value.status}.`);
  } catch (err) {
    modalError.value = err instanceof Error ? err.message : "Move failed.";
  } finally {
    modalLoading.value = false;
  }
}

async function confirmMerge() {
  const source = selectedPrefixes.value[0]?.prefix;
  if (!source) return;
  modalLoading.value = true;
  modalError.value = "";
  try {
    operationResult.value = await api.mergePrefixes({
      bucket: bucket.value,
      source_prefix: source,
      target_prefix: mergeTargetPrefix.value,
      conflict_strategy: conflictStrategy.value,
    }, providerId.value || undefined);
    modal.value = "progress";
    await refreshAfterOperation(`Merge ${operationResult.value.status}.`);
  } catch (err) {
    modalError.value = err instanceof Error ? err.message : "Merge failed.";
  } finally {
    modalLoading.value = false;
  }
}

async function bulkDownload() {
  for (const item of selectedObjects.value) {
    await downloadObject(item);
  }
}

async function copyPath(item: BucketBrowserItem) {
  await navigator.clipboard.writeText(itemPath(item));
  notice.value = "Path copied.";
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
        <p>
          Provider: {{ provider?.name || provider?.display_name || providerId || "default" }}.
          Browsing automatically indexes the current prefix.
        </p>
      </div>
      <div class="inline-actions">
        <NuxtLink
          v-if="providerId"
          class="text-button"
          :to="`/providers/${encodeURIComponent(providerId)}/buckets/${encodeURIComponent(bucket)}/details`"
        >
          Details
        </NuxtLink>
        <button class="primary" :disabled="scanning" @click="scanBucket">
          <span :class="{ spin: scanning }">↻</span>
          {{ scanning ? "Scanning" : "Deep scan bucket" }}
        </button>
      </div>
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
        Search current path
        <input v-model="search" placeholder="*-billing-*, *.json, invoice-*" />
        <small class="muted">Supports patterns like *-billing-*, *.json, invoice-*</small>
      </label>
      <label>
        Page size
        <select v-model.number="pageSize">
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </label>
      <div class="upload-toolbar">
        <button
          class="icon-action primary-icon"
          type="button"
          aria-label="Upload"
          title="Upload"
          @click="openUpload()"
        >
          ⬆
        </button>
      </div>
    </section>

    <section v-if="selectedItems.length > 0" class="bulk-bar" aria-label="Bulk actions">
      <strong>{{ selectedItems.length }} selected</strong>
      <button
        class="icon-action"
        type="button"
        aria-label="Download selected"
        :title="actionTitle(canDownload, 'Download selected', 'Download supports selected objects only')"
        :disabled="!canDownload"
        @click="bulkDownload"
      >
        ⬇
      </button>
      <button
        class="icon-action danger-icon"
        type="button"
        aria-label="Delete selected"
        title="Delete selected"
        :disabled="!canDelete"
        @click="openDeleteModal(selectedItems)"
      >
        🗑
      </button>
      <button
        class="icon-action"
        type="button"
        aria-label="Move selected"
        title="Move selected"
        :disabled="!canMove"
        @click="openMoveModal(selectedItems)"
      >
        📦
      </button>
      <button
        class="icon-action"
        type="button"
        aria-label="Rename selected"
        :title="actionTitle(canRename, 'Rename selected', 'Rename requires exactly one selected item')"
        :disabled="!canRename"
        @click="openRenameModal(selectedItems)"
      >
        ✏
      </button>
      <button
        class="icon-action"
        type="button"
        aria-label="Merge prefixes"
        :title="actionTitle(canMerge, 'Merge prefixes', 'Merge requires selected prefixes only')"
        :disabled="!canMerge"
        @click="openMergeModal(selectedItems)"
      >
        🔀
      </button>
      <button class="text-button" type="button" @click="clearSelection">Clear selection</button>
    </section>

    <section
      class="table-wrap browser-table drop-zone"
      :class="{ 'drag-active': dragActive }"
      @dragenter="handleDragEnter"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    >
      <div v-if="dragActive" class="drop-overlay">Drop files to upload to this prefix</div>
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
            <th class="select-col">
              <input
                type="checkbox"
                aria-label="Select all visible rows"
                :checked="allVisibleSelected"
                @change="toggleAllVisible"
              />
            </th>
            <th>Name</th>
            <th>Type</th>
            <th>Size</th>
            <th>Last modified</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading || loadingObjects">
            <td colspan="6" class="empty">Loading current prefix...</td>
          </tr>
          <template v-else>
            <tr
              v-for="item in items"
              :key="item.prefix || item.key || item.name"
              :class="{ 'prefix-row': item.type === 'prefix' }"
            >
              <td class="select-col">
                <input
                  type="checkbox"
                  :aria-label="`Select ${itemPath(item)}`"
                  :checked="selectedIds.includes(itemId(item))"
                  @change="toggleItem(item)"
                />
              </td>
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
                  class="icon-action"
                  type="button"
                  aria-label="Open prefix"
                  title="Open"
                  @click="openPrefix(item.prefix)"
                >
                  👁
                </button>
                <button
                  v-if="item.type === 'prefix' && item.prefix"
                  class="icon-action"
                  type="button"
                  aria-label="Rename prefix"
                  title="Rename"
                  @click="openRenameModal([item])"
                >
                  ✏
                </button>
                <button
                  v-if="item.type === 'prefix' && item.prefix"
                  class="icon-action"
                  type="button"
                  aria-label="Move prefix"
                  title="Move"
                  @click="openMoveModal([item])"
                >
                  📦
                </button>
                <button
                  v-if="item.type === 'prefix' && item.prefix"
                  class="icon-action"
                  type="button"
                  aria-label="Merge prefix"
                  title="Merge"
                  @click="openMergeModal([item])"
                >
                  🔀
                </button>
                <button
                  class="icon-action"
                  type="button"
                  aria-label="Copy path"
                  title="Copy path"
                  @click="copyPath(item)"
                >
                  📋
                </button>
                <button
                  v-if="item.type === 'prefix' && item.prefix"
                  class="icon-action danger-icon"
                  type="button"
                  aria-label="Delete prefix"
                  title="Delete"
                  @click="openDeleteModal([item])"
                >
                  🗑
                </button>
                <template v-if="item.type === 'object'">
                  <NuxtLink
                    v-if="item.key"
                    class="icon-action icon-link-action"
                    :to="`/objects/preview?bucket=${encodeURIComponent(bucket)}&key=${encodeURIComponent(item.key)}${providerId ? `&provider=${encodeURIComponent(providerId)}` : ''}`"
                    aria-label="Preview object"
                    title="Preview"
                  >
                    👁
                  </NuxtLink>
                  <button
                    class="icon-action"
                    type="button"
                    aria-label="Download object"
                    title="Download"
                    @click="downloadObject(item)"
                  >
                    ⬇
                  </button>
                  <button
                    v-if="item.key"
                    class="icon-action"
                    type="button"
                    aria-label="Rename object"
                    title="Rename"
                    @click="openRenameModal([item])"
                  >
                    ✏
                  </button>
                  <button
                    v-if="item.key"
                    class="icon-action"
                    type="button"
                    aria-label="Move object"
                    title="Move"
                    @click="openMoveModal([item])"
                  >
                    📦
                  </button>
                  <button
                    v-if="item.key"
                    class="icon-action danger-icon"
                    type="button"
                    aria-label="Delete object"
                    title="Delete"
                    @click="openDeleteModal([item])"
                  >
                    🗑
                  </button>
                </template>
              </td>
            </tr>
          </template>
          <tr v-if="!loading && !loadingObjects && items.length === 0">
            <td colspan="6" class="empty">No folders or objects found in this prefix.</td>
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

    <div v-if="modal" class="modal-backdrop" role="presentation">
      <section class="modal-panel" role="dialog" aria-modal="true">
        <template v-if="modal === 'delete'">
          <h2>
            {{
              selectedPrefixes.length > 0
                ? "Delete prefix and all objects inside?"
                : "Delete object?"
            }}
          </h2>
          <ul class="modal-list">
            <li v-for="item in selectedItems" :key="itemId(item)">{{ itemPath(item) }}</li>
          </ul>
          <p class="warning-text">
            {{
              selectedPrefixes.length > 0
                ? "This will recursively delete nested objects and cannot be undone."
                : "This cannot be undone."
            }}
          </p>
          <div v-if="modalError" class="alert error">{{ modalError }}</div>
          <div class="modal-actions">
            <button class="text-button" type="button" :disabled="modalLoading" @click="modal = ''">Cancel</button>
            <button class="primary danger-primary" type="button" :disabled="modalLoading" @click="confirmDelete">
              {{ modalLoading ? "Deleting" : "Confirm delete" }}
            </button>
          </div>
        </template>

        <template v-else-if="modal === 'rename'">
          <h2>Rename</h2>
          <p class="muted">{{ selectedItems[0] ? itemPath(selectedItems[0]) : "" }}</p>
          <label>
            New object key or prefix
            <input v-model="renameTarget" />
          </label>
          <label class="checkbox-label">
            <input v-model="overwrite" type="checkbox" />
            Overwrite existing target
          </label>
          <div v-if="modalError" class="alert error">{{ modalError }}</div>
          <div class="modal-actions">
            <button class="text-button" type="button" :disabled="modalLoading" @click="modal = ''">Cancel</button>
            <button class="primary" type="button" :disabled="modalLoading || !renameTarget" @click="confirmRename">
              {{ modalLoading ? "Renaming" : "Confirm rename" }}
            </button>
          </div>
        </template>

        <template v-else-if="modal === 'move'">
          <h2>Move selected items</h2>
          <p class="muted">{{ selectedItems.length }} item{{ selectedItems.length === 1 ? "" : "s" }} selected</p>
          <label>
            Target prefix
            <input v-model="moveTargetPrefix" placeholder="archive/2026/" />
          </label>
          <label class="checkbox-label">
            <input v-model="overwrite" type="checkbox" />
            Overwrite existing targets
          </label>
          <div v-if="modalError" class="alert error">{{ modalError }}</div>
          <div class="modal-actions">
            <button class="text-button" type="button" :disabled="modalLoading" @click="modal = ''">Cancel</button>
            <button class="primary" type="button" :disabled="modalLoading" @click="confirmMove">
              {{ modalLoading ? "Moving" : "Confirm move" }}
            </button>
          </div>
        </template>

        <template v-else-if="modal === 'merge'">
          <h2>Merge prefixes</h2>
          <p class="muted">Source: {{ selectedPrefixes[0]?.prefix }}</p>
          <label>
            Target prefix
            <input v-model="mergeTargetPrefix" placeholder="prefix-b/" />
          </label>
          <label>
            Conflict strategy
            <select v-model="conflictStrategy">
              <option value="fail">Fail before modifying</option>
              <option value="skip">Skip duplicate targets</option>
              <option value="overwrite">Overwrite duplicate targets</option>
            </select>
          </label>
          <p class="warning-text">Duplicate protection is checked before merge when strategy is fail.</p>
          <div v-if="modalError" class="alert error">{{ modalError }}</div>
          <div class="modal-actions">
            <button class="text-button" type="button" :disabled="modalLoading" @click="modal = ''">Cancel</button>
            <button
              class="primary"
              type="button"
              :disabled="modalLoading || !mergeTargetPrefix"
              @click="confirmMerge"
            >
              {{ modalLoading ? "Merging" : "Confirm merge" }}
            </button>
          </div>
        </template>

        <template v-else-if="modal === 'progress'">
          <h2>Operation progress</h2>
          <p>{{ operationResult?.status || "completed" }}</p>
          <progress
            :value="operationResult?.moved_objects || 0"
            :max="operationResult?.total_objects || 1"
          />
          <p>
            {{ operationResult?.moved_objects || 0 }} / {{ operationResult?.total_objects || 0 }}
            completed
          </p>
          <div v-if="operationResult?.conflicts?.length" class="alert warning">
            {{ operationResult.conflicts.length }} conflict{{ operationResult.conflicts.length === 1 ? "" : "s" }}.
          </div>
          <div v-if="operationResult?.errors?.length" class="alert error">
            {{ operationResult.errors.join(", ") }}
          </div>
          <div class="modal-actions">
            <button class="primary" type="button" @click="modal = ''">Done</button>
          </div>
        </template>
      </section>
    </div>
  </main>
</template>
