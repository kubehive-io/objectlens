<script setup lang="ts">
import type { Bucket, ObjectMetadata } from "../app/composables/useObjectLensApi";
import { useObjectLensApi } from "../app/composables/useObjectLensApi";

const api = useObjectLensApi();

const buckets = ref<Bucket[]>([]);
const selectedBucket = ref("");
const search = ref("");
const objects = ref<ObjectMetadata[]>([]);
const loadingBuckets = ref(true);
const loadingObjects = ref(false);
const scanning = ref(false);
const error = ref("");
const notice = ref("");

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

async function loadBuckets() {
  loadingBuckets.value = true;
  error.value = "";
  try {
    const response = await api.listBuckets();
    buckets.value = response.buckets;
    selectedBucket.value = response.buckets[0]?.name || "";
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load buckets";
  } finally {
    loadingBuckets.value = false;
  }
}

async function loadObjects() {
  if (!selectedBucket.value) return;
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
  await loadBuckets();
});
</script>

<template>
  <main class="app-shell">
    <section class="topbar">
      <div>
        <h1>ObjectLens</h1>
        <p>Kubernetes-ready object storage browser for indexed S3 metadata.</p>
      </div>
      <button class="primary" :disabled="!selectedBucket || scanning" @click="scanBucket">
        <span :class="{ spin: scanning }">↻</span>
        {{ scanning ? "Scanning" : "Scan bucket" }}
      </button>
    </section>

    <section class="toolbar">
      <label>
        Bucket
        <select v-model="selectedBucket" :disabled="loadingBuckets">
          <option v-for="bucket in buckets" :key="bucket.name" :value="bucket.name">
            {{ bucket.name }}
          </option>
        </select>
      </label>

      <label>
        Search key
        <input v-model="search" placeholder="backup, logs/, snapshot.parquet" />
      </label>
    </section>

    <div v-if="error" class="alert error">{{ error }}</div>
    <div v-if="notice" class="alert success">{{ notice }}</div>

    <section class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Key</th>
            <th>Size</th>
            <th>Last Modified</th>
            <th>Storage Class</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loadingObjects">
            <td colspan="5" class="empty">Loading indexed objects...</td>
          </tr>
          <template v-else>
            <tr v-for="object in objects" :key="`${object.bucket}/${object.key}`">
              <td class="key-cell">{{ object.key }}</td>
              <td>{{ formatBytes(object.size) }}</td>
              <td>{{ formatDate(object.last_modified) }}</td>
              <td>{{ object.storage_class || "-" }}</td>
              <td class="actions">
                <button class="icon-button" title="Download" @click="downloadObject(object.key)">
                  ↓
                </button>
              </td>
            </tr>
          </template>
          <tr v-if="!loadingObjects && objects.length === 0">
            <td colspan="5" class="empty">
              No indexed objects found. Scan the bucket to populate local metadata.
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>
