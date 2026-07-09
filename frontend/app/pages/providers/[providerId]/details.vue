<script setup lang="ts">
import type {
  ProviderConnection,
  ProviderSettings,
  ProviderStatus,
} from "../../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../../composables/useObjectLensApi";

const route = useRoute();
const api = useObjectLensApi();

const providerId = computed(() => String(route.params.providerId || ""));
const provider = ref<ProviderConnection | null>(null);
const status = ref<ProviderStatus | null>(null);
const settings = ref<ProviderSettings | null>(null);
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  try {
    provider.value = await api.providerConnection(providerId.value);
    status.value = await api.providerStatus(providerId.value);
    settings.value = await api.providerSettings(providerId.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load provider details.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <main class="app-shell">
    <nav class="breadcrumb real-breadcrumb" aria-label="Provider details path">
      <NuxtLink to="/">Providers</NuxtLink>
      <span>›</span>
      <NuxtLink :to="`/providers/${encodeURIComponent(providerId)}`">
        {{ provider?.name || providerId }}
      </NuxtLink>
      <span>›</span>
      <span>Details</span>
    </nav>

    <section class="topbar compact-topbar">
      <div>
        <h1>{{ provider?.name || providerId }}</h1>
        <p>{{ provider?.description || "Provider connection details and safe runtime settings." }}</p>
      </div>
      <NuxtLink class="text-button" :to="`/providers/${encodeURIComponent(providerId)}`">Open buckets</NuxtLink>
    </section>

    <div v-if="loading" class="empty-panel">Loading provider details...</div>
    <div v-else-if="error" class="alert error">{{ error }}</div>

    <template v-else>
      <section class="status-grid compact-grid">
        <article class="status-card">
          <span class="label">Type</span>
          <strong>{{ provider?.display_name }}</strong>
          <p>{{ provider?.type }}</p>
        </article>
        <article class="status-card">
          <span class="label">Status</span>
          <strong :class="status?.status === 'healthy' ? 'healthy' : 'unhealthy'">
            {{ status?.status }}
          </strong>
          <p>{{ status?.message }}</p>
        </article>
        <article class="status-card">
          <span class="label">Visible buckets</span>
          <strong>{{ status?.visible_bucket_count ?? 0 }}</strong>
          <p>Can list buckets: {{ status?.can_list_buckets ? "yes" : "no" }}</p>
        </article>
      </section>

      <section class="status-grid">
        <article class="status-card">
          <span class="label">Connection</span>
          <dl>
            <div>
              <dt>Endpoint</dt>
              <dd>{{ provider?.endpoint_url || "AWS/default endpoint" }}</dd>
            </div>
            <div>
              <dt>Region</dt>
              <dd>{{ provider?.region }}</dd>
            </div>
            <div>
              <dt>Default bucket</dt>
              <dd>{{ provider?.default_bucket || "No default bucket" }}</dd>
            </div>
            <div>
              <dt>Verify SSL</dt>
              <dd>{{ provider?.verify_ssl ? "true" : "false" }}</dd>
            </div>
          </dl>
          <div class="tag-row">
            <span v-for="tag in provider?.tags || []" :key="tag" class="tag-pill">{{ tag }}</span>
          </div>
        </article>

        <article id="settings" class="status-card">
          <span class="label">Safe settings</span>
          <dl>
            <div>
              <dt>Config source</dt>
              <dd>{{ settings?.config_source }}</dd>
            </div>
            <div>
              <dt>Secrets loaded</dt>
              <dd>{{ settings?.secrets_loaded ? "yes" : "no" }}</dd>
            </div>
            <div>
              <dt>Secret fields</dt>
              <dd>{{ settings?.secret_fields.join(", ") }}</dd>
            </div>
            <div>
              <dt>Editable</dt>
              <dd>{{ settings?.editable ? "yes" : "no" }}</dd>
            </div>
          </dl>
        </article>
      </section>
    </template>
  </main>
</template>
