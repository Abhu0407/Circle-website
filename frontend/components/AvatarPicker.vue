<!--
  Pick a profile picture from the site's avatars (backend: accounts.models.AVATARS).
  Usage: <AvatarPicker :model-value="me.avatar" :avatars="avatars" :disabled="busy" @update:model-value="pick" />
-->
<template>
  <div class="avatars" role="radiogroup" aria-label="Avatar">
    <button
      v-for="a in avatars"
      :key="a.value"
      type="button"
      role="radio"
      class="avatar"
      :class="{ 'avatar--on': modelValue === a.value }"
      :aria-checked="modelValue === a.value"
      :aria-label="a.label"
      :title="a.label"
      :disabled="disabled"
      @click="$emit('update:modelValue', a.value)"
    >
      <img :src="a.url" alt="" class="avatar__img" loading="lazy" />
      <span v-if="modelValue === a.value" class="avatar__check"><Icon name="check" :size="11" /></span>
    </button>
  </div>
</template>

<script setup>
import Icon from './Icon.vue';

defineProps({
  modelValue: { type: String, default: '' },
  // [{ value, label, url }]
  avatars: { type: Array, required: true },
  disabled: { type: Boolean, default: false },
});
defineEmits(['update:modelValue']);
</script>

<style scoped>
.avatars {
  display: grid;
  /* 16 avatars: people on the first two rows, animals on the last two. */
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  max-width: 360px;
  margin: 0 auto;
}

.avatar {
  position: relative;
  aspect-ratio: 1;
  padding: 0;
  background: none;
  border: 3px solid transparent;
  border-radius: 50%;
  cursor: pointer;
  transition: border-color 0.15s, transform 0.15s;
}

.avatar:hover:not(:disabled) {
  transform: scale(1.06);
}

.avatar:focus-visible {
  outline: none;
  box-shadow: 0 0 0 4px var(--focus);
}

.avatar:disabled {
  cursor: default;
  opacity: 0.6;
}

.avatar--on {
  border-color: var(--primary);
}

.avatar__img {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.avatar__check {
  position: absolute;
  right: -2px;
  bottom: -2px;
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  color: #fff;
  background: var(--primary);
  border: 2px solid var(--surface);
  border-radius: 50%;
}
</style>
