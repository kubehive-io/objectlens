<script setup lang="ts">
import type { ProviderConnection, ProviderStatus } from "../composables/useObjectLensApi";
import { useObjectLensApi } from "../composables/useObjectLensApi";

const api = useObjectLensApi();

const providers = ref<ProviderConnection[]>([]);
const bucketCounts = ref<Record<string, number>>({});
const statuses = ref<Record<string, ProviderStatus>>({});
const backendHealthy = ref(false);
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  loading.value = true;
  error.value = "";
  try {
    const health = await api.health();
    backendHealthy.value = health.status === "ok";
    providers.value = await api.listProviders();
    for (const provider of providers.value) {
      try {
        const status = await api.providerStatus(provider.id);
        statuses.value[provider.id] = status;
        bucketCounts.value[provider.id] = status.visible_bucket_count;
      } catch {
        bucketCounts.value[provider.id] = 0;
      }
    }
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
          <h2>Provider connections</h2>
          <p>Select the object-storage connection you want to browse.</p>
        </div>
      </div>

      <div v-if="loading" class="empty-panel">Loading provider connections...</div>
      <div v-else-if="providers.length === 0" class="empty-panel">
        No provider connections are configured.
      </div>
      <div v-else class="bucket-grid">
        <article
          v-for="provider in providers"
          :key="provider.id"
          class="bucket-card"
        >
          <div class="card-title-row">
            <span class="label">{{ provider.type }}</span>
            <span
              class="status-dot"
              :class="statuses[provider.id]?.status === 'healthy' ? 'healthy-dot' : 'unhealthy-dot'"
            />
          </div>
          <strong>{{ provider.name }}</strong>
          <p>{{ provider.description || "No description provided." }}</p>
          <p>{{ provider.endpoint_url || provider.region }}</p>
          <p>{{ provider.region }} · {{ bucketCounts[provider.id] ?? 0 }} visible buckets</p>
          <div class="tag-row">
            <span v-for="tag in provider.tags || []" :key="tag" class="tag-pill">{{ tag }}</span>
          </div>
          <div class="card-actions">
            <NuxtLink class="text-button" :to="`/providers/${encodeURIComponent(provider.id)}`">Open</NuxtLink>
            <NuxtLink class="text-button" :to="`/providers/${encodeURIComponent(provider.id)}/details`">
              Details
            </NuxtLink>
            <NuxtLink class="text-button" :to="`/providers/${encodeURIComponent(provider.id)}/details#settings`">
              Settings
            </NuxtLink>
          </div>
        </article>
      </div>
    </section>
  </main>
</template>
