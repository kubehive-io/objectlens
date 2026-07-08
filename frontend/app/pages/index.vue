<script setup lang="ts">
import type { Bucket, ProviderInfo } from "../composables/useObjectLensApi";
import { useObjectLensApi } from "../composables/useObjectLensApi";

const api = useObjectLensApi();

const buckets = ref<Bucket[]>([]);
const provider = ref<ProviderInfo | null>(null);
const backendHealthy = ref(false);
const loading = ref(true);
const error = ref("");

function formatDate(value?: string | null) {
  if (!value) return "Creation date unavailable";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

onMounted(async () => {
  loading.value = true;
  error.value = "";
  try {
    const health = await api.health();
    backendHealthy.value = health.status === "ok";
    provider.value = await api.provider();
    buckets.value = (await api.listBuckets()).buckets;
  } catch (err) {
    backendHealthy.value = false;
    error.value =
      err instanceof Error
        ? err.message
        : "ObjectLens backend is unavailable. Start it with `just backend` or `just dev`.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <main class="app-shell">
    <section class="topbar">
      <div>
        <h1>ObjectLens</h1>
        <p>Fast object access for Kubernetes and Ceph</p>
      </div>
    </section>

    <section class="status-grid">
      <article class="status-card">
        <span class="label">Provider</span>
        <strong>{{ provider?.display_name || "Ceph RGW" }}</strong>
        <dl>
          <div>
            <dt>Endpoint URL</dt>
            <dd>{{ provider?.endpoint_url || "Not configured" }}</dd>
          </div>
          <div>
            <dt>Default bucket</dt>
            <dd>{{ provider?.default_bucket || "No default bucket" }}</dd>
          </div>
        </dl>
      </article>

      <article class="status-card">
        <span class="label">Backend health</span>
        <strong :class="backendHealthy ? 'healthy' : 'unhealthy'">
          {{ backendHealthy ? "Online" : "Unavailable" }}
        </strong>
        <p>
          {{ backendHealthy ? "FastAPI is reachable on the configured API URL." : "Start the backend with just dev." }}
        </p>
      </article>
    </section>

    <section v-if="error" class="backend-empty">
      <h2>ObjectLens backend is not reachable</h2>
      <p>
        The dashboard is ready, but it cannot reach the API. Start the backend with
        <code>just backend</code> or run the full stack with <code>just dev</code>.
      </p>
      <p class="error-text">{{ error }}</p>
    </section>

    <section v-else class="section-block">
      <div class="section-heading">
        <div>
          <h2>Visible buckets</h2>
          <p>Buckets are returned from the current Ceph RGW credentials.</p>
        </div>
      </div>

      <div v-if="loading" class="empty-panel">Loading visible buckets...</div>
      <div v-else-if="buckets.length === 0" class="empty-panel">
        No buckets are visible to the configured provider credentials.
      </div>
      <div v-else class="bucket-grid">
        <NuxtLink
          v-for="bucket in buckets"
          :key="bucket.name"
          class="bucket-card"
          :to="`/buckets/${encodeURIComponent(bucket.name)}`"
        >
          <span class="label">Bucket</span>
          <strong>{{ bucket.name }}</strong>
          <p>{{ formatDate(bucket.creation_date) }}</p>
        </NuxtLink>
      </div>
    </section>
  </main>
</template>
