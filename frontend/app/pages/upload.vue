<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useObjectLensApi } from "../composables/useObjectLensApi";
import { useUploadQueue } from "../composables/useUploadQueue";
import type { ProviderConnection, Bucket } from "../composables/useObjectLensApi";
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
  Folder,
  ArrowRight,
  Settings,
  Sliders,
  FileText,
  ShieldCheck,
  Check,
  Plus,
  Server,
  ChevronDown,
  Search,
  Lock
} from "@lucide/vue";

const route = useRoute();
const router = useRouter();
const api = useObjectLensApi();
const uploadQueue = useUploadQueue();

// Query Param Pre-selections
const queryProviderId = computed(() => String(route.query.provider || ""));
const queryBucket = computed(() => String(route.query.bucket || ""));
const prefix = computed(() => String(route.query.prefix || ""));

// Target selections
const selectedProviderId = ref("");
const selectedBucket = ref("");

// Focused Select Element Tracker
const activeSelect = ref("");

// Custom Dropdown state
const isProviderDropdownOpen = ref(false);
const isBucketDropdownOpen = ref(false);
const providerSearchQuery = ref("");
const bucketSearchQuery = ref("");

const providerDropdownRef = ref<HTMLElement | null>(null);
const bucketDropdownRef = ref<HTMLElement | null>(null);
const providerSearchInputRef = ref<HTMLInputElement | null>(null);
const bucketSearchInputRef = ref<HTMLInputElement | null>(null);

const selectedProvider = computed(() => {
  return providersList.value.find((p) => p.id === selectedProviderId.value) || null;
});

const filteredProviders = computed(() => {
  if (!providerSearchQuery.value) return providersList.value;
  const q = providerSearchQuery.value.toLowerCase();
  return providersList.value.filter(
    (p) =>
      p.name.toLowerCase().includes(q) ||
      p.id.toLowerCase().includes(q) ||
      p.type.toLowerCase().includes(q),
  );
});

const filteredBuckets = computed(() => {
  if (!bucketSearchQuery.value) return bucketsList.value;
  const q = bucketSearchQuery.value.toLowerCase();
  return bucketsList.value.filter((b) => b.name.toLowerCase().includes(q));
});

function toggleProviderDropdown() {
  isProviderDropdownOpen.value = !isProviderDropdownOpen.value;
  isBucketDropdownOpen.value = false;
  providerSearchQuery.value = "";
  if (isProviderDropdownOpen.value) {
    setTimeout(() => {
      providerSearchInputRef.value?.focus();
    }, 50);
  }
}

function toggleBucketDropdown() {
  if (!selectedProviderId.value) return;
  isBucketDropdownOpen.value = !isBucketDropdownOpen.value;
  isProviderDropdownOpen.value = false;
  bucketSearchQuery.value = "";
  if (isBucketDropdownOpen.value) {
    setTimeout(() => {
      bucketSearchInputRef.value?.focus();
    }, 50);
  }
}

function selectProviderItem(id: string) {
  selectedProviderId.value = id;
  isProviderDropdownOpen.value = false;
  providerSearchQuery.value = "";
}

function selectBucketItem(name: string) {
  selectedBucket.value = name;
  isBucketDropdownOpen.value = false;
  bucketSearchQuery.value = "";
}

function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement;
  if (providerDropdownRef.value && !providerDropdownRef.value.contains(target)) {
    isProviderDropdownOpen.value = false;
  }
  if (bucketDropdownRef.value && !bucketDropdownRef.value.contains(target)) {
    isBucketDropdownOpen.value = false;
  }
}

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});

// Dropdown data options
const providersList = ref<ProviderConnection[]>([]);
const bucketsList = ref<Bucket[]>([]);
const loadingProviders = ref(false);
const loadingBuckets = ref(false);

// Wizard Stepper State
const activeStep = ref(1); // 1: Queue & Target, 2: Global Configuration, 3: Overrides & Review, 4: Uploading Progress

// Global configuration defaults
const globalPrefix = ref("");
const globalCacheControl = ref("max-age=31536000");
const globalMetadata = ref<Array<{ key: string; value: string }>>([]);

// Input fields for adding global metadata headers
const newGlobalKey = ref("");
const newGlobalValue = ref("");

// Individual file overrides
const fileConfigs = ref<Record<string, {
  targetKey: string;
  cacheControl: string;
  metadata: Array<{ key: string; value: string }>;
}>>({});

// Input fields for adding individual metadata overrides
const newLocalKey = ref("");
const newLocalValue = ref("");

// Track the file index currently selected for individual overrides
const editingIndex = ref<number | null>(null);

const activeEditingFile = computed(() => {
  if (editingIndex.value === null) return null;
  return uploadQueue.files.value[editingIndex.value] || null;
});

const activeEditingConfig = computed(() => {
  if (!activeEditingFile.value || editingIndex.value === null) return null;
  const id = fileId(activeEditingFile.value, editingIndex.value);
  return fileConfigs.value[id] || null;
});

const fileInput = ref<HTMLInputElement | null>(null);
const dragActive = ref(false);
const uploading = ref(false);
const progress = ref(0);
const completedCount = ref(0);
const currentUploadingFile = ref<File | null>(null);

// Live stopwatch duration timing
const elapsedTime = ref(0);
let timerInterval: any = null;

const formattedDuration = computed(() => {
  const sec = elapsedTime.value;
  if (sec < 60) return `${sec}s`;
  return `${Math.floor(sec / 60)}m ${sec % 60}s`;
});

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

