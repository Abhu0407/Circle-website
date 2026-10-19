<template>
  <div class="field" :class="{ 'field--error': error }">
    <label :for="id" class="field__label">{{ label }}</label>
    <div class="field__control">
      <input
        :id="id"
        class="field__input"
        :type="inputType"
        :value="modelValue"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :required="required"
        :aria-invalid="!!error"
        :aria-describedby="error ? id + '-error' : undefined"
        @input="$emit('update:modelValue', $event.target.value)"
      />
      <button
        v-if="type === 'password'"
        type="button"
        class="field__toggle"
        :aria-label="showPassword ? 'Hide password' : 'Show password'"
        @click="showPassword = !showPassword"
      >
        {{ showPassword ? 'Hide' : 'Show' }}
      </button>
    </div>
    <p v-if="error" :id="id + '-error'" class="field__error">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  id: { type: String, required: true },
  label: { type: String, required: true },
  modelValue: { type: String, default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  autocomplete: { type: String, default: 'off' },
  required: { type: Boolean, default: false },
  error: { type: String, default: '' },
});

defineEmits(['update:modelValue']);

const showPassword = ref(false);
const inputType = computed(() =>
  props.type === 'password' && showPassword.value ? 'text' : props.type
);
</script>

<style scoped>
.field {
  margin-bottom: 16px;
}

.field__label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 600;
}

.field__control {
  position: relative;
}

.field__input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  font: inherit;
  color: var(--text);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 10px;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.field__input:focus {
  background: var(--surface);
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.field--error .field__input {
  border-color: var(--danger);
}

.field__toggle {
  position: absolute;
  top: 50%;
  right: 8px;
  transform: translateY(-50%);
  padding: 4px 8px;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  background: none;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
}

.field__toggle:hover {
  color: var(--text);
}

.field__error {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--danger);
}
</style>
