<!--
  Pick a place, the same way as on Profile: search for a city or area, or
  click the map to drop a pin (its name is looked up), and edit the name.
  v-model is { label, lat, lng } (lat/lng null when only a name is typed).
  Usage: <LocationPicker v-model="draft" :tile-url="mapTileUrl" :search-api="mapSearchApi" :reverse-api="mapReverseApi" />
-->
<template>
  <div class="picker">
    <div class="search">
      <label class="search__box">
        <Icon name="search" :size="18" />
        <input
          v-model="query"
          type="search"
          placeholder="Search for a city or area"
          aria-label="Search for a place"
          @input="searchPlaces"
          @keydown.enter.prevent
        />
      </label>
      <ul v-if="results.length" class="results">
        <li v-for="(r, i) in results" :key="i">
          <button type="button" @click="choose(r)"><Icon name="pin" :size="14" /> {{ r.label }}</button>
        </li>
      </ul>
      <p v-else-if="searching" class="status">Searching…</p>
      <p v-else-if="query.trim() && searched" class="status">No places found.</p>
    </div>

    <div class="map">
      <MapView :tile-url="tileUrl" :lat="modelValue.lat" :lng="modelValue.lng" interactive @pick="pickPoint" />
    </div>
    <p class="tip"><Icon name="target" :size="14" /> Click the map to drop the pin.</p>

    <label class="name">
      <span>Location name</span>
      <input
        :value="modelValue.label"
        type="text"
        maxlength="255"
        placeholder="e.g. Bandra West, Mumbai"
        @input="update({ label: $event.target.value })"
      />
    </label>
    <p v-if="lookingUp" class="status">Finding the place name…</p>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue';
import { apiGet, parseErrors } from '../api.mjs';
import Icon from './Icon.vue';
import MapView from './MapView.vue';

const props = defineProps({
  modelValue: { type: Object, required: true },
  tileUrl: { type: String, required: true },
  searchApi: { type: String, required: true },
  reverseApi: { type: String, required: true },
});
const emit = defineEmits(['update:modelValue']);

const query = ref('');
const results = ref([]);
const searching = ref(false);
const searched = ref(false);
const lookingUp = ref(false);
const error = ref('');
let searchTimer = null;
let lookupId = 0;

onBeforeUnmount(() => clearTimeout(searchTimer));

function update(changes) {
  emit('update:modelValue', { ...props.modelValue, ...changes });
}

// Photon GeoJSON feature -> { label, lat, lng }
function toPlace(feature) {
  const p = feature.properties || {};
  const parts = [p.name, p.district || p.locality, p.city, p.state, p.country];
  const unique = parts.filter((part, i) => part && parts.indexOf(part) === i);
  const [lng, lat] = feature.geometry.coordinates;
  return { label: unique.slice(0, 4).join(', '), lat, lng };
}

function searchPlaces() {
  clearTimeout(searchTimer);
  const q = query.value.trim();
  searched.value = false;
  if (!q) {
    results.value = [];
    return;
  }
  searching.value = true;
  searchTimer = setTimeout(async () => {
    const params = { q };
    if (props.modelValue.lat != null) Object.assign(params, { lat: props.modelValue.lat, lon: props.modelValue.lng });
    try {
      const res = await apiGet(props.searchApi, params);
      if (query.value.trim() !== q) return;
      results.value = (res.features || []).map(toPlace);
      error.value = '';
    } catch (err) {
      results.value = [];
      error.value = parseErrors(err).message;
    } finally {
      searching.value = false;
      searched.value = true;
    }
  }, 350);
}

function choose(place) {
  update(place);
  results.value = [];
  query.value = '';
  searched.value = false;
}

async function pickPoint({ lat, lng }) {
  update({ lat, lng });
  error.value = '';
  const id = ++lookupId;
  lookingUp.value = true;
  try {
    const res = await apiGet(props.reverseApi, { lat, lon: lng });
    const feature = (res.features || [])[0];
    if (id === lookupId && feature) update({ lat, lng, label: toPlace(feature).label });
  } catch {
    // Keep whatever name is typed; the pin is still used.
  } finally {
    if (id === lookupId) lookingUp.value = false;
  }
}
</script>

<style scoped>
button {
  font: inherit;
  cursor: pointer;
}

.search {
  position: relative;
  margin-bottom: 12px;
}

.search__box {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 44px;
  padding: 0 14px;
  color: var(--muted);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 10px;
}

.search__box:focus-within {
  background: var(--surface);
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.search__box input {
  flex: 1;
  min-width: 0;
  height: 100%;
  font: inherit;
  color: var(--text);
  background: none;
  border: 0;
  outline: none;
}

.results {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  left: 0;
  z-index: 500;
  margin: 0;
  padding: 6px;
  list-style: none;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: var(--shadow);
}

.results button {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  font-size: 14px;
  text-align: left;
  color: var(--text);
  background: none;
  border: 0;
  border-radius: 8px;
}

.results button:hover {
  background: var(--surface-muted);
}

.status {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.map {
  height: 280px;
}

.tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 8px 0 14px;
  font-size: 13px;
  color: var(--muted);
}

.name {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
}

.name input {
  height: 44px;
  padding: 0 14px;
  font: inherit;
  font-weight: 400;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  outline: none;
}

.name input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.error {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--danger);
}

@media (max-width: 560px) {
  .map {
    height: 220px;
  }
}
</style>