function targetKeyForFile(file: File, prefixVal: string) {
  const normalized = prefixVal.replace(/^\/+|\/+$/g, "");
  return normalized ? `${normalized}/${file.name}` : file.name;
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

// Fetch connection directories and configurations
onMounted(async () => {
  loadingProviders.value = true;
  try {
    providersList.value = await api.listProviders();
    
    // Auto-select query parameters if available
    if (queryProviderId.value) {
      selectedProviderId.value = queryProviderId.value;
    } else if (providersList.value.length === 1 && providersList.value[0]) {
      // Auto-select connection if exactly 1 is registered
      selectedProviderId.value = providersList.value[0].id;
    }

    if (queryBucket.value) {
      selectedBucket.value = queryBucket.value;
    }
    if (prefix.value) {
      globalPrefix.value = prefix.value;
    }
  } catch (err) {
    error.value = "Failed to load storage connections.";
  } finally {
    loadingProviders.value = false;
  }
});

// Watch provider selection and fetch its buckets
watch(selectedProviderId, async (newProvider) => {
  if (!newProvider) {
    bucketsList.value = [];
    selectedBucket.value = "";
    return;
  }
  loadingBuckets.value = true;
  try {
    const res = await api.listProviderBuckets(newProvider);
    bucketsList.value = res.buckets;
    
    // Keep query bucket if provider matches
    if (queryProviderId.value === newProvider && queryBucket.value) {
      selectedBucket.value = queryBucket.value;
    } else if (!queryBucket.value && bucketsList.value.length === 1 && bucketsList.value[0]) {
      // Auto-select bucket if exactly 1 exists on connection
      selectedBucket.value = bucketsList.value[0].name;
    } else {
      selectedBucket.value = "";
    }
  } catch (err) {
    error.value = `Failed to fetch buckets for storage provider: ${newProvider}`;
  } finally {
    loadingBuckets.value = false;
  }
});

// Populate file configs dynamically
function initializeFileConfigs() {
  uploadQueue.files.value.forEach((file, index) => {
    const id = fileId(file, index);
    if (!fileConfigs.value[id]) {
      fileConfigs.value[id] = {
        targetKey: targetKeyForFile(file, globalPrefix.value),
        cacheControl: globalCacheControl.value,
        metadata: JSON.parse(JSON.stringify(globalMetadata.value))
      };
    }
  });
  if (uploadQueue.files.value.length > 0 && editingIndex.value === null) {
    editingIndex.value = 0;
  }
}

watch(() => uploadQueue.files.value.length, () => {
  initializeFileConfigs();
}, { immediate: true });

function applyGlobalDefaults() {
  uploadQueue.files.value.forEach((file, index) => {
    const id = fileId(file, index);
    fileConfigs.value[id] = {
      targetKey: targetKeyForFile(file, globalPrefix.value),
      cacheControl: globalCacheControl.value,
      metadata: JSON.parse(JSON.stringify(globalMetadata.value))
    };
  });
  activeStep.value = 3;
}

// Global Metadata management
function addGlobalHeader() {
  const key = newGlobalKey.value.trim().toLowerCase();
  const val = newGlobalValue.value.trim();
  if (!key || !val) return;
  if (globalMetadata.value.some(h => h.key === key)) return;
  globalMetadata.value.push({ key, value: val });
  newGlobalKey.value = "";
  newGlobalValue.value = "";
}

function removeGlobalHeader(idx: number) {
  globalMetadata.value.splice(idx, 1);
}

// Local Metadata management
function addLocalHeader() {
  if (!activeEditingConfig.value) return;
  const key = newLocalKey.value.trim().toLowerCase();
  const val = newLocalValue.value.trim();
  if (!key || !val) return;
  if (activeEditingConfig.value.metadata.some(h => h.key === key)) return;
  activeEditingConfig.value.metadata.push({ key, value: val });
  newLocalKey.value = "";
  newLocalValue.value = "";
}

function removeLocalHeader(idx: number) {
  if (!activeEditingConfig.value) return;
  activeEditingConfig.value.metadata.splice(idx, 1);
}

async function startUpload() {
  if (!uploadQueue.files.value.length || !selectedBucket.value) return;
  uploading.value = true;
  activeStep.value = 4; // Shift to progress step
  error.value = "";
  result.value = "";
  progress.value = 0;
  completedCount.value = 0;
  
  // Start stopwatch interval
  elapsedTime.value = 0;
  timerInterval = setInterval(() => {
    elapsedTime.value += 1;
  }, 1000);

  try {
    let completed = 0;
    const files = [...uploadQueue.files.value];
    for (const [index, file] of files.entries()) {
      const id = fileId(file, index);
      fileStates.value[id] = { status: "uploading" };
      currentUploadingFile.value = file;
      try {
        const config = fileConfigs.value[id] || {
          targetKey: targetKeyForFile(file, globalPrefix.value),
          cacheControl: "",
          metadata: []
        };
        const metadataDict: Record<string, string> = {};
        config.metadata.forEach(h => {
          metadataDict[h.key] = h.value;
        });
        
        await api.uploadObject(
          selectedBucket.value,
          "",
          file,
          selectedProviderId.value || undefined,
          config.targetKey,
          config.cacheControl || undefined,
          metadataDict
        );
        fileStates.value[id] = { status: "uploaded" };
        completed += 1;
      } catch (err) {
        fileStates.value[id] = {
          status: "failed",
          error: err instanceof Error ? err.message : "Upload failed.",
        };
        throw err;
      } finally {
        completedCount.value = index + 1;
        progress.value = Math.round((completed / files.length) * 100);
      }
    }
    result.value = `Uploaded ${completed} file${completed === 1 ? "" : "s"} successfully to bucket: ${selectedBucket.value}.`;
    uploadQueue.clearFiles();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Upload failed.";
  } finally {
    uploading.value = false;
    currentUploadingFile.value = null;
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }
}

function backToBucket() {
  if (selectedBucket.value) {
    void router.push({
      path: `/buckets/${encodeURIComponent(selectedBucket.value)}`,
      query: {
        ...(selectedProviderId.value ? { provider: selectedProviderId.value } : {}),
        ...(globalPrefix.value ? { prefix: globalPrefix.value } : {}),
      },
    });
  } else {
    void router.push("/");
  }
}

function resetQuerySelection() {
  // Clear route queries to let user manually choose another connection and bucket
  void router.replace({
    path: "/upload",
    query: {}
  });
  selectedProviderId.value = "";
  selectedBucket.value = "";
}
</script>

<template>
  <div class="upload-page-container">
    <!-- Header -->
    <header class="page-title-section">
      <div class="header-text-block">
        <div class="title-with-icon-row">
          <FolderOpen :size="24" class="text-accent" />
          <h1>Upload Wizard</h1>
        </div>
        <p class="subtitle" v-if="selectedBucket">
          Target Storage: <code>{{ selectedProviderId }}</code> / Bucket: <strong>{{ selectedBucket }}</strong>
        </p>
        <p class="subtitle" v-else>Configure and batch upload files natively to any of your storage connections.</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary flex-center" type="button" @click="backToBucket">
          <ArrowLeft :size="14" />
          <span>{{ selectedBucket ? 'Back to Bucket' : 'Cancel' }}</span>
        </button>
      </div>
    </header>

    <!-- Error/Success Notices -->
    <div v-if="error" class="alert error flex-center-left gap-10">
      <AlertTriangle :size="16" />
      <span>{{ error }}</span>
    </div>

    <!-- Wizard Stepper Indicators -->
    <div class="wizard-stepper-bar">
      <div class="step-indicator" :class="{ active: activeStep === 1, completed: activeStep > 1 }">
        <span class="step-num">1</span>
        <span class="step-lbl">Selection & Target</span>
      </div>
      <div class="step-separator-line" />
      <div class="step-indicator" :class="{ active: activeStep === 2, completed: activeStep > 2 }">
        <span class="step-num">2</span>
        <span class="step-lbl">Global Defaults</span>
      </div>
      <div class="step-separator-line" />
      <div class="step-indicator" :class="{ active: activeStep === 3, completed: activeStep > 3 }">
        <span class="step-num">3</span>
        <span class="step-lbl">Overrides & Review</span>
      </div>
      <div class="step-separator-line" />
      <div class="step-indicator" :class="{ active: activeStep === 4, completed: activeStep > 4 }">
        <span class="step-num">4</span>
        <span class="step-lbl">Upload Status</span>
      </div>
    </div>

    <!-- STEP 1: Selection & Queue -->
    <template v-if="activeStep === 1">
      <!-- Target Configuration Banner / Select Card -->
      <section class="dashboard-content-block target-configuration-section mb-24">
        <!-- If already pre-selected from route query parameter -->
        <div v-if="queryBucket && selectedBucket" class="destination-badge-card">
          <div class="badge-icon-wrap">
            <CheckCircle2 :size="20" class="text-success" />
          </div>
          <div class="badge-info-wrap">
            <h3>Destination Configured</h3>
            <p class="flex-center-left gap-10 flex-wrap">
              Targeting connection
              <span class="inline-badge flex-center gap-6">
                <Server :size="11" class="text-accent" />
                <strong>{{ selectedProviderId }}</strong>
              </span>
              · Bucket
              <span class="inline-badge flex-center gap-6">
                <FolderOpen :size="11" class="text-accent" />
                <strong>{{ selectedBucket }}</strong>
              </span>
              <span v-if="prefix" class="flex-center">
                · Directory Path <code>{{ prefix }}</code>
              </span>
            </p>
          </div>
          <button class="btn btn-secondary btn-xs flex-center" type="button" @click="resetQuerySelection">
            <span>Change Target</span>
          </button>
        </div>

        <!-- Manual selection grid: Visually redesigned as interactive visual card flows -->
        <div v-else class="manual-target-card-v2">
          <!-- Step 1: Storage Connection Selection -->
          <div class="selection-flow-step mb-24">
            <div class="step-title-row mb-12">
              <span class="step-badge">1</span>
              <div>
                <h3 class="margin-0 font-bold">Select Storage Connection</h3>
                <p class="subtitle">Choose which active cloud storage connection to target.</p>
              </div>
            </div>

            <!-- Connections Cards Grid -->
            <div v-if="loadingProviders" class="connections-loading">
              <Loader :size="24" class="spin text-accent" />
              <span>Fetching your connections...</span>
            </div>
            
            <div v-else-if="providersList.length === 0" class="connections-empty">
              <AlertTriangle :size="24" class="text-warning" />
              <p>No storage connections configured.</p>
              <NuxtLink to="/providers" class="btn btn-secondary btn-xs mt-8">Configure Connections</NuxtLink>
            </div>

            <div v-else class="connections-container-v2">
              <!-- Connection Search Input -->
              <div class="connection-search-wrapper mb-16">
                <Search :size="14" class="search-input-icon text-muted" />
                <input
                  v-model="providerSearchQuery"
                  type="text"
                  placeholder="Filter connections by name or type..."
                  class="connection-search-input-with-icon"
                />
              </div>

              <!-- Connections Empty State (when filtered out) -->
              <div v-if="filteredProviders.length === 0" class="connections-empty-inline">
                <Server :size="24" class="text-muted" />
                <p class="margin-0">No connections found matching filter.</p>
              </div>

              <!-- Connections Grid -->
              <div v-else class="connections-visual-grid">
                <button
                  v-for="p in filteredProviders"
                  :key="p.id"
                  type="button"
                  class="provider-visual-card"
                  :class="{ 
                    active: selectedProviderId === p.id,
                    'has-error': p.error
                  }"
                  @click="selectProviderItem(p.id)"
                >
                  <div class="provider-card-header">
                    <div class="provider-avatar">
                      <Server :size="16" class="text-accent" />
                    </div>
                    <span class="provider-badge-type">{{ p.type.toUpperCase() }}</span>
                  </div>

                  <div class="provider-card-body">
                    <h4 class="provider-card-name">{{ p.name }}</h4>
                    <p v-if="p.region" class="provider-card-region">{{ p.region }}</p>
                    <p v-else class="provider-card-region">Global Region</p>
                    <code class="provider-card-endpoint">{{ p.endpoint_url || 'Default Endpoint' }}</code>
                  </div>

                  <div class="provider-card-footer">
                    <span v-if="p.error" class="badge-status-error">Error</span>
                    <span v-else class="badge-status-healthy">Ready</span>
                    <div v-if="selectedProviderId === p.id" class="provider-selected-indicator">
                      <Check :size="12" class="text-white" />
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>

          <!-- Step 2: Bucket Selection (Only shown once connection is selected) -->
          <div class="selection-flow-step" :class="{ 'step-locked': !selectedProviderId }">
            <div class="step-title-row mb-12">
              <span class="step-badge">2</span>
              <div>
                <h3 class="margin-0 font-bold">Select Destination Bucket</h3>
                <p class="subtitle">Specify the bucket on the selected connection where your files will be stored.</p>
              </div>
            </div>

            <div v-if="!selectedProviderId" class="bucket-placeholder-lock">
              <div class="lock-icon-stack mb-6">
                <FolderOpen :size="32" class="text-muted" />
                <Lock :size="16" class="lock-badge-overlay text-accent" />
              </div>
              <p class="margin-0">Please select a storage connection above to unlock bucket choices.</p>
            </div>

            <div v-else-if="loadingBuckets" class="buckets-loading">
              <Loader :size="24" class="spin text-accent" />
              <span>Fetching buckets from provider...</span>
            </div>

            <div v-else class="buckets-container-v2">
              <!-- Bucket Search Input -->
              <div class="bucket-search-wrapper mb-16">
                <Search :size="14" class="search-input-icon text-muted" />
                <input
                  v-model="bucketSearchQuery"
                  type="text"
                  placeholder="Filter buckets by name..."
                  class="bucket-search-input-with-icon"
                />
              </div>

              <!-- Buckets Visual Cards Grid -->
              <div v-if="filteredBuckets.length === 0" class="buckets-empty">
                <Folder :size="24" class="text-muted" />
                <p>No buckets found matching filter.</p>
              </div>

              <div v-else class="buckets-visual-grid">
                <button
                  v-for="b in filteredBuckets"
                  :key="b.name"
                  type="button"
                  class="bucket-visual-card"
                  :class="{ active: selectedBucket === b.name }"
                  @click="selectedBucket = b.name"
                >
                  <div class="bucket-card-icon-wrap">
                    <Folder :size="16" class="bucket-icon" />
                  </div>
                  <div class="bucket-card-info">
                    <span class="bucket-card-name">{{ b.name }}</span>
                    <span v-if="b.creation_date" class="bucket-card-date">
                      Created: {{ new Date(b.creation_date).toLocaleDateString() }}
                    </span>
                  </div>
                  <div v-if="selectedBucket === b.name" class="bucket-selected-check">
                    <Check :size="14" class="text-accent" />
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Drag zone -->
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
          <p class="subtitle">Supports uploading multiple files recursively to storage buckets.</p>
        </div>
        <button class="btn btn-primary flex-center" type="button" @click="openPicker">
          <span>Choose Files</span>
        </button>
      </section>

      <!-- Queue Summary -->
      <section class="dashboard-content-block mt-32">
        <div class="block-header border-bottom pb-12 mb-24">
          <div>
            <h2>Selected Files Queue ({{ uploadQueue.files.value.length }})</h2>
            <p>Verify and populate your queue before advancing to settings configuration.</p>
          </div>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>File Name</th>
                <th>Size</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="uploadQueue.files.value.length === 0">
                <td colspan="3" class="empty">Drag files or click choose to populate queue.</td>
              </tr>
              <tr v-for="(file, index) in uploadQueue.files.value" :key="`${file.name}-${file.size}-${index}`">
                <td class="font-bold-text">{{ file.name }}</td>
                <td>{{ formatBytes(file.size) }}</td>
                <td class="actions">
                  <button class="icon-action danger-icon" type="button" @click="uploadQueue.removeFile(index)">
                    <Trash2 :size="14" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Next Button placed at bottom of page -->
        <div class="panel-action-row border-top pt-16 mt-24 flex-right-align">
          <button
            class="btn btn-primary flex-center"
            type="button"
            :disabled="uploadQueue.files.value.length === 0 || !selectedBucket"
            @click="activeStep = 2"
          >
            <span>Next: Configure Defaults</span>
            <ArrowRight :size="14" />
          </button>
        </div>
      </section>
    </template>

    <!-- STEP 2: Global Configuration Defaults -->
    <template v-else-if="activeStep === 2">
      <section class="dashboard-content-block wizard-config-card">
        <div class="block-header border-bottom pb-12 mb-24">
          <div class="flex-center-left gap-10">
            <Sliders :size="18" class="text-accent" />
            <h2 class="margin-0">Global Configuration Defaults</h2>
          </div>
          <p class="subtitle mt-8">These options will apply as defaults to all files in the upload queue.</p>
        </div>

        <div class="wizard-fields-grid">
          <div class="setting-field-row">
            <label for="g-prefix" class="field-lbl">Target Prefix/Directory Path</label>
            <input id="g-prefix" v-model="globalPrefix" class="form-input" placeholder="e.g., raw-uploads/2026/" />
            <p class="small-muted-text mt-4">Where the files will be placed. Defaults to your current path.</p>
          </div>

          <div class="setting-field-row mt-16">
            <label for="g-cache" class="field-lbl">Cache-Control Header</label>
            <input id="g-cache" v-model="globalCacheControl" class="form-input" placeholder="e.g. max-age=31536000" />
            <p class="small-muted-text mt-4">Sets cache threshold. Useful for static assets and web caching.</p>
          </div>

          <!-- Global Metadata Headers -->
          <div class="setting-field-row mt-16">
            <label class="field-lbl">Global Custom Metadata Headers</label>
            <p class="small-muted-text">Add custom key-value headers to be appended on all uploaded objects.</p>
            
            <div class="metadata-add-row mt-8">
              <input v-model="newGlobalKey" class="form-input inline-inp" placeholder="x-amz-meta-key" />
              <input v-model="newGlobalValue" class="form-input inline-inp" placeholder="value" />
              <button class="btn btn-secondary icon-only" type="button" title="Add global header" @click="addGlobalHeader">
                <Plus :size="14" />
              </button>
            </div>

            <!-- List of added global headers -->
            <div class="metadata-tags-list mt-8" v-if="globalMetadata.length > 0">
              <span v-for="(h, idx) in globalMetadata" :key="h.key" class="metadata-tag-pill">
                <code>{{ h.key }}: {{ h.value }}</code>
                <button class="tag-remove-btn" type="button" @click="removeGlobalHeader(idx)"><X :size="10" /></button>
              </span>
            </div>
          </div>
        </div>

        <div class="panel-action-row flex-space-between mt-24 border-top pt-16">
          <button class="btn btn-secondary flex-center" type="button" @click="activeStep = 1">
            <ArrowLeft :size="14" />
            <span>Back to Queue</span>
          </button>
          <button class="btn btn-primary flex-center" type="button" @click="applyGlobalDefaults">
            <span>Next: File-Level Overrides</span>
            <ArrowRight :size="14" />
          </button>
        </div>
      </section>
    </template>

    <!-- STEP 3: Individual File Overrides and Final Review -->
    <template v-else-if="activeStep === 3">
      <div class="wizard-overrides-layout">
        <!-- Files list -->
        <section class="dashboard-content-block file-selection-pane">
          <div class="block-header border-bottom pb-12 mb-16">
            <h3>Files in Queue ({{ uploadQueue.files.value.length }})</h3>
          </div>
          <div class="file-overrides-list">
            <button
              v-for="(file, index) in uploadQueue.files.value"
              :key="`${file.name}-${index}`"
              class="override-file-selector"
              :class="{ active: editingIndex === index }"
              type="button"
              @click="editingIndex = index"
            >
              <FileText :size="16" class="text-accent flex-shrink-0" />
              <div class="file-text-col text-left">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">{{ formatBytes(file.size) }}</span>
              </div>
            </button>
          </div>
        </section>

        <!-- Overrides Config Pane -->
        <section class="dashboard-content-block config-overrides-pane" v-if="activeEditingFile">
          <div class="block-header border-bottom pb-12 mb-16">
            <div class="flex-center-left gap-10">
              <Settings :size="18" class="text-accent" />
              <h3 class="margin-0">Configure Object Settings</h3>
            </div>
            <p class="subtitle mt-8">Customize destination paths, headers, and metadata specifically for this file.</p>
          </div>

          <div class="overrides-form-fields" v-if="activeEditingConfig">
            <div class="setting-field-row">
              <label class="field-lbl">Object Key Destination</label>
              <input
                v-model="activeEditingConfig.targetKey"
                class="form-input font-mono"
              />
              <p class="small-muted-text mt-4">Full path and filename in bucket. Customize this to rename or organize directories.</p>
            </div>

            <div class="setting-field-row mt-16">
              <label class="field-lbl">Cache-Control Header Override</label>
              <input
                v-model="activeEditingConfig.cacheControl"
                class="form-input"
              />
            </div>

            <!-- Custom Metadata Headers override for this specific file -->
            <div class="setting-field-row mt-16">
              <label class="field-lbl">Individual Custom Metadata Headers</label>
              <p class="small-muted-text">Add custom, object-specific metadata headers for this file.</p>

              <div class="metadata-add-row mt-8">
                <input v-model="newLocalKey" class="form-input inline-inp" placeholder="x-amz-meta-key" />
                <input v-model="newLocalValue" class="form-input inline-inp" placeholder="value" />
                <button class="btn btn-secondary icon-only" type="button" title="Add local header" @click="addLocalHeader">
                  <Plus :size="14" />
                </button>
              </div>

              <!-- List of added local headers -->
              <div class="metadata-tags-list mt-8" v-if="activeEditingConfig.metadata.length > 0">
                <span v-for="(h, idx) in activeEditingConfig.metadata" :key="h.key" class="metadata-tag-pill">
                  <code>{{ h.key }}: {{ h.value }}</code>
                  <button class="tag-remove-btn" type="button" @click="removeLocalHeader(idx)"><X :size="10" /></button>
                </span>
              </div>
            </div>
          </div>

          <div class="panel-action-row border-top pt-16 mt-24 flex-space-between">
            <button class="btn btn-secondary flex-center" type="button" @click="activeStep = 2">
              <ArrowLeft :size="14" />
              <span>Back to Defaults</span>
            </button>
            <button class="btn btn-primary flex-center" type="button" @click="startUpload">
              <Upload :size="14" />
              <span>Start Object Upload</span>
            </button>
          </div>
        </section>
      </div>
    </template>

    <!-- STEP 4: Live Uploading Status & Progress -->
    <template v-else-if="activeStep === 4">
      <!-- SUCCESS SUMMARY: Upload completed -->
      <section v-if="result" class="dashboard-content-block upload-success-hero-panel">
        <div class="success-illustration-circle mb-16">
          <CheckCircle2 :size="48" class="text-success" />
        </div>
        <div class="success-text-col text-center">
          <h2>Batch Upload Completed</h2>
          <p class="subtitle mt-8">
            Successfully uploaded <strong>{{ completedCount }}</strong> files in <strong>{{ formattedDuration }}</strong>!
          </p>
          <div class="success-destination-meta-tag mt-12">
            <span>Bucket: <code>{{ selectedBucket }}</code></span>
            <span v-if="globalPrefix"> · Path: <code>{{ globalPrefix }}</code></span>
          </div>
        </div>

        <div class="success-actions-row mt-24">
          <button class="btn btn-primary flex-center" type="button" @click="backToBucket">
            <span>Back to Bucket</span>
            <ArrowRight :size="14" />
          </button>
          <button class="btn btn-secondary flex-center" type="button" @click="activeStep = 1">
            <span>Upload More</span>
          </button>
        </div>
      </section>

      <!-- ACTIVE PROGRESS: Uploading -->
      <section v-else class="dashboard-content-block uploading-progress-hero">
        <div class="block-header border-bottom pb-12 mb-24">
          <div class="flex-center-left gap-10">
            <Loader :size="18" class="spin text-accent" />
            <h2 class="margin-0">Uploading Files to Bucket...</h2>
          </div>
          <span class="elapsed-time-ticker">Duration: {{ formattedDuration }}</span>
        </div>

        <!-- Progress elements -->
        <div class="upload-progress-bar-block mb-24">
          <div class="flex-space-between mb-8">
            <span class="progress-lbl">
              Uploaded {{ completedCount }} of {{ uploadQueue.files.value.length }} files
              <span v-if="currentUploadingFile" class="current-file-indicator">
                · Processing: <code>{{ currentUploadingFile.name }}</code>
              </span>
            </span>
            <span class="progress-pct">{{ progress }}%</span>
          </div>
          <progress class="upload-progress-element" :value="progress" max="100" />
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>File Name</th>
                <th>Custom Key Path</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(file, index) in uploadQueue.files.value" :key="`${file.name}-${index}`">
                <td class="font-bold-text">{{ file.name }}</td>
                <td class="key-cell"><code>{{ fileConfigs[fileId(file, index)]?.targetKey || file.name }}</code></td>
                <td>
                  <span class="provider-status-badge" :class="stateFor(file, index) === 'uploaded' ? 'healthy' : (stateFor(file, index) === 'failed' ? 'unhealthy' : 'info')">
                    <span class="status-dot-indicator" />
                    <span>{{ stateFor(file, index) }}</span>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
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

