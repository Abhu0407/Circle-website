<!--
  Notifications: posts uploaded and communities created by other people,
  newest first, grouped by day. Ones newer than `seenAt` are highlighted.
  Usage: <NotificationList :notifications-api="notificationsApi" :seen-at="seenAt" />
-->
<template>
  <div class="notes">
    <div class="filters" role="group" aria-label="Show">
      <FilterChip v-for="f in FILTERS" :key="f.value" :on="kind === f.value" @click="setKind(f.value)">
        {{ f.label }}
      </FilterChip>
    </div>

    <p v-if="loading && !items.length" class="note">Loading notifications…</p>
    <p v-else-if="error && !items.length" class="note note--error">{{ error }}</p>

    <EmptyState v-else-if="!items.length" icon="bell" :text="emptyText" />

    <template v-else>
      <section v-for="group in groups" :key="group.label" class="day">
        <h2 class="day__label">{{ group.label }}</h2>
        <ul class="list">
          <li v-for="n in group.items" :key="n.key">
            <a :href="n.url" class="item" :class="{ 'item--new': isNew(n) }">
              <span class="item__pics">
                <img :src="n.community.image" alt="" class="item__cover" />
                <span class="item__kind" :class="`item__kind--${n.type}`">
                  <Icon :name="kindIcon(n)" :size="12" />
                </span>
              </span>

              <span class="item__body">
                <span class="item__line">
                  <template v-if="n.type === 'post'">
                    <b>{{ personName(n.actor) }}</b> posted {{ mediaLabel(n) }} in <b>{{ n.community.name }}</b>
                  </template>
                  <template v-else>
                    <b>{{ personName(n.actor) }}</b> created the community <b>{{ n.community.name }}</b>
                  </template>
                </span>
                <span v-if="n.text" class="item__text">{{ n.text }}</span>
                <span v-if="n.type === 'community'" class="item__meta">
                  {{ n.category }}<template v-if="n.location"> · <Icon name="pin" :size="12" /> {{ n.location }}</template>
                </span>
                <time class="item__time" :datetime="n.created_at" :title="fullDate(n.created_at)">
                  {{ timeAgo(n.created_at) }}
                </time>
              </span>

              <img v-if="n.image" :src="n.image" alt="" class="item__thumb" />
              <span v-if="isNew(n)" class="item__dot" aria-label="New"></span>
            </a>
          </li>
        </ul>
      </section>

      <p v-if="error" class="note note--error">{{ error }}</p>
      <div v-if="hasMore" class="more">
        <ActionButton
          icon="chevron"
          :label="loading ? 'Loading…' : 'Show older'"
          variant="secondary"
          :disabled="loading"
          @click="load(true)"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { apiGet } from '../api.mjs';
import { dayLabel, fullDate, timeAgo } from '../time.mjs';
import ActionButton from './ActionButton.vue';
import EmptyState from './EmptyState.vue';
import FilterChip from './FilterChip.vue';
import Icon from './Icon.vue';

const props = defineProps({
  notificationsApi: { type: String, required: true },
  // ISO time the page was last opened; anything newer is "new".
  seenAt: { type: String, default: '' },
});

const FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'posts', label: 'Posts' },
  { value: 'communities', label: 'Communities' },
];

const kind = ref('all');
const items = ref([]);
const hasMore = ref(false);
const loading = ref(false);
const error = ref('');
// Ignores replies to an older request after the filter changed.
let requestId = 0;
// Where the next page starts (from the API).
let next = null;

const seenTime = computed(() => (props.seenAt ? new Date(props.seenAt).getTime() : 0));
const isNew = (n) => new Date(n.created_at).getTime() > seenTime.value;

const emptyText = computed(() => ({
  all: 'Nothing yet. New posts and communities show up here as soon as someone shares one.',
  posts: 'Nobody else has posted yet.',
  communities: 'Nobody else has created a community yet.',
})[kind.value]);

// [{ label: "Today", items }, { label: "Yesterday", items }, ...]
const groups = computed(() => {
  const out = [];
  for (const n of items.value) {
    const label = dayLabel(n.created_at);
    const last = out[out.length - 1];
    if (last && last.label === label) last.items.push(n);
    else out.push({ label, items: [n] });
  }
  return out;
});

async function load(more = false) {
  const id = ++requestId;
  loading.value = true;
  error.value = '';
  try {
    const params = { kind: kind.value };
    if (more && next) params.before = next;
    const data = await apiGet(props.notificationsApi, params);
    if (id !== requestId) return;
    items.value = more ? [...items.value, ...data.notifications] : data.notifications;
    hasMore.value = data.has_more;
    next = data.next;
  } catch {
    if (id === requestId) error.value = 'Could not load notifications. Please try again.';
  } finally {
    if (id === requestId) loading.value = false;
  }
}

function setKind(value) {
  if (kind.value === value) return;
  kind.value = value;
  items.value = [];
  hasMore.value = false;
  load();
}

function personName(person) {
  return person ? person.name || person.username : 'Someone';
}

function kindIcon(n) {
  if (n.type === 'community') return 'users';
  return n.media === 'video' ? 'video' : n.media === 'image' ? 'image' : 'edit';
}

function mediaLabel(n) {
  return n.media === 'video' ? 'a video' : n.media === 'image' ? 'a photo' : '';
}

onMounted(() => load());
</script>

<style scoped>
.notes {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.note {
  margin: 0;
  padding: 16px;
  text-align: center;
  color: var(--muted);
}

.note--error {
  color: var(--danger);
}

.day {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.day__label {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--muted);
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 28px 12px 12px;
  font-weight: 400;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}

.item:hover {
  text-decoration: none;
  border-color: #c9dafa;
  box-shadow: 0 0 0 4px var(--focus);
}

.item--new {
  background: var(--primary-soft);
  border-color: #c9dafa;
}

.item__pics {
  position: relative;
  flex: none;
}

.item__cover {
  display: block;
  width: 48px;
  height: 48px;
  object-fit: cover;
  background: var(--surface-muted);
  border-radius: 50%;
}

.item__kind {
  position: absolute;
  right: -4px;
  bottom: -4px;
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  color: #fff;
  border: 2px solid var(--surface);
  border-radius: 50%;
}

.item__kind--post {
  background: var(--primary);
}

.item__kind--community {
  background: var(--green);
}

.item__body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.item__line {
  font-size: 15px;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.item__line b {
  font-weight: 600;
}

.item__text {
  display: -webkit-box;
  overflow: hidden;
  font-size: 14px;
  color: var(--muted);
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow-wrap: anywhere;
}

.item__meta {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--muted);
}

.item__time {
  font-size: 12px;
  color: var(--muted);
}

.item--new .item__time {
  font-weight: 600;
  color: var(--primary);
}

.item__thumb {
  flex: none;
  width: 56px;
  height: 56px;
  object-fit: cover;
  background: var(--surface-muted);
  border-radius: 10px;
}

.item__dot {
  position: absolute;
  top: 14px;
  right: 12px;
  width: 9px;
  height: 9px;
  background: var(--primary);
  border-radius: 50%;
}

.more {
  display: flex;
  justify-content: center;
}

@media (max-width: 560px) {
  .item__cover {
    width: 40px;
    height: 40px;
  }
  .item__thumb {
    width: 48px;
    height: 48px;
  }
}
</style>
