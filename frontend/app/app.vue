<script setup lang="ts">
import Sidebar from "./components/layout/Sidebar.vue";
import TopNav from "./components/layout/TopNav.vue";
</script>

<template>
  <div class="app-layout">
    <!-- Consolidated Sidebar Navigation -->
    <Sidebar />

    <div class="main-workspace">
      <!-- Consolidated Top Navigation Bar -->
      <TopNav />

      <!-- Scrollable Main Page Viewport -->
      <main class="workspace-viewport">
        <NuxtPage />
      </main>
    </div>
  </div>
</template>
