<script setup lang="ts">
import type {
  BucketBrowserItem,
  BucketDetails,
  BucketObjectListing,
  BucketSummary,
  OperationSummary,
  ProviderConnection,
  ProviderInfo,
} from "../../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../../composables/useObjectLensApi";
import { useUploadQueue } from "../../../composables/useUploadQueue";

import {
  Eye,
  Edit3,
  Move,
  GitMerge,
  Copy,
  Trash2,
  Download,
  Upload,
  ChevronLeft,
  ChevronRight,
  Search,
  Database,
  Folder,
  FolderOpen,
  File,
  FileText,
  Settings,
  AlertCircle,
  Info,
  ShieldCheck,
  Check,
  RefreshCw,
  FileSpreadsheet,
  FileImage,
  FileCode
} from "@lucide/vue";

const route = useRoute();
const router = useRouter();
const api = useObjectLensApi();
const uploadQueue = useUploadQueue();

// Drawer state for modern Right-Side object details
const isDrawerOpen = ref(false);
const activeDrawerItem = ref<any>(null);
const activePresignedUrl = ref<string | null>(null);

async function openDetails(item: BucketBrowserItem) {
  if (item.type !== "object" || !item.key) return;
  activeDrawerItem.value = item;
  isDrawerOpen.value = true;
  try {
    const response = await api.presignDownload(bucket.value, item.key, providerId.value || undefined);
    activePresignedUrl.value = response.url;
  } catch (err) {
    console.error("Failed to fetch presigned URL for details drawer:", err);
    activePresignedUrl.value = null;
  }
}

function handleRowClick(item: BucketBrowserItem, event: Event) {
  const target = event.target as HTMLElement;
  if (target.closest("button") || target.closest("a") || target.closest("input")) {
    return;
  }
  if (item.type === "object") {
    openDetails(item);
  } else if (item.type === "prefix" && item.prefix) {
    openPrefix(item.prefix);
  }
}

function handleDrawerDelete(item: any) {
  openDeleteModal([item]);
}

function handleDrawerRename(item: any) {
  openRenameModal([item]);
}

function handleDrawerMove(item: any) {
  openMoveModal([item]);
}

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

const fileInputRef = ref<HTMLInputElement | null>(null);

function handleFilePickerChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    void openUpload(target.files);
  }
}

