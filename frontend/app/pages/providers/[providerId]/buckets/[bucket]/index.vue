<script setup lang="ts">
import { navigateTo, useRoute } from "#app";

const route = useRoute();
const providerId = route.params.providerId as string;
const bucket = route.params.bucket as string;
const prefix = (route.query.prefix as string) || "";

// Redirect to the unified bucket browser
navigateTo(`/buckets/${encodeURIComponent(bucket)}?provider=${encodeURIComponent(providerId)}&prefix=${encodeURIComponent(prefix)}`, {
  replace: true,
});
</script>

<template>
  <div class="empty-panel">Redirecting to unified bucket view...</div>
</template>