/* Wizard Stepper Header */
.wizard-stepper-bar {
  display: flex;
  align-items: center;
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  padding: 16px 24px;
  box-shadow: 0 4px 12px rgb(15 23 42 / 2%);
}

.step-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.step-indicator.active {
  color: var(--accent);
  font-weight: 700;
}

.step-indicator.completed {
  color: var(--success);
}

.step-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--border-soft);
  color: var(--muted-strong);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid var(--border);
}

.step-indicator.active .step-num {
  background: var(--accent-soft);
  color: var(--accent);
  border-color: var(--accent);
}

.step-indicator.completed .step-num {
  background: var(--success-soft);
  color: var(--success);
  border-color: var(--success);
}

.step-separator-line {
  flex: 1;
  height: 1px;
  background: var(--border-soft);
  margin: 0 16px;
}

/* Step 1: Drop panel */
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

/* Target configuration Section & Premium Selects */
.target-configuration-section {
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgb(15 23 42 / 2%);
}

.destination-badge-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--success-soft);
  border: 1px solid var(--success-border);
  border-radius: 12px;
  padding: 16px 20px;
}

.badge-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--success-soft-strong);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.badge-info-wrap {
  flex: 1;
}

.badge-info-wrap h3 {
  font-size: 14px;
  font-weight: 800;
  color: var(--success-text);
  margin: 0 0 4px 0;
}

