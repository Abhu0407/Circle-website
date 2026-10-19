<template>
  <div class="layout">
    <!-- Dark header band behind the title, filters and top of the right panel. -->
    <div class="band" aria-hidden="true"></div>

    <!-- ---------- Sidebar ---------- -->
    <aside class="sidebar">
      <div class="sidebar__top">
        <BrandLogo :size="30" />
        <span class="location"><Icon name="pin" :size="13" /> Mumbai</span>
      </div>

      <nav class="nav" aria-label="Main">
        <button
          v-for="item in NAV"
          :key="item.id"
          type="button"
          class="nav__item"
          :class="{ 'nav__item--active': active === item.id }"
          :aria-current="active === item.id ? 'page' : undefined"
          @click="active = item.id"
        >
          <Icon :name="item.icon" />
          <span>{{ item.label }}</span>
        </button>

        <hr class="nav__divider" />

        <button type="button" class="nav__item" @click="active = 'create'">
          <Icon name="plus" />
          <span>Create Community</span>
        </button>
      </nav>

      <div class="account">
        <button
          type="button"
          class="account__btn"
          :aria-expanded="menuOpen"
          @click="menuOpen = !menuOpen"
        >
          <span class="avatar" style="--a: #22b8c9; --b: #1f6fe5">{{ initial }}</span>
          <span class="account__name">{{ displayName }}</span>
          <Icon name="chevron" :size="16" class="account__chev" :class="{ 'account__chev--open': menuOpen }" />
        </button>

        <div v-if="menuOpen" class="account__menu">
          <p class="account__email">{{ user.email }}</p>
          <button type="button" class="account__signout" :disabled="signingOut" @click="signOut">
            <Icon name="logout" :size="16" />
            {{ signingOut ? 'Signing out…' : 'Sign out' }}
          </button>
        </div>
      </div>
    </aside>

    <!-- ---------- Main ---------- -->
    <main class="main">
      <template v-if="active === 'discover'">
        <h1 class="main__title">Discover People &amp; Activities</h1>

        <div class="filters">
          <label class="search">
            <Icon name="search" :size="18" />
            <input v-model="query" type="search" placeholder="Search" aria-label="Search people and activities" />
          </label>
          <div class="chips">
            <button
              v-for="c in CATEGORIES"
              :key="c"
              type="button"
              class="chip"
              :class="{ 'chip--on': categories.has(c) }"
              :aria-pressed="categories.has(c)"
              @click="toggle(categories, c)"
            >{{ c }}</button>
            <button
              type="button"
              class="chip"
              :class="{ 'chip--on': nearby }"
              :aria-pressed="nearby"
              @click="nearby = !nearby"
            >Within 10km</button>
          </div>
        </div>

        <div v-if="feed.length" class="grid">
          <template v-for="item in feed" :key="item.id">
            <!-- Person card -->
            <article v-if="item.type === 'person'" class="card">
              <div class="card__media person" :style="{ '--a': item.colors[0], '--b': item.colors[1] }">
                <span class="person__initial">{{ item.name[0] }}</span>
                <span class="distance"><Icon name="pin" :size="12" /> {{ item.distanceKm }} km</span>
              </div>
              <div class="card__body">
                <h2 class="card__title">{{ item.name }}, {{ item.age }}</h2>
                <p class="card__text">{{ item.bio }}</p>
                <div class="tags">
                  <span v-for="t in item.tags" :key="t">#{{ t }}</span>
                </div>
                <button
                  type="button"
                  class="btn btn--solid"
                  :class="{ 'btn--done': connected.has(item.id) }"
                  @click="toggle(connected, item.id)"
                >
                  <Icon v-if="connected.has(item.id)" name="check" :size="16" />
                  {{ connected.has(item.id) ? 'Requested' : 'Connect' }}
                </button>
              </div>
            </article>

            <!-- Community card -->
            <article v-else class="card">
              <div class="card__media">
                <ActivityArt :kind="item.art" />
                <span class="distance"><Icon name="pin" :size="12" /> {{ item.distanceKm }} km</span>
              </div>
              <div class="card__body">
                <h2 class="card__title card__title--lg">{{ item.title }}</h2>
                <div class="members">
                  <span class="avatar avatar--sm" style="--a: #f59f00; --b: #e8590c">A</span>
                  <span class="avatar avatar--sm" style="--a: #be4bdb; --b: #7048e8">P</span>
                  <span class="avatar avatar--sm avatar--count">+{{ item.members - 2 }}</span>
                  <span class="members__count">{{ item.members + (joined.has(item.id) ? 1 : 0) }} members</span>
                </div>
                <button
                  type="button"
                  class="btn btn--soft"
                  :class="{ 'btn--done': joined.has(item.id) }"
                  @click="toggle(joined, item.id)"
                >
                  <Icon v-if="joined.has(item.id)" name="check" :size="16" />
                  {{ joined.has(item.id) ? 'Joined' : 'Join Group' }}
                </button>
              </div>
            </article>
          </template>
        </div>

        <div v-else-if="allItems.length" class="empty">
          <p>No people or activities match your filters.</p>
          <button type="button" class="btn btn--soft" @click="clearFilters">Clear filters</button>
        </div>

        <div v-else class="empty">
          <Icon name="compass" :size="36" />
          <p>No people or activities near you yet.</p>
          <button type="button" class="btn btn--soft" @click="active = 'create'">Create a community</button>
        </div>
      </template>

      <section v-else class="placeholder">
        <h1 class="main__title">{{ activeLabel }}</h1>
        <div class="empty">
          <Icon :name="activeIcon" :size="36" />
          <p>{{ activeLabel }} is coming soon.</p>
          <button type="button" class="btn btn--soft" @click="active = 'discover'">Back to Discover</button>
        </div>
      </section>
    </main>

    <!-- ---------- Right panel ---------- -->
    <aside class="aside">
      <section class="panel">
        <h2 class="panel__title">Quick Activity Map</h2>
        <div class="map">
          <svg viewBox="0 0 200 220" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
            <rect width="200" height="220" fill="#cfe2f2" />
            <path
              d="M78 0H200V220H128C118 204 106 192 100 172C92 152 66 142 68 118C70 98 56 84 60 62C64 42 80 26 78 0Z"
              fill="#eef2f6"
            />
            <path d="M200 120C180 118 168 126 150 124" fill="none" stroke="#cfe2f2" stroke-width="6" />
            <ellipse cx="160" cy="54" rx="26" ry="18" fill="#cfe8c9" />
            <ellipse cx="118" cy="150" rx="10" ry="7" fill="#cfe8c9" />
            <g fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round">
              <path d="M96 0C100 60 92 120 120 220" />
              <path d="M130 0C134 70 140 140 150 220" />
              <path d="M72 100C110 96 160 104 200 96" />
              <path d="M84 40C120 44 160 30 200 34" />
            </g>
          </svg>
          <span class="map__you" style="left: 60%; top: 70%" title="You"></span>
          <span
            v-for="p in people"
            :key="p.id"
            class="map__pin"
            :style="{ left: p.map.x + '%', top: p.map.y + '%', '--a': p.colors[0], '--b': p.colors[1] }"
            :title="`${p.name} · ${p.distanceKm} km`"
          ><span>{{ p.name[0] }}</span></span>
        </div>
      </section>

      <section class="panel">
        <h2 class="panel__title">Happening Now</h2>
        <ul v-if="events.length" class="events">
          <li v-for="e in events" :key="e.id" class="event" :style="{ '--c': e.color }">
            <strong>{{ e.title }}</strong>
            <span><Icon name="clock" :size="13" /> {{ e.time }}</span>
          </li>
        </ul>
        <p v-else class="panel__empty">Nothing happening right now.</p>
      </section>
    </aside>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { apiPost } from '../../api.mjs';
