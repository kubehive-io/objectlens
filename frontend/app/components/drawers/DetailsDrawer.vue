<script setup lang="ts">
import { ref, watch, computed } from "vue";
import {
  X,
  FileText,
  Calendar,
  Database,
  Tag,
  Download,
  Trash2,
  Edit,
  Copy,
  FolderOpen
} from "@lucide/vue";

// Define TypeScript interfaces for our drawer items
export interface DrawerItem {
  key: string;
  size: number;
  last_modified?: string | null;
  etag?: string | null;
  storage_class?: string | null;
  content_type?: string | null;
}

const props = defineProps<{
  isOpen: boolean;
  item: DrawerItem | null;
  bucket: string;
  providerId: string;
  presignedUrl?: string | null;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "delete", item: DrawerItem): void;
  (e: "rename", item: DrawerItem): void;
  (e: "move", item: DrawerItem): void;
}>();

// Helper to format bytes to human-readable size
function formatBytes(bytes: number, decimals = 2) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}

// Get file extension
const fileExtension = computed(() => {
  if (!props.item) return "";
  const parts = props.item.key.split(".");
  return parts.length > 1 ? parts.pop()?.toLowerCase() || "" : "";
});

// Check if file is previewable
const isPreviewableImage = computed(() => {
  const images = ["png", "jpg", "jpeg", "webp", "gif", "svg"];
  return images.includes(fileExtension.value);
});

// Trigger download
function downloadFile() {
  if (props.presignedUrl) {
    window.open(props.presignedUrl, "_blank");
  }
}
</script>

<template>
  <Transition name="slide-over">
    <aside v-if="isOpen && item" class="details-drawer-container" aria-label="Selected item details">
      <!-- Drawer Header -->
      <div class="drawer-header">
        <div class="drawer-title-row">
          <FileText :size="20" class="text-accent" />
          <h2 class="drawer-filename" :title="item.key">{{ item.key.split('/').pop() }}</h2>
        </div>
        <button class="drawer-close-btn" type="button" aria-label="Close details" @click="emit('close')">
          <X :size="18" />
        </button>
      </div>

      <!-- Drawer Scrollable Content -->
      <div class="drawer-body">
        <!-- Overview Card -->
        <section class="drawer-card">
          <h4>Overview</h4>
          <dl class="drawer-details-list">
            <div class="detail-row">
              <dt><FolderOpen :size="14" /> Prefix Path</dt>
              <dd :title="item.key">{{ item.key.substring(0, item.key.lastIndexOf('/') + 1) || '/' }}</dd>
            </div>
            <div class="detail-row">
              <dt><Database :size="14" /> File Size</dt>
              <dd>{{ formatBytes(item.size) }}</dd>
            </div>
            <div class="detail-row">
              <dt><Calendar :size="14" /> Last Modified</dt>
              <dd>{{ item.last_modified ? new Date(item.last_modified).toLocaleString() : 'N/A' }}</dd>
            </div>
          </dl>
        </section>

        <!-- Preview Block if available -->
        <section class="drawer-card" v-if="isPreviewableImage && presignedUrl">
          <h4>Preview</h4>
          <div class="drawer-preview-box">
            <img :src="presignedUrl" class="drawer-img-preview" alt="File preview" />
          </div>
        </section>

        <!-- Metadata Section -->
        <section class="drawer-card">
          <h4>System Metadata</h4>
          <dl class="drawer-details-list">
            <div class="detail-row" v-if="item.etag">
              <dt>ETag</dt>
              <dd class="code-val"><code>{{ item.etag }}</code></dd>
            </div>
            <div class="detail-row" v-if="item.storage_class">
              <dt>Storage Class</dt>
              <dd><span class="storage-badge">{{ item.storage_class }}</span></dd>
            </div>
            <div class="detail-row" v-if="item.content_type">
              <dt>Content Type</dt>
              <dd><code>{{ item.content_type }}</code></dd>
            </div>
          </dl>
        </section>

        <!-- Placeholder for user metadata tags -->
        <section class="drawer-card">
          <div class="flex-space-between mb-8">
            <h4>User Metadata Tags</h4>
            <span class="storage-badge">0 tags</span>
          </div>
          <p class="small-muted-text">Placeholders for S3 Object tagging and custom key-value metadata pairs will populate here.</p>
        </section>
      </div>

      <!-- Drawer Footer Quick Actions -->
      <div class="drawer-footer">
        <button
          v-if="presignedUrl"
          class="btn btn-primary flex-center flex-1"
          type="button"
          @click="downloadFile"
        >
          <Download :size="14" />
          <span>Download</span>
        </button>
        <button class="btn btn-secondary" type="button" title="Rename Object" @click="emit('rename', item)">
          <Edit :size="14" />
        </button>
        <button class="btn btn-secondary" type="button" title="Move Object" @click="emit('move', item)">
          <Copy :size="14" />
        </button>
        <button class="btn btn-secondary text-danger hover-danger" type="button" title="Delete Object" @click="emit('delete', item)">
          <Trash2 :size="14" />
        </button>
      </div>
    </aside>
  </Transition>
</template>