.badge-info-wrap p {
  font-size: 12px;
  color: var(--success-text-subtle);
  margin: 0;
}

.inline-badge {
  display: inline-flex;
  align-items: center;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--text);
}

.btn-xs {
  height: 28px;
  font-size: 11px;
  padding: 0 10px;
  border-radius: 6px;
}

.manual-target-card {
  display: flex;
  flex-direction: column;
}

.premium-selector-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 600px) {
  .premium-selector-grid {
    grid-template-columns: 1fr;
  }
}

button.premium-select-box {
  width: 100%;
  text-align: left;
  font-family: inherit;
  cursor: pointer;
  background: var(--panel-subtle);
  border: 1px solid var(--border);
  color: var(--text);
  font-size: inherit;
  outline: none;
}

button.premium-select-box:hover:not(.disabled) {
  border-color: var(--accent);
  background: var(--panel);
}

button.premium-select-box:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
  background: var(--panel);
}

.premium-select-box {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--panel-subtle);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 16px;
  transition: all 0.15s ease;
}

.premium-select-box.focused {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
  background: var(--panel);
}

.premium-select-box.disabled {
  opacity: 0.55;
  cursor: not-allowed;
  pointer-events: none;
}

.select-box-icon {
  flex-shrink: 0;
}

/* Custom Dropdown Styling */
.custom-dropdown-container {
  position: relative;
  width: 100%;
}

