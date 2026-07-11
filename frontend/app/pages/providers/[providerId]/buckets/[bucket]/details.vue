<script setup lang="ts">
import { navigateTo, useRoute } from "#app";

const route = useRoute();
const providerId = route.params.providerId as string;
const bucket = route.params.bucket as string;

// Redirect to the unified bucket details
navigateTo(`/buckets/${encodeURIComponent(bucket)}/details?provider=${encodeURIComponent(providerId)}`, {
  replace: true,
});
</script>

<template>
  <div class="empty-panel">Redirecting to unified bucket details view...</div>
</template>
