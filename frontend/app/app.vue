<script setup lang="ts">
import { ref, onMounted } from "vue";
import Sidebar from "./components/layout/Sidebar.vue";
import TopNav from "./components/layout/TopNav.vue";
import { useObjectLensApi } from "./composables/useObjectLensApi";
import { Lock, LogIn, AlertCircle, ShieldAlert } from "@lucide/vue";

const api = useObjectLensApi();
const isCheckingAuth = ref(true);
const showLoginOverlay = ref(false);

const username = ref("");
const password = ref("");
const loginError = ref("");
const loginLoading = ref(false);

async function checkAuth() {
  isCheckingAuth.value = true;
  try {
    // Attempt a light check to see if we are authorized or if auth is disabled
    await api.listProviders();
    showLoginOverlay.value = false;
  } catch (err) {
    const errMsg = String(err);
    // If we receive unauthorized, trigger the login screen
    if (errMsg.includes("credentials") || errMsg.includes("Unauthorized") || errMsg.includes("401")) {
      showLoginOverlay.value = true;
    }
  } finally {
    isCheckingAuth.value = false;
  }
}

async function handleLogin(e: Event) {
  e.preventDefault();
  if (!username.value.trim() || !password.value.trim()) {
    loginError.value = "Username and password are required.";
    return;
  }

  loginError.value = "";
  loginLoading.value = true;
  try {
    await api.login(username.value.trim(), password.value);
    showLoginOverlay.value = false;
    // Reload window to cleanly refresh all active Nuxt page states
    window.location.reload();
  } catch (err) {
    loginError.value = "Invalid username or password configuration.";
  } finally {
    loginLoading.value = false;
  }
}

onMounted(() => {
  checkAuth();
});
</script>

<template>
  <!-- Full Screen Initial Auth Validation Loader -->
  <div v-if="isCheckingAuth" class="auth-initial-spinner">
    <div class="spinner-circle"></div>
    <p>Securing connection...</p>
  </div>

  <!-- Main Authenticated Console Interface -->
  <div v-else-if="!showLoginOverlay" class="app-layout">
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

  <!-- Gorgeous High-Fidelity Login Overlay -->
  <div v-else class="login-fullscreen-overlay">
    <div class="login-card-container">
      <header class="login-card-header">
        <div class="login-logo-avatar">
          <Lock :size="24" class="text-accent" />
        </div>
        <h2>Sign in to ObjectLens</h2>
        <p>Role-Based Access Control (RBAC) is active on this deployment.</p>
      </header>

      <form class="login-form-body" @submit="handleLogin">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="input-full"
            placeholder="e.g. admin"
            required
            autofocus
            :disabled="loginLoading"
          />
        </div>

        <div class="form-group mt-16">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="input-full"
            placeholder="••••••••••••"
            required
            :disabled="loginLoading"
          />
        </div>

        <div v-if="loginError" class="alert error mt-16 flex-center gap-8">
          <AlertCircle :size="15" />
          <span>{{ loginError }}</span>
        </div>

        <button type="submit" class="btn btn-primary w-full mt-24 flex-center gap-8" :disabled="loginLoading">
          <LogIn :size="16" />
          <span>{{ loginLoading ? "Signing In..." : "Sign In" }}</span>
        </button>
      </form>

      <footer class="login-card-footer mt-24">
        <ShieldAlert :size="12" class="text-muted" />
        <span>Managed via local YAML manifests in <code>data/users/</code></span>
      </footer>
    </div>
  </div>
</template>

<style>
/* CSS styles for global overlays and auth */
.auth-initial-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: var(--bg);
  gap: 16px;
  color: var(--text-muted);
}

.spinner-circle {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-soft);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin-auth 0.8s linear infinite;
}

@keyframes spin-auth {
  to { transform: rotate(360deg); }
}

.login-fullscreen-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg);
  padding: 24px;
}

.login-card-container {
  width: 100%;
  max-width: 400px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

.login-logo-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: rgba(23, 107, 135, 0.08);
  margin: 0 auto 16px;
}

.login-card-header {
  text-align: center;
  margin-bottom: 24px;
}

.login-card-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 6px 0;
}

.login-card-header p {
  font-size: 13px;
  color: var(--muted);
  margin: 0;
  line-height: 1.4;
}

.login-form-body {
  display: flex;
  flex-direction: column;
}

.login-card-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 11px;
  color: var(--muted);
  border-top: 1px solid var(--border-soft);
  padding-top: 16px;
}
</style>
