<script setup lang="ts">
import { ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useObjectLensApi } from "../../../composables/useObjectLensApi";
import { useUploadQueue } from "../../../composables/useUploadQueue";
import {
  Upload,
  CheckCircle2,
  AlertTriangle,
  Loader,
  X,
  FileUp,
  FolderOpen,
  ArrowLeft,
  Trash2,
  Folder
} from "@lucide/vue";

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
  <div class="upload-page-container">
    <!-- Header -->
    <header class="page-title-section">
      <div class="header-text-block">
        <div class="title-with-icon-row">
          <FolderOpen :size="24" class="text-accent" />
          <h1>Upload Objects</h1>
        </div>
        <p class="subtitle">
          Bucket: <strong>{{ bucket }}</strong> <span v-if="prefix">· Prefix: <code>{{ prefix }}</code></span>
        </p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary flex-center" type="button" @click="backToBucket">
          <ArrowLeft :size="14" />
          <span>Back to Bucket</span>
        </button>
      </div>
    </header>

    <!-- Error/Success Notices -->
    <div v-if="error" class="alert error flex-center-left gap-10">
      <AlertTriangle :size="16" />
      <span>{{ error }}</span>
    </div>
    
    <div v-if="result" class="alert success flex-center-left gap-10">
      <CheckCircle2 :size="16" />
      <span class="flex-1">{{ result }}</span>
      <div class="inline-actions gap-10">
        <button class="btn btn-primary" type="button" @click="backToBucket">Back to Bucket</button>
        <button class="btn btn-secondary" type="button" @click="openPicker">Upload More</button>
      </div>
    </div>

    <!-- Drag and Drop Panel -->
    <section
      class="premium-upload-drop-panel"
      :class="{ 'drag-active': dragActive }"
      @dragenter.prevent="dragActive = true"
      @dragover.prevent="dragActive = true"
      @dragleave.prevent="dragActive = false"
      @drop="handleDrop"
    >
      <input ref="fileInput" class="visually-hidden" type="file" multiple @change="handleInput" />
      <div class="drop-illustration-circle">
        <FileUp :size="32" class="text-accent" />
      </div>
      <div class="drop-text-content">
        <h3>Drag and Drop Files Here</h3>
        <p class="subtitle">Upload target: <code>{{ prefix || "bucket root" }}</code></p>
      </div>
      <button class="btn btn-primary flex-center" type="button" @click="openPicker">
        <span>Choose Files</span>
      </button>
    </section>

    <!-- Queue List -->
    <section class="dashboard-content-block mt-32">
      <div class="block-header border-bottom pb-12 mb-24">
        <div>
          <h2>Selected Upload Queue</h2>
          <p>Confirm and verify your selected files before starting the S3 upload sequence.</p>
        </div>
        
        <button
          class="btn btn-primary flex-center"
          type="button"
          :disabled="uploading || uploadQueue.files.value.length === 0"
          @click="startUpload"
        >
          <Loader v-if="uploading" :size="14" class="spin" />
          <Upload v-else :size="14" />
          <span>{{ uploading ? 'Uploading...' : 'Start S3 Upload' }}</span>
        </button>
      </div>

      <!-- Sync Progress indicator -->
      <div v-if="uploading" class="upload-progress-bar-block mb-16">
        <div class="flex-space-between mb-8">
          <span class="progress-lbl">Uploading S3 batch...</span>
          <span class="progress-pct">{{ progress }}%</span>
        </div>
        <progress class="upload-progress-element" :value="progress" max="100" />
      </div>

      <!-- Queue Table -->
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>File Name</th>
              <th>Size</th>
              <th>Target Object Key</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="uploadQueue.files.value.length === 0">
              <td colspan="5" class="empty">No files in S3 upload queue yet. Drag files in or click choose to populate queue.</td>
            </tr>
            <tr v-for="(file, index) in uploadQueue.files.value" :key="`${file.name}-${file.size}-${index}`">
              <td class="font-bold-text">{{ file.name }}</td>
              <td>{{ formatBytes(file.size) }}</td>
              <td class="key-cell"><code>{{ targetKey(file) }}</code></td>
              <td>
                <span class="provider-status-badge" :class="stateFor(file, index) === 'uploaded' ? 'healthy' : (stateFor(file, index) === 'failed' ? 'unhealthy' : 'info')">
                  <span class="status-dot-indicator" />
                  <span>{{ stateFor(file, index) }}</span>
                </span>
              </td>
              <td class="actions">
                <button
                  class="icon-action danger-icon"
                  type="button"
                  aria-label="Remove selected file"
                  title="Remove"
                  :disabled="uploading"
                  @click="uploadQueue.removeFile(index)"
                >
                  <Trash2 :size="14" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.upload-page-container {
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

.premium-upload-drop-panel {
  background: var(--panel);
  border: 2px dashed var(--border-soft);
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 12px rgb(15 23 42 / 2%);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.premium-upload-drop-panel.drag-active {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.drop-illustration-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--accent-soft);
  display: flex;
  align-items: center;
  justify-content: center;
}

.drop-text-content h3 {
  font-size: 18px;
  font-weight: 800;
  margin: 0 0 6px 0;
  letter-spacing: -0.3px;
}

.upload-progress-bar-block {
  background: var(--panel-subtle);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 16px;
}

.progress-lbl {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted-strong);
}

.progress-pct {
  font-size: 12px;
  font-weight: 800;
  color: var(--accent);
}

.upload-progress-element {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
  border: none;
  background: var(--border-soft);
}

.upload-progress-element::-webkit-progress-bar {
  background: var(--border-soft);
}

.upload-progress-element::-webkit-progress-value {
  background: var(--accent);
}

.upload-progress-element::-moz-progress-bar {
  background: var(--accent);
}

.font-bold-text {
  font-weight: 600;
  font-size: 13px;
}

.key-cell code {
  font-size: 11px;
}

.gap-10 {
  gap: 10px;
}

.mb-8 {
  margin-bottom: 8px;
}

.mb-16 {
  margin-bottom: 16px;
}

.mt-32 {
  margin-top: 32px;
}

.pb-12 {
  padding-bottom: 12px;
}

.mb-24 {
  margin-bottom: 24px;
}

.border-bottom {
  border-bottom: 1px solid var(--border-soft);
}

.flex-shrink-0 {
  flex-shrink: 0;
}
</style>