import BrandLogo from '../../components/BrandLogo.vue';
import Icon from '../../components/Icon.vue';
import ActivityArt from '../../components/ActivityArt.vue';
// Props come from HomePageView.get_page_props() in Django.
// people:  [{ id, name, age, bio, category, tags: [], distanceKm, colors: [a, b], map: { x, y } }]
// groups:  [{ id, title, category, art, members, distanceKm }]
// events:  [{ id, title, time, color }]
const props = defineProps({
  user: { type: Object, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  people: { type: Array, default: () => [] },
  groups: { type: Array, default: () => [] },
  events: { type: Array, default: () => [] },
});

const NAV = [
  { id: 'discover', label: 'Discover', icon: 'compass' },
  { id: 'communities', label: 'My Communities', icon: 'users' },
  { id: 'chats', label: 'Chats', icon: 'chat' },
  { id: 'profile', label: 'Profile', icon: 'user' },
];
const CATEGORIES = ['Sports', 'Tech', 'Arts'];

const active = ref('discover');
const menuOpen = ref(false);
const signingOut = ref(false);

const query = ref('');
const categories = ref(new Set());
const nearby = ref(false);
const connected = ref(new Set());
const joined = ref(new Set());

const displayName = computed(() => props.user.first_name || props.user.username);
const initial = computed(() => displayName.value.charAt(0).toUpperCase());
const activeItem = computed(
  () => NAV.find((n) => n.id === active.value) || { label: 'Create Community', icon: 'plus' }
);
const activeLabel = computed(() => activeItem.value.label);
const activeIcon = computed(() => activeItem.value.icon);

// People and communities interleaved, then filtered by search + chips.
const allItems = computed(() => {
  const { people, groups } = props;
  const out = [];
  const len = Math.max(people.length, groups.length);
  for (let i = 0; i < len; i++) {
    if (people[i]) out.push({ ...people[i], type: 'person' });
    if (groups[i]) out.push({ ...groups[i], type: 'group' });
  }
  return out;
});

const feed = computed(() => {
  const q = query.value.trim().toLowerCase();
  return allItems.value.filter((item) => {
    if (categories.value.size && !categories.value.has(item.category)) return false;
    if (nearby.value && item.distanceKm > 10) return false;
    if (!q) return true;
    const haystack = [item.name, item.title, item.bio, item.category, ...(item.tags || [])]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    return haystack.includes(q);
  });
});

function toggle(set, value) {
  if (set.has(value)) set.delete(value);
  else set.add(value);
}

function clearFilters() {
  query.value = '';
  categories.value.clear();
  nearby.value = false;
}

async function signOut() {
  signingOut.value = true;
  try {
    await apiPost(props.signoutApi);
  } finally {
    window.location.href = props.signinUrl;
  }
}
</script>

<style scoped>
/* ---------- layout ---------- */
.layout {
  display: grid;
  grid-template-columns: 248px minmax(0, 1fr) 300px;
  grid-template-areas: 'sidebar main aside';
  min-height: 100vh;
  background: var(--bg);
}

button {
  font: inherit;
  cursor: pointer;
}

/* ---------- sidebar ---------- */
.sidebar {
  grid-area: sidebar;
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 28px 0 20px;
  color: var(--night-text);
  background: linear-gradient(180deg, var(--night-700) 0%, var(--night-800) 70%);
}

.sidebar__top {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  padding: 0 24px 28px;
}

.location {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: 40px;
  padding: 2px 10px;
  font-size: 12px;
  color: var(--night-muted);
  background: rgba(255, 255, 255, 0.07);
  border-radius: 8px;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-right: 16px;
}

.nav__item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 11px 20px 11px 24px;
  font-size: 15px;
  font-weight: 500;
  text-align: left;
  color: var(--night-muted);
  background: none;
  border: 0;
  border-radius: 0 12px 12px 0;
  transition: background 0.15s, color 0.15s;
}

