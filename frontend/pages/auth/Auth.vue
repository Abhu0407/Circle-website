<template>
  <AuthLayout>
    <GoogleButton
      :client-id="googleClientId"
      :text="mode === 'signup' ? 'signup_with' : 'signin_with'"
      @credential="submitGoogle"
      @error="(text) => (message = text)"
    />

    <Transition name="fade" mode="out-in">
      <!-- Sign in -->
      <form v-if="mode === 'signin'" key="signin" novalidate @submit.prevent="submitSignIn">
        <p v-if="message" class="alert" role="alert">{{ message }}</p>

        <FormField
          id="identifier"
          v-model="signin.identifier"
          label="Username or email"
          placeholder="you@example.com"
          autocomplete="username"
          required
          :error="fieldErrors.identifier"
        />
        <FormField
          id="password"
          v-model="signin.password"
          type="password"
          label="Password"
          placeholder="Your password"
          autocomplete="current-password"
          required
          :error="fieldErrors.password"
        />

        <button class="btn" type="submit" :disabled="loading">
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <!-- Sign up -->
      <form v-else key="signup" novalidate @submit.prevent="submitSignUp">
        <p v-if="message" class="alert" role="alert">{{ message }}</p>

        <FormField
          id="username"
          v-model="signup.username"
          label="Username"
          placeholder="e.g. alex_vibes"
          autocomplete="username"
          required
          :error="fieldErrors.username"
        />
        <FormField
          id="email"
          v-model="signup.email"
          type="email"
          label="Email"
          placeholder="you@example.com"
          autocomplete="email"
          required
          :error="fieldErrors.email"
        />
        <FormField
          id="new-password"
          v-model="signup.password"
          type="password"
          label="Password"
          placeholder="At least 8 characters"
          autocomplete="new-password"
          required
          :error="fieldErrors.password"
        />

        <button class="btn" type="submit" :disabled="loading">
          {{ loading ? 'Creating account…' : 'Create account' }}
        </button>
      </form>
    </Transition>

    <template #footer>
      <template v-if="mode === 'signin'">
        Don't have an account?
        <a :href="signupUrl" @click.prevent="switchTo('signup')">Sign up</a>
      </template>
      <template v-else>
        Already have an account?
        <a :href="signinUrl" @click.prevent="switchTo('signin')">Sign in</a>
      </template>
    </template>
  </AuthLayout>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import AuthLayout from '../../components/AuthLayout.vue';
import FormField from '../../components/FormField.vue';
import GoogleButton from '../../components/GoogleButton.vue';
import { apiPost, parseErrors } from '../../api.mjs';

// Props come from AuthPageView.get_page_props() in Django.
const props = defineProps({
  mode: { type: String, default: 'signin' }, // 'signin' | 'signup'
  signinApi: { type: String, required: true },
  signupApi: { type: String, required: true },
  googleApi: { type: String, required: true },
  googleClientId: { type: String, default: '' }, // empty = Google button hidden
  signinUrl: { type: String, required: true },
  signupUrl: { type: String, required: true },
  nextUrl: { type: String, default: '/' },
});

const mode = ref(props.mode === 'signup' ? 'signup' : 'signin');

const signin = reactive({ identifier: '', password: '' });
const signup = reactive({ username: '', email: '', password: '' });
const fieldErrors = ref({});
const message = ref('');
const loading = ref(false);

// Swap forms in place and keep the URL / tab title in sync, without a reload.
function setMode(next) {
  mode.value = next;
  fieldErrors.value = {};
  message.value = '';
  document.title = `${next === 'signup' ? 'Sign up' : 'Sign in'} · Circle`;
}

function switchTo(next) {
  if (next === mode.value || loading.value) return;
  setMode(next);
  const url = (next === 'signup' ? props.signupUrl : props.signinUrl) + window.location.search;
  history.pushState({ mode: next }, '', url);
}

function onPopState() {
  setMode(window.location.pathname === props.signupUrl ? 'signup' : 'signin');
}

onMounted(() => window.addEventListener('popstate', onPopState));
onBeforeUnmount(() => window.removeEventListener('popstate', onPopState));

function validateSignIn() {
  const errors = {};
  if (!signin.identifier.trim()) errors.identifier = 'Enter your username or email.';
  if (!signin.password) errors.password = 'Enter your password.';
  return errors;
}

function validateSignUp() {
  const errors = {};
  if (!signup.username.trim()) errors.username = 'Choose a username.';
  if (!/^\S+@\S+\.\S+$/.test(signup.email.trim())) errors.email = 'Enter a valid email address.';
  if (signup.password.length < 8) errors.password = 'Password must be at least 8 characters.';
  return errors;
}

async function submit(validate, url, data) {
  if (loading.value) return;
  message.value = '';
  fieldErrors.value = validate();
  if (Object.keys(fieldErrors.value).length) return;

  loading.value = true;
  try {
    await apiPost(url, data);
    window.location.href = props.nextUrl;
  } catch (err) {
    const parsed = parseErrors(err);
    fieldErrors.value = parsed.fieldErrors;
    message.value = parsed.message;
    loading.value = false;
  }
}

const submitSignIn = () => submit(validateSignIn, props.signinApi, signin);
const submitSignUp = () => submit(validateSignUp, props.signupApi, signup);
const submitGoogle = (credential) => submit(() => ({}), props.googleApi, { credential });
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.alert {
  margin: 0 0 16px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--danger);
  background: var(--danger-bg);
  border-radius: 10px;
}

.btn {
  width: 100%;
  height: 46px;
  margin-top: 8px;
  font: inherit;
  font-weight: 600;
  color: #fff;
  background: var(--primary);
  border: 0;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn:disabled {
  opacity: 0.7;
  cursor: progress;
}
</style>
