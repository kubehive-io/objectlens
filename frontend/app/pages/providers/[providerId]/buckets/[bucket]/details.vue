<script setup lang="ts">
import type {
  BucketDetails,
  BucketSettings,
  ProviderConnection,
} from "../../../../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../../../../composables/useObjectLensApi";

const route = useRoute();
const api = useObjectLensApi();

const providerId = computed(() => String(route.params.providerId || ""));
const bucket = computed(() => String(route.params.bucket || ""));
const provider = ref<ProviderConnection | null>(null);
const details = ref<BucketDetails | null>(null);
const settings = ref<BucketSettings | null>(null);
const loading = ref(true);
const error = ref("");

function formatBytes(value?: number | null) {
  if (value === null || value === undefined) return "0 B";
  if (value === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value?: string | null) {
  if (!value) return "unknown";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

onMounted(async () => {
  try {
    provider.value = await api.providerConnection(providerId.value);
    details.value = await api.providerBucketDetails(providerId.value, bucket.value);
    settings.value = await api.providerBucketSettings(providerId.value, bucket.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load bucket details.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <main class="app-shell">
    <nav class="breadcrumb real-breadcrumb" aria-label="Bucket details path">
      <NuxtLink to="/">Providers</NuxtLink>
      <span>›</span>
      <NuxtLink :to="`/providers/${encodeURIComponent(providerId)}`">
        {{ provider?.name || providerId }}
      </NuxtLink>
      <span>›</span>
      <NuxtLink :to="`/buckets/${encodeURIComponent(bucket)}?provider=${encodeURIComponent(providerId)}`">
        {{ bucket }}
      </NuxtLink>
      <span>›</span>
      <span>Details</span>
    </nav>

    <section class="topbar compact-topbar">
      <div>
        <h1>{{ bucket }}</h1>
        <p>Provider: {{ provider?.name || providerId }}</p>
      </div>
      <NuxtLink
        class="text-button"
        :to="`/buckets/${encodeURIComponent(bucket)}?provider=${encodeURIComponent(providerId)}`"
      >
        Open browser
      </NuxtLink>
    </section>

    <div v-if="loading" class="empty-panel">Loading bucket details...</div>
    <div v-else-if="error" class="alert error">{{ error }}</div>

    <template v-else>
      <section class="status-grid compact-grid">
        <article class="status-card">
          <span class="label">Indexed objects</span>
          <strong>{{ details?.indexed_object_count ?? 0 }}</strong>
          <p>{{ formatBytes(details?.indexed_total_size) }}</p>
        </article>
        <article class="status-card">
          <span class="label">Last indexed</span>
          <strong>{{ formatDate(details?.last_indexed_at) }}</strong>
          <p>Creation: {{ formatDate(details?.creation_date) }}</p>
        </article>
        <article class="status-card">
          <span class="label">Settings</span>
          <strong>{{ settings?.versioning }}</strong>
          <p>Lifecycle: {{ settings?.lifecycle }} · Policy: {{ settings?.policy }}</p>
        </article>
      </section>

      <section class="insight-grid">
        <article class="status-card">
          <span class="label">Recent objects</span>
          <ul class="object-list">
            <li v-for="object in details?.recent_objects || []" :key="object.key">
              <span>{{ object.key }}</span>
              <small>{{ formatDate(object.last_modified) }}</small>
            </li>
            <li v-if="!details?.recent_objects?.length" class="muted">No recent indexed objects.</li>
          </ul>
        </article>
        <article class="status-card">
          <span class="label">Largest objects</span>
          <ul class="object-list">
            <li v-for="object in details?.largest_objects || []" :key="object.key">
              <span>{{ object.key }}</span>
              <small>{{ formatBytes(object.size) }}</small>
            </li>
            <li v-if="!details?.largest_objects?.length" class="muted">No indexed object sizes.</li>
          </ul>
        </article>
        <article class="status-card">
          <span class="label">Top prefixes</span>
          <ul class="object-list">
            <li v-for="item in details?.top_prefixes || []" :key="item.prefix">
              <span>{{ item.prefix }}</span>
              <small>{{ item.object_count }} objects · {{ formatBytes(item.total_size) }}</small>
            </li>
            <li v-if="!details?.top_prefixes?.length" class="muted">No prefixes indexed.</li>
          </ul>
        </article>
      </section>
    </template>
  </main>
</template>
