<!--
  Home's Discover tab (inside the page's PageSheet): every community,
  nearest first. Search box plus a Filters button (categories, distance
  from your Profile location); active filters show as removable chips.
  Join right from a card.
  Emits `joined` with the community, so the page can update My Communities.
  Usage: <DiscoverCommunities :communities-api="communitiesApi" :categories="communityCategories"
                              :user="me" :profile-url="profileUrl" @joined="..." @create="..." />
-->
<template>
  <div class="discover">
    <!-- ---------- Search + filters ---------- -->
    <div class="toolbar">
      <label class="search">
        <Icon name="search" :size="18" />
        <input
          v-model="query"
          type="search"
          placeholder="Search by name, description, place or category"
          aria-label="Search communities"
        />
      </label>

      <FilterMenu :count="filterCount" @clear="clearChoices">
        <FilterGroup label="Category" hint="pick one or more">
          <FilterChip v-for="c in categories" :key="c.value" :on="picked.includes(c.value)" @click="toggleCategory(c.value)">
            {{ c.label }}
          </FilterChip>
        </FilterGroup>

        <FilterGroup label="Distance" hint="pick one, from your location">
          <FilterChip v-for="km in DISTANCES" :key="km" :on="within === km" :disabled="!hasPoint" @click="toggleDistance(km)">
            Within {{ km }} km
          </FilterChip>
          <template v-if="!hasPoint" #note>
            <Icon name="pin" :size="13" /> <a :href="profileUrl">Set your location</a> on your profile to filter by distance.
          </template>
        </FilterGroup>
      </FilterMenu>
    </div>

    <!-- Filters that are on; × removes one. -->
    <ul v-if="filterCount" class="active" aria-label="Filters on">
      <li v-for="key in picked" :key="key">
        <button type="button" class="pill" :aria-label="`Remove ${labelOf(key)} filter`" @click="toggleCategory(key)">
          {{ labelOf(key) }} <Icon name="close" :size="12" />
        </button>
      </li>
      <li v-if="within">
        <button type="button" class="pill" aria-label="Remove distance filter" @click="within = 0">
          Within {{ within }} km <Icon name="close" :size="12" />
        </button>
      </li>
    </ul>

    <!-- ---------- Results ---------- -->
    <div class="bar">
      <span class="bar__count">
        {{ loading ? 'Searching…' : `${results.length} ${results.length === 1 ? 'community' : 'communities'}` }}
      </span>
      <button v-if="filtered" type="button" class="bar__clear" @click="clearFilters">
        <Icon name="close" :size="14" /> Clear filters
      </button>
    </div>

    <EmptyState v-if="error" icon="close" :text="error">
      <ActionButton icon="back" label="Try again" @click="load" />
    </EmptyState>

    <div v-else-if="results.length" class="grid">
      <article v-for="c in results" :key="c.id" class="ccard">
        <a :href="c.url" class="ccard__cover" :style="c.image ? { backgroundImage: `url(${c.image})` } : null" tabindex="-1" aria-hidden="true">
          <span v-if="!c.image" class="ccard__initial">{{ c.name.charAt(0).toUpperCase() }}</span>
          <span class="badge badge--category">{{ c.category_label }}</span>
          <span v-if="c.distance_km != null" class="badge badge--distance"><Icon name="pin" :size="11" /> {{ formatKm(c.distance_km) }}</span>
        </a>

        <div class="ccard__body">
          <h2 class="ccard__name"><a :href="c.url">{{ c.name }}</a></h2>
          <p class="ccard__text" :class="{ 'ccard__text--empty': !c.description }">{{ c.description || 'No description yet.' }}</p>
          <p class="ccard__meta">
            <span><Icon name="users" :size="13" /> {{ c.members_count }} {{ c.members_count === 1 ? 'member' : 'members' }}</span>
            <span v-if="c.location"><Icon name="pin" :size="13" /> {{ shortPlace(c.location) }}</span>
          </p>

          <div class="ccard__actions">
            <ActionButton
              v-if="c.is_member"
              icon="check"
              label="Joined"
              size="sm"
              variant="secondary"
              @click="open(c)"
            />
            <ActionButton
              v-else
              icon="userPlus"
              :label="joining === c.id ? 'Joining…' : 'Join'"
              size="sm"
              :disabled="joining === c.id"
              @click="join(c)"
            />
            <a :href="c.url" class="ccard__view">View <Icon name="chevron" :size="14" class="ccard__arrow" /></a>
          </div>
          <p v-if="joinError[c.id]" class="ccard__error">{{ joinError[c.id] }}</p>
        </div>
      </article>
    </div>

    <EmptyState v-else-if="!loading && filtered" icon="search" text="No communities match your filters.">
      <ActionButton icon="close" label="Clear filters" @click="clearFilters" />
    </EmptyState>

    <EmptyState v-else-if="!loading" icon="compass" text="There are no communities yet. Start the first one!">
      <ActionButton icon="plus" label="Create a community" @click="$emit('create')" />
    </EmptyState>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { apiGet, apiPost, parseErrors } from '../api.mjs';
import ActionButton from './ActionButton.vue';
import EmptyState from './EmptyState.vue';
import FilterChip from './FilterChip.vue';
import FilterGroup from './FilterGroup.vue';
import FilterMenu from './FilterMenu.vue';
import Icon from './Icon.vue';

const DISTANCES = [2, 5, 10, 25, 50];

const props = defineProps({
  communitiesApi: { type: String, required: true },
  // [{ value, label }]
  categories: { type: Array, required: true },
  user: { type: Object, required: true },
  profileUrl: { type: String, required: true },
});
const emit = defineEmits(['joined', 'create']);

