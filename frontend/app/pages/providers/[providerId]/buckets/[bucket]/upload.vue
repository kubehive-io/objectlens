<script setup lang="ts">
const route = useRoute();

await navigateTo({
  path: `/buckets/${encodeURIComponent(String(route.params.bucket || ""))}/upload`,
  query: {
    provider: String(route.params.providerId || ""),
    ...(route.query.prefix ? { prefix: String(route.query.prefix) } : {}),
  },
});
</script>

<template>
  <main class="app-shell">
    <div class="empty-panel">Opening upload page...</div>
  </main>
</template>
