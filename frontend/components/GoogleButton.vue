<!--
  "Sign in with Google" button (Google Identity Services).
  Usage: <GoogleButton :client-id="id" text="signup_with" @credential="..." />
  Emits `credential` with the Google ID token; the backend verifies it.
  Until a client id is configured (or if Google can't be loaded) it shows a
  look-alike button that emits `error` with an explanation when clicked.
-->
<template>
  <div class="google">
    <div v-if="ready" ref="el" class="google__btn"></div>
    <button v-else class="fallback" type="button" @click="emit('error', fallbackMessage)">
      <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
        <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
        <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
        <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
        <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
      </svg>
      {{ text === 'signup_with' ? 'Sign up with Google' : 'Sign in with Google' }}
    </button>
    <div class="divider"><span>or</span></div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

const props = defineProps({
  clientId: { type: String, default: '' },
  // Google's button label: 'signin_with' | 'signup_with' | 'continue_with'
  text: { type: String, default: 'signin_with' },
});
const emit = defineEmits(['credential', 'error']);

const el = ref(null);
const ready = ref(false); // true once Google's own button can be rendered
const fallbackMessage = ref(
  props.clientId
    ? 'Could not load Google sign in. Check your connection and try again.'
    : 'Google sign in is not set up yet (GOOGLE_CLIENT_ID is missing on the server).',
);

function loadGis() {
  if (window.google?.accounts?.id) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = Object.assign(document.createElement('script'), {
      src: 'https://accounts.google.com/gsi/client',
      async: true,
      onload: resolve,
      onerror: reject,
    });
    document.head.appendChild(script);
  });
}

function render() {
  if (!el.value || !window.google?.accounts?.id) return;
  el.value.innerHTML = '';
  window.google.accounts.id.renderButton(el.value, {
    theme: 'outline',
    size: 'large',
    shape: 'rectangular',
    text: props.text,
    logo_alignment: 'center',
    width: Math.min(400, el.value.clientWidth || 320), // Google caps it at 400px
  });
}

onMounted(async () => {
  if (!props.clientId) return;
  try {
    await loadGis();
  } catch {
    return; // keep the fallback button, which explains the problem
  }
  window.google.accounts.id.initialize({
    client_id: props.clientId,
    callback: (response) => emit('credential', response.credential),
    ux_mode: 'popup',
  });
  ready.value = true;
  await nextTick();
  render();
});

onBeforeUnmount(() => window.google?.accounts?.id?.cancel());

watch(() => props.text, render);
</script>

<style scoped>
.google__btn {
  display: flex;
  justify-content: center;
  min-height: 44px;
}

.fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  height: 44px;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  color: #3c4043;
  background: #fff;
  border: 1px solid #dadce0;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.fallback:hover {
  background: #f8faff;
  border-color: #d2e3fc;
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 18px 0;
  font-size: 13px;
  color: var(--muted);
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}
</style>