.select-box-selected-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  overflow: hidden;
  text-align: left;
}

.selected-value-main {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected-value-placeholder {
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
}

.selected-value-sub {
  font-size: 11px;
  font-weight: 500;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.select-box-arrow {
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.select-box-arrow.rotated {
  transform: rotate(180deg);
}

.custom-dropdown-list {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
  z-index: 50;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 320px;
  animation: dropdown-slide-up 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes dropdown-slide-up {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-search-wrapper {
  padding: 8px;
  border-bottom: 1px solid var(--border-soft);
  background: var(--panel-subtle);
  position: sticky;
  top: 0;
  z-index: 10;
}

.dropdown-search-input {
  width: 100%;
  height: 32px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--text);
  font-size: 12px;
  outline: none;
  transition: all 0.15s ease;
}

.dropdown-search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent-soft);
}

.dropdown-items-container {
  overflow-y: auto;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* Custom scrollbar for items container */
.dropdown-items-container::-webkit-scrollbar {
  width: 6px;
}

.dropdown-items-container::-webkit-scrollbar-track {
  background: transparent;
}

.dropdown-items-container::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}

.dropdown-items-container::-webkit-scrollbar-thumb:hover {
  background: var(--muted);
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  color: var(--text);
  transition: all 0.12s ease;
  outline: none;
}

.dropdown-item:hover,
.dropdown-item:focus {
  background: var(--border-soft);
  outline: none;
}

.dropdown-item.active {
  background: var(--accent-soft);
}

.dropdown-item .item-icon {
  color: var(--muted);
  flex-shrink: 0;
}

.dropdown-item:hover .item-icon,
.dropdown-item.active .item-icon {
  color: var(--accent);
}

.item-text-container {
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex: 1;
  overflow: hidden;
}

.item-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-item.active .item-title {
  color: var(--accent);
}

.item-subtitle {
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-item:hover .item-subtitle {
  color: var(--muted-strong);
}

.item-check {
  flex-shrink: 0;
  color: var(--accent);
}

.dropdown-no-results {
  padding: 24px 12px;
  text-align: center;
  font-size: 12px;
  color: var(--muted);
}

.badge-status-error {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--danger-soft);
  color: var(--danger);
  border: 1px solid rgba(155, 28, 28, 0.15);
  flex-shrink: 0;
}

/* Transition effects */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.select-box-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.select-box-lbl {
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--muted-strong);
}

/* Step 2: Global Configuration fields */
.wizard-config-card {
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 14px;
  padding: 24px;
}

.wizard-fields-grid {
  max-width: 540px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-field-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-lbl {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
}

.form-input {
  height: 34px;
  background: var(--panel-subtle);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0 12px;
  font-size: 13px;
  color: var(--text);
  outline: none;
  width: 100%;
}

.form-input:focus {
  border-color: var(--accent);
}

/* Metadata tag managers */
.metadata-add-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.metadata-add-row .inline-inp {
  flex: 1;
}

.metadata-tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.metadata-tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--panel-subtle);
  border: 1px solid var(--border-soft);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text);
}