async function openUpload(files?: FileList) {
  if (files && files.length > 0) {
    uploadQueue.setFiles(files);
    await router.push({
      path: providerId.value
        ? `/providers/${encodeURIComponent(providerId.value)}/buckets/${encodeURIComponent(bucket.value)}/upload`
        : `/buckets/${encodeURIComponent(bucket.value)}/upload`,
      query: currentPrefix.value ? { prefix: currentPrefix.value } : {},
    });
  } else {
    fileInputRef.value?.click();
  }
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
  <div class="bucket-browser-page">
    <!-- Header -->
    <header class="page-title-section">
      <div class="header-text-block">
        <div class="title-with-icon-row">
          <FolderOpen :size="24" class="text-accent" />
          <h1>{{ bucket }}</h1>
        </div>
        <p class="subtitle">
          Provider: {{ provider?.name || provider?.display_name || providerId || "default" }} · Browsing automatically indexes S3 metadata.
        </p>
      </div>
      <div class="header-actions">
        <NuxtLink
          v-if="providerId"
          class="btn btn-secondary flex-center"
          :to="`/providers/${encodeURIComponent(providerId)}/buckets/${encodeURIComponent(bucket)}/details`"
        >
          <Info :size="14" />
          <span>Details</span>
        </NuxtLink>
        <button class="btn btn-secondary flex-center" :disabled="scanning" @click="scanBucket">
          <RefreshCw :size="14" :class="{ spin: scanning }" />
          <span>{{ scanning ? "Scanning..." : "Deep Scan" }}</span>
        </button>
      </div>
    </header>

    <div v-if="error" class="alert error">{{ error }}</div>
    <div v-if="notice" class="alert success">{{ notice }}</div>

    <!-- Metrics Cards Row -->
    <section class="metrics-card-grid" aria-label="Bucket index metrics summary">
      <!-- Metric 1: Parent Provider connection -->
      <article class="metric-card">
        <div class="metric-header">
          <span class="metric-title">Provider Connection</span>
          <Server :size="16" class="metric-icon muted" />
        </div>
        <div class="metric-content">
          <strong class="text-ellipsis" :title="provider?.display_name || summary?.provider || details?.provider || 'S3 Host'">
            {{ provider?.display_name || summary?.provider || details?.provider || "S3 Host" }}
          </strong>
          <span class="metric-trend">{{ provider?.type || "s3" }}</span>
        </div>
        <p class="metric-caption text-ellipsis" :title="provider?.endpoint_url || 'Endpoint not configured'">
          {{ provider?.endpoint_url || "Endpoint not configured" }}
        </p>
      </article>

      <!-- Metric 2: Total Indexed objects -->
      <article class="metric-card">
        <div class="metric-header">
          <span class="metric-title">Cached Metadata</span>
          <Database :size="16" class="metric-icon muted" />
        </div>
        <div class="metric-content">
          <strong>{{ details?.indexed_object_count ?? summary?.indexed_object_count ?? 0 }}</strong>
          <span class="metric-trend success">Indexed</span>
        </div>
        <p class="metric-caption">
          {{ formatBytes(details?.indexed_total_size ?? summary?.indexed_total_size) }} total size scanned.
        </p>
      </article>

      <!-- Metric 3: Last sync timestamp -->
      <article class="metric-card">
        <div class="metric-header">
          <span class="metric-title">Last Indexed At</span>
          <Activity :size="16" class="metric-icon muted" />
        </div>
        <div class="metric-content">
          <strong class="font-date-text">{{ formatDate(details?.last_indexed_at ?? summary?.last_indexed_at) }}</strong>
        </div>
        <p class="metric-caption">Prefix auto-sync on directory access is enabled.</p>
      </article>
    </section>

    <!-- Hidden native file picker trigger -->
    <input
      ref="fileInputRef"
      type="file"
      multiple
      class="visually-hidden"
      @change="handleFilePickerChange"
    />

    <section class="toolbar">
      <div class="toolbar-search-box">
        <Search :size="15" class="search-icon" />
        <input v-model="search" placeholder="Search current path (e.g. *-billing-*, *.json, invoice-*)" />
      </div>
      <div class="toolbar-controls-right">
        <div class="control-select-group">
          <span>Show</span>
          <select v-model.number="pageSize" class="control-select">
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
          <span>items</span>
        </div>
        <button
          class="btn btn-primary flex-center"
          type="button"
          aria-label="Upload File"
          title="Upload File"
          @click="openUpload()"
        >
          <Upload :size="14" />
          <span>Upload File</span>
        </button>
      </div>
    </section>

    <!-- Bulks Bar Overlay -->
    <section v-if="selectedItems.length > 0" class="bulk-bar" aria-label="Bulk actions">
      <strong>{{ selectedItems.length }} selected</strong>
      <div class="bulk-actions-group">
        <button
          class="btn btn-secondary flex-center"
          type="button"
          aria-label="Download selected"
          :title="actionTitle(canDownload, 'Download selected', 'Download supports selected objects only')"
          :disabled="!canDownload"
          @click="bulkDownload"
        >
          <Download :size="14" />
          <span>Download</span>
        </button>
        <button
          class="btn btn-secondary flex-center"
          type="button"
          aria-label="Rename selected"
          :title="actionTitle(canRename, 'Rename selected', 'Rename requires exactly one selected item')"
          :disabled="!canRename"
          @click="openRenameModal(selectedItems)"
        >
          <Edit3 :size="14" />
          <span>Rename</span>
        </button>
        <button
          class="btn btn-secondary flex-center"
          type="button"
          aria-label="Move selected"
          title="Move selected"
          :disabled="!canMove"
          @click="openMoveModal(selectedItems)"
        >
          <Move :size="14" />
          <span>Move</span>
        </button>
        <button
          v-if="canMerge"
          class="btn btn-secondary flex-center"
          type="button"
          aria-label="Merge prefixes"
          title="Merge prefixes"
          @click="openMergeModal(selectedItems)"
        >
          <GitMerge :size="14" />
          <span>Merge</span>
        </button>
        <button
          class="btn btn-secondary text-danger hover-danger flex-center"
          type="button"
          aria-label="Delete selected"
          title="Delete selected"
          :disabled="!canDelete"
          @click="openDeleteModal(selectedItems)"
        >
          <Trash2 :size="14" />
          <span>Delete</span>
        </button>
      </div>
      <button class="btn btn-secondary" type="button" @click="clearSelection">Clear selection</button>
    </section>

    <!-- Browser Table -->
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
          <span class="range-indicator">{{ objectRange }}</span>
          <button :disabled="!listing?.pagination.has_previous || loadingObjects" @click="previousPage" class="btn btn-secondary icon-only">
            <ChevronLeft :size="14" />
          </button>
          <button :disabled="!listing?.pagination.has_next || loadingObjects" @click="nextPage" class="btn btn-secondary icon-only">
            <ChevronRight :size="14" />
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
              class="clickable-row"
              @click="handleRowClick(item, $event)"
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
                <span class="item-icon">
                  <Folder v-if="item.type === 'prefix'" :size="16" class="text-accent" />
                  <FileImage v-else-if="item.icon === 'image'" :size="16" class="text-success" />
                  <FileSpreadsheet v-else-if="item.icon === 'csv'" :size="16" class="text-warning" />
                  <FileText v-else-if="item.icon === 'json'" :size="16" class="text-info" />
                  <FileCode v-else-if="item.icon === 'parquet'" :size="16" class="text-danger" />
                  <File v-else :size="16" class="text-muted" />
                </span>
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
                  <FolderOpen :size="14" />
                </button>
                <button
                  v-if="item.type === 'object'"
                  class="icon-action"
                  type="button"
                  aria-label="View Details"
                  title="View Details"
                  @click="openDetails(item)"
                >
                  <Eye :size="14" />
                </button>
                <button
                  v-if="item.type === 'object'"
                  class="icon-action"
                  type="button"
                  aria-label="Download object"
                  title="Download"
                  @click="downloadObject(item)"
                >
                  <Download :size="14" />
                </button>
                <button
                  class="icon-action"
                  type="button"
                  aria-label="Rename item"
                  title="Rename"
                  @click="openRenameModal([item])"
                >
                  <Edit3 :size="14" />
                </button>
                <button
                  class="icon-action"
                  type="button"
                  aria-label="Move item"
                  title="Move"
                  @click="openMoveModal([item])"
                >
                  <Move :size="14" />
                </button>
                <button
                  v-if="item.type === 'prefix' && item.prefix"
                  class="icon-action"
                  type="button"
                  aria-label="Merge prefix"
                  title="Merge"
                  @click="openMergeModal([item])"
                >
                  <GitMerge :size="14" />
                </button>
                <button
                  class="icon-action"
                  type="button"
                  aria-label="Copy path"
                  title="Copy path"
                  @click="copyPath(item)"
                >
                  <Copy :size="14" />
                </button>
                <button
                  class="icon-action danger-icon"
                  type="button"
                  aria-label="Delete item"
                  title="Delete"
                  @click="openDeleteModal([item])"
                >
                  <Trash2 :size="14" />
                </button>
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

    <!-- Right-Side Sliding Details Drawer -->
    <DetailsDrawer
      :is-open="isDrawerOpen"
      :item="activeDrawerItem"
      :bucket="bucket"
      :provider-id="providerId"
      :presigned-url="activePresignedUrl"
      @close="isDrawerOpen = false"
      @delete="handleDrawerDelete"
      @rename="handleDrawerRename"
      @move="handleDrawerMove"
    />
  </div>
</template>

<style scoped>
.bucket-browser-page {
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

.font-date-text {
  font-size: 14px !important;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
