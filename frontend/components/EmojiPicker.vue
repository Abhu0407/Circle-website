<!--
  Emoji picker that pops up above the chat's message box: search, recently
  used, and every category in one scrolling list (the tabs jump to one).
  Closes on Esc or a click outside it (except on an element marked
  data-emoji-toggle, i.e. the button that opens it).
  Usage: <EmojiPicker v-if="open" @pick="insert" @close="open = false" />
-->
<template>
  <div ref="root" class="picker" role="dialog" aria-label="Emoji" @keydown.esc.stop="$emit('close')">
    <label class="picker__search">
      <Icon name="search" :size="15" />
      <input ref="search" v-model="query" type="search" placeholder="Search emoji" aria-label="Search emoji" />
    </label>

    <nav v-if="!query.trim()" class="picker__tabs" aria-label="Emoji categories">
      <button
        v-for="s in sections"
        :key="s.id"
        type="button"
        class="picker__tab"
        :class="{ 'picker__tab--on': current === s.id }"
        :title="s.label"
        :aria-label="s.label"
        @click="jump(s.id)"
      >{{ s.icon }}</button>
    </nav>

    <div ref="list" class="picker__list" @scroll="onScroll">
      <template v-if="query.trim()">
        <div v-if="results.length" class="picker__grid">
          <button
            v-for="e in results"
            :key="e.char"
            type="button"
            class="picker__emoji"
            :title="e.words"
            @click="pick(e.char)"
          >{{ e.char }}</button>
        </div>
        <p v-else class="picker__none">No emoji found</p>
      </template>

      <section v-for="s in sections" v-else :key="s.id" :data-section="s.id">
        <h3 class="picker__heading">{{ s.label }}</h3>
        <div class="picker__grid">
          <button
            v-for="e in s.emoji"
            :key="e.char"
            type="button"
            class="picker__emoji"
            :title="e.words"
            @click="pick(e.char)"
          >{{ e.char }}</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { EMOJI_CATEGORIES, recentEmoji, rememberEmoji, searchEmoji } from '../emoji.mjs';
import Icon from './Icon.vue';

const emit = defineEmits(['pick', 'close']);

const root = ref(null);
const list = ref(null);
const search = ref(null);
const query = ref('');
const recent = ref(recentEmoji());
const current = ref(recent.value.length ? 'recent' : EMOJI_CATEGORIES[0].id);

const sections = computed(() => {
  const all = EMOJI_CATEGORIES;
  if (!recent.value.length) return all;
  const words = new Map(all.flatMap((c) => c.emoji.map((e) => [e.char, e.words])));
  const recentSection = {
    id: 'recent',
    label: 'Recently used',
    icon: '🕘',
    emoji: recent.value.map((char) => ({ char, words: words.get(char) || '' })),
  };
  return [recentSection, ...all];
});

const results = computed(() => searchEmoji(query.value));

function pick(char) {
  recent.value = rememberEmoji(char);
  emit('pick', char);
}

function jump(id) {
  const el = list.value && list.value.querySelector(`[data-section="${id}"]`);
  if (el) list.value.scrollTop = el.offsetTop - list.value.offsetTop;
  current.value = id;
}

// Highlight the tab of the category being looked at.
function onScroll() {
  const top = list.value.scrollTop + list.value.offsetTop + 8;
  let at = sections.value[0].id;
  for (const el of list.value.querySelectorAll('[data-section]')) {
    if (el.offsetTop <= top) at = el.dataset.section;
  }
  current.value = at;
}

function onOutside(event) {
  if (root.value && !root.value.contains(event.target) && !event.target.closest('[data-emoji-toggle]')) {
    emit('close');
  }
}

onMounted(() => {
  document.addEventListener('mousedown', onOutside);
  // Phones: don't pop the keyboard up over the picker.
  if (window.matchMedia('(hover: hover)').matches) search.value?.focus();
});
onBeforeUnmount(() => document.removeEventListener('mousedown', onOutside));
</script>

<style scoped>
.picker {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  z-index: 6;
  display: flex;
  flex-direction: column;
  width: 340px;
  max-width: calc(100vw - 32px);
  height: 380px;
  max-height: 60vh;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

button {
  font: inherit;
  cursor: pointer;
}

.picker__search {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 10px 6px;
  padding: 0 10px;
  color: var(--muted);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 10px;
}

.picker__search:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--focus);
}

.picker__search input {
  flex: 1;
  min-width: 0;
  padding: 7px 0;
  font: inherit;
  font-size: 14px;
  color: var(--text);
  background: none;
  border: 0;
  outline: none;
}

.picker__tabs {
  display: flex;
  gap: 2px;
  padding: 0 8px 6px;
  border-bottom: 1px solid var(--border);
}

.picker__tab {
  flex: 1;
  padding: 4px 0;
  font-size: 17px;
  line-height: 1.4;
  background: none;
  border: 0;
  border-bottom: 2px solid transparent;
  border-radius: 6px 6px 0 0;
  opacity: 0.6;
}

.picker__tab:hover {
  background: var(--surface-muted);
  opacity: 1;
}

.picker__tab--on {
  border-bottom-color: var(--primary);
  opacity: 1;
}

.picker__list {
  position: relative;
  flex: 1;
  padding: 0 8px 8px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.picker__heading {
  position: sticky;
  top: 0;
  z-index: 1;
  margin: 0;
  padding: 8px 4px 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  background: var(--surface);
}

.picker__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(36px, 1fr));
  padding-top: 4px;
}

.picker__emoji {
  display: grid;
  place-items: center;
  height: 36px;
  padding: 0;
  font-size: 22px;
  line-height: 1;
  background: none;
  border: 0;
  border-radius: 8px;
}

.picker__emoji:hover,
.picker__emoji:focus-visible {
  background: var(--primary-soft);
  outline: none;
}

.picker__none {
  margin: 24px 0;
  font-size: 14px;
  text-align: center;
  color: var(--muted);
}
</style>