.metadata-tag-pill code {
  font-size: 10px;
  font-family: monospace;
}

.tag-remove-btn {
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: 2px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.1s ease;
}

.tag-remove-btn:hover {
  background: var(--border-soft);
  color: var(--danger);
}

/* Step 3: Overrides Layout split pane */
.wizard-overrides-layout {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 24px;
}

@media (max-width: 900px) {
  .wizard-overrides-layout {
    grid-template-columns: 1fr;
  }
}

.file-selection-pane {
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  padding: 20px;
  max-height: 500px;
  overflow-y: auto;
}

.file-overrides-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.override-file-selector {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  text-align: left;
  gap: 12px;
  padding: 10px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.override-file-selector:hover {
  background: var(--border-soft);
}

.override-file-selector.active {
  background: var(--accent-soft);
  border-color: var(--accent);
}

.file-text-col {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 11px;
  color: var(--muted);
}

.config-overrides-pane {
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  padding: 24px;
}

.overrides-form-fields {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Step 4: Progress elements */
.uploading-progress-hero {
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 14px;
  padding: 24px;
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

/* Provider/Bucket select grid in Step 1 */
.provider-bucket-selector-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 600px) {
  .provider-bucket-selector-row {
    grid-template-columns: 1fr;
  }
}

.select-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Shared UI Primatives */
.font-bold-text {
  font-weight: 600;
  font-size: 13px;
}

.font-mono {
  font-family: monospace;
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

.mb-20 {
  margin-bottom: 20px;
}

.mb-24 {
  margin-bottom: 24px;
}

.mt-8 {
  margin-top: 8px;
}

.mt-12 {
  margin-top: 12px;
}

.mt-16 {
  margin-top: 16px;
}

.mt-24 {
  margin-top: 24px;
}

.mt-32 {
  margin-top: 32px;
}

.pb-12 {
  padding-bottom: 12px;
}

.pb-8 {
  padding-bottom: 8px;
}

.border-bottom {
  border-bottom: 1px solid var(--border-soft);
}

.border-top {
  border-top: 1px solid var(--border-soft);
}

.pt-16 {
  padding-top: 16px;
}

.flex-shrink-0 {
  flex-shrink: 0;
}

.flex-right-align {
  display: flex;
  justify-content: flex-end;
}

.text-left {
  text-align: left;
}

.mb-6 {
  margin-bottom: 6px;
}

.upload-success-hero-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 32px;
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgb(15 23 42 / 2%);
}

.success-illustration-circle {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--success-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 4px var(--success-soft-strong);
}

.success-destination-meta-tag {
  display: inline-flex;
  align-items: center;
  background: var(--panel-subtle);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 12px;
  color: var(--muted-strong);
}

.success-destination-meta-tag code {
  font-size: 11px;
  font-family: monospace;
  background: transparent;
  color: var(--text);
  font-weight: 700;
}

.success-actions-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.elapsed-time-ticker {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted-strong);
  background: var(--panel-subtle);
  border: 1px solid var(--border-soft);
  padding: 4px 10px;
  border-radius: 6px;
}

.current-file-indicator {
  margin-left: 8px;
  color: var(--accent);
  font-weight: 500;
}

.current-file-indicator code {
  font-size: 11px;
}

/* Redesigned Target Selection V2 */
.manual-target-card-v2 {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.selection-flow-step {
  transition: all 0.2s ease;
}

.selection-flow-step.step-locked {
  opacity: 0.55;
  pointer-events: none;
}

.step-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--panel);
  font-size: 13px;
  font-weight: 800;
  flex-shrink: 0;
}