const query = ref('');
const picked = ref([]);
const within = ref(0);
const results = ref([]);
const loading = ref(true);
const error = ref('');
const joining = ref(null);
const joinError = ref({});

const hasPoint = computed(() => props.user.latitude != null && props.user.longitude != null);
// Choices in the Filters panel that are on (the search box isn't counted).
const filterCount = computed(() => picked.value.length + (within.value ? 1 : 0));
const filtered = computed(() => !!(query.value.trim() || filterCount.value));
const labelOf = (key) => (props.categories.find((c) => c.value === key) || {}).label || key;

// Ignore answers to older requests when filters change quickly.
let request = 0;
let timer = null;

async function load() {
  const id = ++request;
  loading.value = true;
  error.value = '';
  const params = new URLSearchParams();
  if (query.value.trim()) params.append('q', query.value.trim());
  for (const key of picked.value) params.append('category', key);
  if (within.value) params.append('within', within.value);
  try {
    // apiGet takes an object, which can't repeat `category`, so build the URL here.
    const qs = params.toString();
    const data = await apiGet(qs ? `${props.communitiesApi}?${qs}` : props.communitiesApi);
    if (id === request) results.value = data;
  } catch (err) {
    if (id === request) error.value = parseErrors(err).message || 'Could not load communities.';
  } finally {
    if (id === request) loading.value = false;
  }
}

onMounted(load);
onBeforeUnmount(() => clearTimeout(timer));

// Typing waits a moment; chips search straight away.
watch(query, () => {
  clearTimeout(timer);
  timer = setTimeout(load, 300);
});
watch([picked, within], load);

function toggleCategory(key) {
  picked.value = picked.value.includes(key) ? picked.value.filter((k) => k !== key) : [...picked.value, key];
}

// Picking the chosen distance again turns the distance filter off.
function toggleDistance(km) {
  within.value = within.value === km ? 0 : km;
}

function clearChoices() {
  picked.value = [];
  within.value = 0;
}

function clearFilters() {
  query.value = '';
  clearChoices();
}

async function join(community) {
  joining.value = community.id;
  joinError.value = { ...joinError.value, [community.id]: '' };
  try {
    const res = await apiPost(`${props.communitiesApi}${community.id}/join/`);
    community.is_member = res.is_member;
    community.members_count = res.members_count;
    emit('joined', { ...community });
  } catch (err) {
    joinError.value = { ...joinError.value, [community.id]: parseErrors(err).message || 'Could not join. Please try again.' };
  } finally {
    joining.value = null;
  }
}

function open(community) {
  window.circleNavigate(community.url);
}

const formatKm = (km) => (km < 1 ? `${Math.round(km * 1000)} m` : `${km < 10 ? km.toFixed(1) : Math.round(km)} km`);
const shortPlace = (place) => place.split(',').slice(0, 2).join(',');
</script>

<style scoped>
.discover {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ---------- search + filters ---------- */
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search {
  display: flex;
  flex: 1;
  align-items: center;
  gap: 8px;
  min-width: 0;
  height: 44px;
  padding: 0 14px;
  color: var(--muted);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 10px;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}

.search:focus-within {
  color: var(--text);
  background: var(--surface);
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.search input {
  flex: 1;
  min-width: 0;
  height: 100%;
  font: inherit;
  color: var(--text);
  background: none;
  border: 0;
  outline: none;
}

.active {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: -6px 0 0;
  padding: 0;
  list-style: none;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 10px 0 12px;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-soft);
  border: 1px solid #c9dafa;
  border-radius: 999px;
  cursor: pointer;
}

.pill:hover {
  border-color: var(--primary);
}

/* ---------- results ---------- */
.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.bar__count {
  font-size: 14px;
  font-weight: 600;
  color: var(--muted);
}

.bar__clear {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  font: inherit;
  font-size: 14px;
  font-weight: 600;
  color: var(--primary);
  background: none;
  border: 0;
  cursor: pointer;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

/* Same box as Profile's cards. */
.ccard {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 16px;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.ccard:hover {
  border-color: #c9dafa;
  box-shadow: 0 0 0 4px var(--focus);
}

.ccard__cover {
  position: relative;
  display: grid;
  place-items: center;
  height: 110px;
  background:
    radial-gradient(400px 120px at 85% 0%, rgba(34, 184, 201, 0.55), transparent 70%),
    linear-gradient(120deg, #1f6fe5 0%, #13284a 100%);
  background-position: center;
  background-size: cover;
}

.ccard__cover:hover {
  text-decoration: none;
}

.ccard__initial {
  font-size: 40px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.badge {
  position: absolute;
  top: 8px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 9px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: rgba(8, 19, 31, 0.55);
  border-radius: 999px;
}

.badge--category {
  left: 8px;
}

.badge--distance {
  right: 8px;
}

.ccard__body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8px;
  padding: 14px 14px 16px;
}

.ccard__name {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  line-height: 1.3;
}

.ccard__name a {
  color: var(--text);
}

.ccard__text {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  font-size: 14px;
  line-height: 1.45;
  color: var(--muted);
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.ccard__text--empty {
  font-style: italic;
}

.ccard__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
  margin: 0;
  font-size: 13px;
  color: var(--muted);
}

.ccard__meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.ccard__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 6px;
}

.ccard__view {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 14px;
}

.ccard__arrow {
  transform: rotate(-90deg);
}

.ccard__error {
  margin: 0;
  font-size: 13px;
  color: var(--danger);
}
</style>
