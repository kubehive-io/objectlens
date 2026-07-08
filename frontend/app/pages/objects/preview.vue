<script setup lang="ts">
import type { ObjectPreview } from "../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../composables/useObjectLensApi";

const route = useRoute();
const api = useObjectLensApi();

const bucket = computed(() => String(route.query.bucket || ""));
const key = computed(() => String(route.query.key || ""));
const preview = ref<ObjectPreview | null>(null);
const loading = ref(true);
const error = ref("");

function valueText(value: unknown) {
  if (value === null || value === undefined) return "";
  return String(value);
}

onMounted(async () => {
  loading.value = true;
  error.value = "";
  try {
    preview.value = await api.objectPreview(bucket.value, key.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Preview failed.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <main class="app-shell">
    <section class="topbar">
      <div>
        <NuxtLink class="back-link" :to="`/buckets/${encodeURIComponent(bucket)}`">Bucket details</NuxtLink>
        <h1>Object preview</h1>
        <p>{{ key }}</p>
      </div>
    </section>

    <div v-if="loading" class="empty-panel">Loading preview...</div>
    <div v-else-if="error" class="alert error">{{ error }}</div>

    <section v-else-if="preview" class="preview-panel">
      <div class="preview-meta">
        <span class="label">{{ preview.preview_type }}</span>
        <p>Preview reads only a limited amount of the object.</p>
        <p v-if="preview.reason" class="muted">{{ preview.reason }}</p>
      </div>

      <pre v-if="preview.preview_type === 'json'" class="code-preview">{{ preview.text }}</pre>

      <div v-else-if="preview.preview_type === 'csv'" class="table-wrap">
        <table>
          <thead>
            <tr>
              <th v-for="header in preview.headers || []" :key="header">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in preview.rows || []" :key="index">
              <td v-for="header in preview.headers || []" :key="header">
                {{ valueText(row[header]) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else-if="preview.preview_type === 'parquet'" class="preview-stack">
        <h2>Schema</h2>
        <ul class="object-list">
          <li v-for="field in preview.schema_fields || []" :key="field.name">
            <span>{{ field.name }}</span>
            <small>{{ field.type }}</small>
          </li>
        </ul>
        <pre class="code-preview">{{ JSON.stringify(preview.rows || [], null, 2) }}</pre>
      </div>

      <div v-else-if="preview.preview_type === 'image'" class="image-preview">
        <img v-if="preview.image_url" :src="preview.image_url" :alt="key" />
      </div>

      <div v-else class="empty-panel">
        <h2>Preview unsupported</h2>
        <p>{{ preview.reason || "This object type cannot be previewed yet." }}</p>
      </div>

      <a v-if="preview.download_url" class="primary link-button" :href="preview.download_url" target="_blank" rel="noreferrer">
        Download object
      </a>
    </section>
  </main>
</template>