.step-locked .step-badge {
  background: var(--border);
  color: var(--muted);
}

.step-title-row h3 {
  font-size: 15px;
  color: var(--text);
  margin: 0;
}

.step-title-row .subtitle {
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}

/* Connections Visual Cards Grid */
.connections-loading,
.buckets-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 32px;
  background: var(--panel-subtle);
  border: 1px dashed var(--border);
  border-radius: 12px;
  color: var(--muted);
  font-size: 13px;
}

.connections-empty,
.buckets-empty,
.bucket-placeholder-lock {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 16px;
  background: var(--panel-subtle);
  border: 1px dashed var(--border);
  border-radius: 12px;
  color: var(--muted);
  text-align: center;
  font-size: 13px;
}

.connections-visual-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  max-height: 240px;
  overflow-y: auto;
  padding-right: 4px;
}

.provider-visual-card {
  display: flex;
  flex-direction: column;
  background: var(--panel-subtle);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px;
  text-align: left;
  cursor: pointer;
  transition: all 0.18s ease;
  position: relative;
  outline: none;
  min-width: 0;
}

.provider-visual-card:hover {
  border-color: var(--accent);
  background: var(--panel);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgb(15 23 42 / 4%);
}

.provider-visual-card.active {
  border-color: var(--accent);
  background: var(--accent-soft);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.provider-visual-card.active:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
  transform: translateY(-2px);
}

