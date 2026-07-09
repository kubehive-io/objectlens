<script setup lang="ts">
import { useObjectLensApi } from "../../../composables/useObjectLensApi";
import { useUploadQueue } from "../../../composables/useUploadQueue";

const route = useRoute();
const router = useRouter();
const api = useObjectLensApi();
const uploadQueue = useUploadQueue();

const bucket = computed(() => String(route.params.bucket || ""));
const providerId = computed(() => String(route.params.providerId || route.query.provider || ""));
const prefix = computed(() => String(route.query.prefix || ""));
const fileInput = ref<HTMLInputElement | null>(null);
const dragActive = ref(false);
const uploading = ref(false);
const progress = ref(0);
const error = ref("");
const result = ref("");
const fileStates = ref<Record<string, { status: "pending" | "uploading" | "uploaded" | "failed"; error?: string }>>(
  {},
);

const breadcrumbs = computed(() => {
  const parts = prefix.value.split("/").filter(Boolean);
  const crumbs = [
    { label: "Buckets", to: "/" },
    {
      label: providerId.value || "Provider",
      to: providerId.value ? `/providers/${encodeURIComponent(providerId.value)}` : "/",
    },
    {
      label: bucket.value,
      to: providerId.value
        ? `/buckets/${encodeURIComponent(bucket.value)}?provider=${encodeURIComponent(providerId.value)}`
        : `/buckets/${encodeURIComponent(bucket.value)}`,
    },
  ];
  let currentPrefix = "";
  for (const part of parts) {
    currentPrefix += `${part}/`;
    crumbs.push({
      label: part,
      to: `/buckets/${encodeURIComponent(bucket.value)}?prefix=${encodeURIComponent(currentPrefix)}`,
    });
  }
  crumbs.push({ label: "Upload", to: route.fullPath });
  return crumbs;
});

function formatBytes(value: number) {
  if (value === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function targetKey(file: File) {
  const normalizedPrefix = prefix.value.replace(/^\/+|\/+$/g, "");
  return normalizedPrefix ? `${normalizedPrefix}/${file.name}` : file.name;
}

function fileId(file: File, index: number) {
  return `${file.name}-${file.size}-${file.lastModified}-${index}`;
}

function stateFor(file: File, index: number) {
  return fileStates.value[fileId(file, index)]?.status || "pending";
}

function openPicker() {
  fileInput.value?.click();
}

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files) uploadQueue.addFiles(target.files);
  target.value = "";
}

function handleDrop(event: DragEvent) {
  event.preventDefault();
  dragActive.value = false;
  if (event.dataTransfer?.files) uploadQueue.setFiles(event.dataTransfer.files);
}

async function startUpload() {
  if (!uploadQueue.files.value.length) return;
  uploading.value = true;
  error.value = "";
  result.value = "";
  progress.value = 0;
  try {
    let completed = 0;
    const files = [...uploadQueue.files.value];
    for (const [index, file] of files.entries()) {
      const id = fileId(file, index);
      fileStates.value[id] = { status: "uploading" };
      try {
      await api.uploadObject(bucket.value, prefix.value, file, providerId.value || undefined);
        fileStates.value[id] = { status: "uploaded" };
        completed += 1;
      } catch (err) {
        fileStates.value[id] = {
          status: "failed",
          error: err instanceof Error ? err.message : "Upload failed.",
        };
        throw err;
      } finally {
        progress.value = Math.round((completed / files.length) * 100);
      }
    }
    result.value = `Uploaded ${completed} file${completed === 1 ? "" : "s"} to ${prefix.value || "bucket root"}.`;
    uploadQueue.clearFiles();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Upload failed.";
  } finally {
    uploading.value = false;
  }
}

function backToBucket() {
  void router.push({
    path: `/buckets/${encodeURIComponent(bucket.value)}`,
    query: {
      ...(providerId.value ? { provider: providerId.value } : {}),
      ...(prefix.value ? { prefix: prefix.value } : {}),
    },
  });
}
</script>

<template>
  <main class="app-shell">
    <nav class="breadcrumb real-breadcrumb" aria-label="Upload path">
      <NuxtLink v-for="(crumb, index) in breadcrumbs" :key="`${crumb.to}-${index}`" :to="crumb.to">
        {{ crumb.label }}<span v-if="index < breadcrumbs.length - 1">›</span>
      </NuxtLink>
    </nav>

    <section class="topbar compact-topbar">
      <div>
        <h1>Upload objects</h1>
        <p>{{ bucket }} / {{ prefix || "bucket root" }}</p>
      </div>
      <button class="text-button" type="button" @click="backToBucket">Cancel</button>
    </section>

    <div v-if="error" class="alert error">{{ error }}</div>
    <div v-if="result" class="alert success">
      {{ result }}
      <div class="inline-actions">
        <button class="text-button" type="button" @click="backToBucket">Back to bucket</button>
        <button class="text-button" type="button" @click="openPicker">Upload more</button>
      </div>
    </div>

    <section
      class="upload-panel"
      :class="{ 'drag-active': dragActive }"
      @dragenter.prevent="dragActive = true"
      @dragover.prevent="dragActive = true"
      @dragleave.prevent="dragActive = false"
      @drop="handleDrop"
    >
      <input ref="fileInput" class="visually-hidden" type="file" multiple @change="handleInput" />
      <div class="upload-drop-copy">
        <strong>Drop files to upload to this prefix</strong>
        <p>Upload target: {{ prefix || "bucket root" }}</p>
      </div>
      <button class="primary" type="button" @click="openPicker">Choose files</button>
    </section>

    <section class="table-wrap section-block">
      <div class="table-header">
        <div>
          <h2>Selected files</h2>
          <p>Upload does not start until you confirm.</p>
        </div>
        <button
          class="primary"
          type="button"
          :disabled="uploading || uploadQueue.files.value.length === 0"
          @click="startUpload"
        >
          Start upload
        </button>
      </div>
      <div v-if="uploading" class="progress-block">
        <progress :value="progress" max="100" />
        <span>{{ progress }}%</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Size</th>
            <th>Target object key</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="uploadQueue.files.value.length === 0">
            <td colspan="5" class="empty">No files selected.</td>
          </tr>
          <tr v-for="(file, index) in uploadQueue.files.value" :key="`${file.name}-${file.size}-${index}`">
            <td>{{ file.name }}</td>
            <td>{{ formatBytes(file.size) }}</td>
            <td class="key-cell">{{ targetKey(file) }}</td>
            <td>
              <span class="status-pill" :class="`status-${stateFor(file, index)}`">
                {{ stateFor(file, index) }}
              </span>
            </td>
            <td class="actions">
              <button
                class="icon-action"
                type="button"
                aria-label="Remove selected file"
                title="Remove"
                :disabled="uploading"
                @click="uploadQueue.removeFile(index)"
              >
                🗑
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>
