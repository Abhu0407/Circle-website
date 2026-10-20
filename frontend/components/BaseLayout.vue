<!--
  The frame shared by every signed-in page: left sidebar (logo, location,
  menu, account menu), the dark header band, the right panel (Quick Activity
  Map, Happening Now) and the responsive grid. The page's own content goes in
  the default slot.

  Usage (see pages/home/Home.vue, pages/profile/Profile.vue):
    <BaseLayout :user="me" active="profile" :home-url="homeUrl" ...>
      ...page content...
    </BaseLayout>

  Menu items are links. Items listed in `localTabs` are handled by the page
  itself without a reload: clicking one emits `navigate` with its id.
  On phones the menu is hidden behind a ☰ button and opens as a list.
-->
<template>
  <div class="layout">
    <!-- Dark header band behind the title, filters and top of the right panel. -->
    <div class="band" aria-hidden="true"></div>

    <!-- ---------- Sidebar ---------- -->
    <aside class="sidebar">
      <div class="sidebar__top">
        <BrandLogo :size="30" />
        <a :href="profileUrl" class="location">
          <Icon name="pin" :size="13" /> {{ cityName || 'Set location' }}
        </a>
      </div>

      <button
        type="button"
        class="menu-btn"
        :aria-expanded="navOpen"
        aria-controls="main-nav"
        :aria-label="navOpen ? 'Close menu' : 'Open menu'"
        @click="navOpen = !navOpen"
      >
        <Icon :name="navOpen ? 'close' : 'menu'" />
      </button>

      <nav id="main-nav" class="nav" :class="{ 'nav--open': navOpen }" aria-label="Main">
        <a
          v-for="item in NAV"
          :key="item.id"
          :href="item.href"
          class="nav__item"
          :class="{ 'nav__item--active': active === item.id }"
          :aria-current="active === item.id ? 'page' : undefined"
          @click="onNav($event, item.id)"
        >
          <Icon :name="item.icon" />
          <span>{{ item.label }}</span>
        </a>

        <hr class="nav__divider" />

        <a
          :href="CREATE.href"
          class="nav__item"
          :class="{ 'nav__item--active': active === CREATE.id }"
          :aria-current="active === CREATE.id ? 'page' : undefined"
          @click="onNav($event, CREATE.id)"
        >
          <Icon :name="CREATE.icon" />
          <span>{{ CREATE.label }}</span>
        </a>
      </nav>

      <div class="account">
        <button
          type="button"
          class="account__btn"
          :aria-expanded="menuOpen"
          @click="menuOpen = !menuOpen"
        >
          <img v-if="user.profile_picture" :src="user.profile_picture" alt="" class="avatar avatar--img" />
          <span v-else class="avatar" style="--a: #22b8c9; --b: #1f6fe5">{{ initial }}</span>
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

    <!-- ---------- Main (the page) ---------- -->
    <main class="main">
      <slot />
    </main>

    <!-- ---------- Right panel ---------- -->
    <aside class="aside">
      <section class="panel">
        <div class="panel__head">
          <h2 class="panel__title">Quick Activity Map</h2>
          <button type="button" class="panel__expand" aria-label="Open large map" title="Open large map" @click="mapOpen = true">
            <Icon name="expand" :size="16" />
          </button>
        </div>
        <PeopleMap :tile-url="mapTileUrl" :people="mapPeople" :me="user" />

        <Modal v-if="mapOpen" :title="mapTitle" large @close="mapOpen = false">
          <PeopleMap :tile-url="mapTileUrl" :people="mapPeople" :me="user" large />
        </Modal>
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
import { apiPost } from '../api.mjs';
import BrandLogo from './BrandLogo.vue';
import Icon from './Icon.vue';
import Modal from './Modal.vue';
import PeopleMap from './PeopleMap.vue';