.provider-visual-card.active .provider-card-name {
  color: var(--accent);
}

.provider-visual-card.active .provider-card-region {
  color: var(--accent);
  opacity: 0.85;
}

.provider-visual-card.active .provider-card-endpoint {
  background: color-mix(in srgb, var(--accent) 8%, transparent);
  color: var(--accent);
}

.provider-visual-card.has-error {
  border-color: var(--danger);
}

.provider-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 12px;
}

.provider-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--accent-soft);
}

.provider-visual-card.active .provider-avatar {
  background: var(--accent);
}

.provider-visual-card.active .provider-avatar svg {
  color: var(--panel) !important;
}

.provider-badge-type {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--border-soft);
  color: var(--muted-strong);
}

.provider-visual-card.active .provider-badge-type {
  background: var(--panel);
  color: var(--accent);
  border: 1px solid rgba(23, 107, 135, 0.15);
}

.provider-card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
  min-width: 0;
  overflow: hidden;
}

.provider-card-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.provider-card-region {
  font-size: 11px;
  color: var(--muted);
  margin: 0;
}

.provider-card-endpoint {
  font-size: 10px;
  color: var(--muted);
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  background: var(--code-bg);
  padding: 1px 4px;
  border-radius: 4px;
}

.provider-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.badge-status-healthy {
  font-size: 10px;
  font-weight: 700;
  color: var(--success);
  background: var(--success-soft);
  padding: 1px 6px;
  border-radius: 4px;
}

.provider-selected-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent);
}

/* Unified Symmetrical Step Containers V2 */
.connections-container-v2,
.buckets-container-v2 {
  background: var(--panel-subtle);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
}

.connection-search-wrapper,
.bucket-search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.lock-icon-stack {
  position: relative;
  display: inline-flex;
}

.lock-badge-overlay {
  position: absolute;
  bottom: -4px;
  right: -4px;
  background: var(--panel);
  border: 1.5px solid var(--border-soft);
  border-radius: 50%;
  padding: 2px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.search-input-icon {
  position: absolute;
  left: 12px;
  pointer-events: none;
}

.connection-search-input-with-icon,
.bucket-search-input-with-icon {
  width: 100%;
  height: 36px;
  padding: 0 14px 0 34px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--text);
  font-size: 13px;
  outline: none;
  transition: all 0.15s ease;
}

.connection-search-input-with-icon:focus,
.bucket-search-input-with-icon:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.connections-visual-grid,
.buckets-visual-grid {
  display: grid;
  gap: 12px;
  max-height: 240px;
  overflow-y: auto;
  padding-right: 4px;
}

.connections-visual-grid {
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
}

.buckets-visual-grid {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

/* Custom scrollbars for grids */
.connections-visual-grid::-webkit-scrollbar,
.buckets-visual-grid::-webkit-scrollbar {
  width: 6px;
}

.connections-visual-grid::-webkit-scrollbar-track,
.buckets-visual-grid::-webkit-scrollbar-track {
  background: transparent;
}

.connections-visual-grid::-webkit-scrollbar-thumb,
.buckets-visual-grid::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}

.connections-visual-grid::-webkit-scrollbar-thumb:hover,
.buckets-visual-grid::-webkit-scrollbar-thumb:hover {
  background: var(--muted);
}

.connections-empty-inline {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 16px;
  color: var(--muted);
  text-align: center;
  font-size: 13px;
}

.bucket-visual-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
  text-align: left;
  outline: none;
}

.bucket-visual-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}

.bucket-visual-card.active {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.bucket-card-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--border-soft);
  color: var(--muted);
}

.bucket-visual-card.active .bucket-card-icon-wrap {
  background: var(--accent);
  color: var(--panel);
}

.bucket-card-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.bucket-card-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bucket-visual-card.active .bucket-card-name {
  color: var(--accent);
}

.bucket-card-date {
  font-size: 10px;
  color: var(--muted);
}

.bucket-selected-check {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  flex-shrink: 0;
}
</style>