.nav__item:hover {
  color: var(--night-text);
  background: rgba(255, 255, 255, 0.05);
}

.nav__item--active {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: inset 3px 0 0 var(--teal);
}

.nav__divider {
  margin: 12px 0 12px 24px;
  border: 0;
  border-top: 1px solid var(--night-border);
}

.account {
  position: relative;
  margin-top: auto;
  padding: 16px 16px 0 24px;
  border-top: 1px solid var(--night-border);
}

.account__btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 4px;
  color: var(--night-text);
  background: none;
  border: 0;
  border-radius: 12px;
}

.account__name {
  overflow: hidden;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account__chev {
  margin-left: auto;
  color: var(--night-muted);
  transition: transform 0.15s;
}

.account__chev--open {
  transform: rotate(180deg);
}

.account__menu {
  position: absolute;
  right: 16px;
  bottom: calc(100% + 8px);
  left: 24px;
  padding: 12px;
  color: var(--text);
  background: var(--surface);
  border-radius: 12px;
  box-shadow: var(--shadow);
}

.account__email {
  margin: 0 0 8px;
  overflow: hidden;
  font-size: 13px;
  color: var(--muted);
  text-overflow: ellipsis;
}

.account__signout {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  font-weight: 600;
  color: var(--danger);
  background: var(--danger-bg);
  border: 0;
  border-radius: 8px;
}

.account__signout:disabled {
  opacity: 0.7;
  cursor: progress;
}

/* ---------- avatars ---------- */
.avatar {
  display: grid;
  flex: none;
  place-items: center;
  width: 38px;
  height: 38px;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--a), var(--b));
  border-radius: 50%;
}

