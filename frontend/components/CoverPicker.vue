<!--
  Pick a community's picture from the site's drawings for its category
  (backend: models.COVERS). Used as the community's cover and round picture.
  Usage:
    <CoverPicker v-model="form.cover" :covers="communityCovers[form.category] || []" />
-->
<template>
  <div class="covers" role="radiogroup" aria-label="Picture">
    <button
      v-for="c in covers"
      :key="c.value"
      type="button"
      role="radio"
      class="cover"
      :class="{ 'cover--on': modelValue === c.value }"
      :aria-checked="modelValue === c.value"
      @click="$emit('update:modelValue', c.value)"
    >
      <img :src="c.url" alt="" class="cover__img" loading="lazy" />
      <span class="cover__label">{{ c.label }}</span>
      <span v-if="modelValue === c.value" class="cover__check"><Icon name="check" :size="12" /></span>
    </button>
  </div>
</template>

<script setup>
import Icon from './Icon.vue';

defineProps({
  modelValue: { type: String, default: '' },
  // [{ value, label, url }]
  covers: { type: Array, required: true },
});
defineEmits(['update:modelValue']);
</script>

<style scoped>
.covers {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}

.cover {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
  font: inherit;
  text-align: left;
  color: var(--text);
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.cover:hover {
  border-color: var(--primary);
}

.cover:focus-visible {
  outline: none;
  box-shadow: 0 0 0 4px var(--focus);
}

.cover--on {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--focus);
}

.cover__img {
  display: block;
  width: 100%;
  aspect-ratio: 2 / 1;
  object-fit: cover;
}

.cover__label {
  padding: 6px 10px;
  font-size: 13px;
  font-weight: 500;
}

.cover__check {
  position: absolute;
  top: 6px;
  right: 6px;
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  color: #fff;
  background: var(--primary);
  border: 2px solid #fff;
  border-radius: 50%;
}
</style>