// mapPeople: [{ id, username, lat, lng }]  (Quick Activity Map pins)
// events:    [{ id, title, time, color }]  (Happening Now)
const props = defineProps({
  user: { type: Object, required: true },
  // Which menu item is highlighted.
  active: { type: String, default: '' },
  // Menu ids this page switches between itself (no reload).
  localTabs: { type: Array, default: () => [] },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  mapTileUrl: { type: String, required: true },
  mapPeople: { type: Array, default: () => [] },
  events: { type: Array, default: () => [] },
});
const emit = defineEmits(['navigate']);

const tabUrl = (id) => `${props.homeUrl}?tab=${id}`;
const NAV = [
  { id: 'foryou', label: 'For You', icon: 'sparkle', href: props.homeUrl },
  { id: 'discover', label: 'Discover', icon: 'compass', href: tabUrl('discover') },
  { id: 'communities', label: 'My Communities', icon: 'users', href: tabUrl('communities') },
  { id: 'chats', label: 'Chats', icon: 'chat', href: tabUrl('chats') },
  { id: 'profile', label: 'Profile', icon: 'user', href: props.profileUrl },
];
const CREATE = { id: 'create', label: 'Create Community', icon: 'plus', href: tabUrl('create') };

const menuOpen = ref(false);
// Phone-width menu (☰).
const navOpen = ref(false);
const mapOpen = ref(false);
const mapTitle = computed(() => {
  const n = props.mapPeople.length;
  return n ? `Activity Map · ${n} ${n === 1 ? 'person' : 'people'}` : 'Activity Map';
});
const signingOut = ref(false);

const displayName = computed(
  () => props.user.name || [props.user.first_name, props.user.last_name].filter(Boolean).join(' ') || props.user.username
);
const initial = computed(() => displayName.value.charAt(0).toUpperCase());
const cityName = computed(() => (props.user.location || '').split(',')[0].trim());

function onNav(event, id) {
  navOpen.value = false;
  if (!props.localTabs.includes(id)) return; // normal link: load that page
  event.preventDefault();
  emit('navigate', id);
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
  font-weight: 400;
  text-decoration: none;
  align-items: center;
  gap: 4px;
  max-width: 180px;
  margin-left: 40px;
  padding: 2px 10px;
  overflow: hidden;
  font-size: 12px;
  white-space: nowrap;
  color: var(--night-muted);
  background: rgba(255, 255, 255, 0.07);
  border: 0;
  border-radius: 8px;
}

.location:hover {
  text-decoration: none;
  color: var(--night-text);
  background: rgba(255, 255, 255, 0.12);
}

.menu-btn {
  display: none;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-right: 16px;
}

.nav__item {
  display: flex;
  text-decoration: none;
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
  text-decoration: none;
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

/* ---------- avatar ---------- */
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

.avatar--img {
  object-fit: cover;
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

.panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.panel__head .panel__title {
  margin: 0;
}

.panel__expand {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  color: var(--muted);
  background: var(--surface-muted);
  border: 0;
  border-radius: 8px;
}

.panel__expand:hover {
  color: var(--primary);
  background: var(--primary-soft);
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
  .menu-btn {
    display: grid;
    order: 2;
    place-items: center;
    width: 38px;
    height: 38px;
    margin-left: 8px;
    color: var(--night-text);
    background: rgba(255, 255, 255, 0.07);
    border: 0;
    border-radius: 10px;
  }
  .menu-btn:hover,
  .menu-btn[aria-expanded='true'] {
    background: rgba(255, 255, 255, 0.14);
  }
  .nav {
    order: 3;
    display: none;
    width: 100%;
    margin-top: 12px;
    padding: 8px 0 0;
    border-top: 1px solid var(--night-border);
  }
  .nav--open {
    display: flex;
  }
  .nav__item {
    padding: 11px 14px;
    border-radius: 10px;
  }
  .nav__divider {
    margin: 6px 0;
  }
  .account {
    order: 1;
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