.avatar--sm {
  width: 28px;
  height: 28px;
  margin-right: -8px;
  font-size: 11px;
  border: 2px solid var(--surface);
}

.avatar--count {
  font-size: 10px;
  color: var(--muted);
  background: var(--surface-muted);
}

/* ---------- main ---------- */
.main {
  grid-area: main;
  position: relative;
  min-width: 0;
  padding: 32px clamp(16px, 3vw, 36px) 40px;
}

/* Dark header band with a soft curved bottom. */
.band {
  grid-row: main-start;
  grid-column: main-start / aside-end;
  align-self: start;
  height: 300px;
  background:
    radial-gradient(700px 300px at 0% 0%, #1b4e66 0%, transparent 60%),
    linear-gradient(180deg, var(--night-700) 0%, #1d3b62 100%);
  border-radius: 0 0 50% 50% / 0 0 48px 48px;
}

.main,
.aside {
  z-index: 1;
}

.main__title {
  margin: 0 0 16px;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--night-text);
}

.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--night-border);
  border-radius: 14px;
}

.search {
  display: flex;
  flex: 1 1 200px;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  color: var(--night-muted);
}

.search input {
  width: 100%;
  height: 36px;
  font: inherit;
  color: var(--night-text);
  background: none;
  border: 0;
  outline: none;
}

.search input::placeholder {
  color: var(--night-muted);
}

.search:focus-within {
  color: var(--night-text);
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 6px 14px;
  font-size: 14px;
  font-weight: 500;
  color: var(--night-text);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 9px;
  transition: background 0.15s, border-color 0.15s;
}

.chip:hover {
  background: rgba(255, 255, 255, 0.12);
}

.chip--on {
  color: var(--night-900);
  background: var(--night-text);
  border-color: var(--night-text);
}

.chip--on:hover {
  background: #fff;
}

/* ---------- cards ---------- */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
}

.card {
  display: flex;
  flex-direction: column;
  padding: 10px;
  background: var(--surface);
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(8, 19, 31, 0.14);
  transition: transform 0.15s, box-shadow 0.15s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 36px rgba(8, 19, 31, 0.18);
}

.card__media {
  position: relative;
  height: 150px;
  overflow: hidden;
  border-radius: 12px;
}

.person {
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.35), transparent 55%),
    linear-gradient(135deg, var(--a), var(--b));
}

.person__initial {
  display: grid;
  place-items: center;
  width: 84px;
  height: 84px;
  font-size: 38px;
  font-weight: 700;
  color: #fff;
  background: rgba(255, 255, 255, 0.18);
  border: 3px solid rgba(255, 255, 255, 0.6);
  border-radius: 50%;
}

.distance {
  position: absolute;
  top: 8px;
  right: 8px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: rgba(8, 19, 31, 0.55);
  border-radius: 999px;
}

.card__body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 10px;
  padding: 14px 6px 4px;
}

.card__title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.25;
}

.card__title--lg {
  font-size: 19px;
}

