<script setup lang="ts">
import type { Bucket, ProviderConnection } from "../../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../../composables/useObjectLensApi";

const route = useRoute();
const api = useObjectLensApi();

const providerId = computed(() => String(route.params.providerId || ""));
const provider = ref<ProviderConnection | null>(null);
const buckets = ref<Bucket[]>([]);
const loading = ref(true);
const error = ref("");

function formatDate(value?: string | null) {
  if (!value) return "Creation date unavailable";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

onMounted(async () => {
  try {
    provider.value = await api.providerConnection(providerId.value);
    buckets.value = (await api.listProviderBuckets(providerId.value)).buckets;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load provider.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <main class="app-shell">
    <nav class="breadcrumb real-breadcrumb" aria-label="Provider path">
      <NuxtLink to="/">Providers</NuxtLink>
      <span>›</span>
      <span>{{ provider?.name || providerId }}</span>
    </nav>

    <section class="topbar compact-topbar">
      <div>
        <h1>{{ provider?.name || providerId }}</h1>
        <p>{{ provider?.display_name }} · {{ provider?.region }}</p>
      </div>
    </section>

    <div v-if="error" class="alert error">{{ error }}</div>

    <section class="status-grid">
      <article class="status-card">
        <span class="label">Provider type</span>
        <strong>{{ provider?.type }}</strong>
        <p>{{ provider?.endpoint_url || "AWS/default endpoint" }}</p>
      </article>
      <article class="status-card">
        <span class="label">Visible buckets</span>
        <strong>{{ buckets.length }}</strong>
        <p>Buckets returned by {{ provider?.name || "this provider" }} credentials.</p>
      </article>
    </section>

    <section class="section-block">
      <div class="section-heading">
        <div>
          <h2>Visible buckets</h2>
          <p>Only buckets available to this provider connection are shown.</p>
        </div>
      </div>
      <div v-if="loading" class="empty-panel">Loading buckets...</div>
      <div v-else-if="buckets.length === 0" class="empty-panel">No buckets visible.</div>
      <div v-else class="bucket-grid">
        <NuxtLink
          v-for="bucket in buckets"
          :key="bucket.name"
          class="bucket-card"
          :to="`/buckets/${encodeURIComponent(bucket.name)}?provider=${encodeURIComponent(providerId)}`"
        >
          <span class="label">Bucket</span>
          <strong>{{ bucket.name }}</strong>
          <p>{{ formatDate(bucket.creation_date) }}</p>
        </NuxtLink>
      </div>
    </section>
  </main>
</template>