.card__text {
  margin: -4px 0 0;
  font-size: 14px;
  line-height: 1.4;
  color: var(--muted);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tags span {
  padding: 2px 9px;
  font-size: 12px;
  color: var(--muted);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 7px;
}

.members {
  display: flex;
  align-items: center;
}

.members__count {
  margin-left: 18px;
  font-size: 14px;
  color: var(--muted);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 40px;
  margin-top: auto;
  padding: 0 16px;
  font-weight: 600;
  border-radius: 10px;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.btn--solid {
  color: #fff;
  background: var(--primary);
  border: 1px solid var(--primary);
}

.btn--solid:hover {
  background: var(--primary-hover);
}

.btn--soft {
  color: var(--primary);
  background: var(--primary-soft);
  border: 1px solid #c9dafa;
}

.btn--soft:hover {
  border-color: var(--primary);
}

.btn--done,
.btn--done:hover {
  color: var(--green-dark);
  background: var(--green-soft);
  border-color: #bfe8d0;
}

/* ---------- empty / placeholder ---------- */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
  padding: 48px 24px;
  text-align: center;
  color: var(--muted);
  background: var(--surface);
  border-radius: 18px;
  box-shadow: var(--shadow);
}

.empty p {
  margin: 0;
}

.empty .btn {
  margin-top: 4px;
}

/* ---------- right panel ---------- */
.aside {
  grid-area: aside;
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100vh;
  padding: 24px 20px 24px 0;
  overflow-y: auto;
}

.panel {
  padding: 16px;
  background: var(--surface);
  border-radius: 18px;
  box-shadow: var(--shadow);
}

.panel__title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
}

.panel__empty {
  margin: 0;
  padding: 16px 12px;
  font-size: 14px;
  text-align: center;
  color: var(--muted);
  background: var(--surface-muted);
  border-radius: 10px;
}

.map {
  position: relative;
  height: 230px;
  overflow: hidden;
  border-radius: 12px;
}

.map svg {
  display: block;
  width: 100%;
  height: 100%;
}

.map__pin {
  position: absolute;
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--a), var(--b));
  border: 2px solid #fff;
  border-radius: 50% 50% 50% 0;
  box-shadow: 0 4px 10px rgba(8, 19, 31, 0.25);
  transform: translate(-50%, -100%) rotate(-45deg);
}

/* Keep the letter upright inside the rotated pin. */
.map__pin > span {
  transform: rotate(45deg);
}

.map__you {
  position: absolute;
  width: 14px;
  height: 14px;
  background: var(--primary);
  border: 3px solid #fff;
  border-radius: 50%;
  box-shadow: 0 0 0 6px rgba(31, 111, 229, 0.2);
  transform: translate(-50%, -50%);
}

.events {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.event {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  font-size: 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--c);
  border-radius: 10px;
}

.event strong {
  font-weight: 500;
}

.event span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--muted);
}

/* ---------- responsive ---------- */
@media (max-width: 1200px) {
  .layout {
    grid-template-columns: 220px minmax(0, 1fr);
    grid-template-areas:
      'sidebar main'
      'sidebar aside';
  }
  .aside {
    position: static;
    display: grid;
    grid-template-columns: 1fr 1fr;
    align-items: start;
    height: auto;
    padding: 0 clamp(16px, 3vw, 36px) 40px;
  }
}

@media (max-width: 760px) {
  .layout {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas: 'sidebar' 'main' 'aside';
  }
  .sidebar {
    position: static;
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
    height: auto;
    padding: 14px 16px;
  }
  .sidebar__top {
    flex-direction: row;
    align-items: center;
    padding: 0;
  }
  .location {
    margin-left: 0;
  }
  .nav {
    order: 3;
    flex-direction: row;
    width: 100%;
    margin-top: 12px;
    padding: 0;
    overflow-x: auto;
  }
  .nav__item {
    flex: none;
    width: auto;
    padding: 8px 12px;
    font-size: 14px;
    border-radius: 10px;
  }
  .nav__item--active {
    box-shadow: inset 0 -2px 0 var(--teal);
  }
  .nav__divider {
    display: none;
  }
  .account {
    margin: 0 0 0 auto;
    padding: 0;
    border: 0;
  }
  .account__name {
    display: none;
  }
  .account__menu {
    top: calc(100% + 8px);
    right: 0;
    bottom: auto;
    left: auto;
    z-index: 10;
    width: 220px;
  }
  .main {
    padding-top: 24px;
  }
  .aside {
    grid-template-columns: 1fr;
    padding: 0 16px 32px;
  }
}
</style>
