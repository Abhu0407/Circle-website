<!--
  OpenStreetMap map with one pin. Tiles come through Django (apps/maps).
  Usage: <MapView :tile-url="..." :lat="19.07" :lng="72.87" interactive @pick="onPick" />
  When `interactive`, clicking the map emits `pick` with { lat, lng }.
-->
<template>
  <div class="mapview">
    <div ref="el" class="mapview__canvas"></div>
    <p v-if="error" class="mapview__error">{{ error }}</p>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { loadLeaflet } from '../leaflet.mjs';

const props = defineProps({
  tileUrl: { type: String, required: true },
  lat: { type: Number, default: null },
  lng: { type: Number, default: null },
  interactive: { type: Boolean, default: false },
});
const emit = defineEmits(['pick']);

// Shown when there is no point yet (India).
const FALLBACK = { center: [21.0, 78.0], zoom: 4 };
const POINT_ZOOM = 13;

const el = ref(null);
const error = ref('');
let map = null;
let marker = null;
let L = null;

const hasPoint = () => props.lat != null && props.lng != null;

function placeMarker() {
  if (!map) return;
  if (!hasPoint()) {
    if (marker) marker.remove();
    marker = null;
    return;
  }
  const latLng = [props.lat, props.lng];
  if (marker) marker.setLatLng(latLng);
  else {
    marker = L.marker(latLng, {
      icon: L.divIcon({ className: 'circle-pin', html: '<span></span>', iconSize: [28, 28], iconAnchor: [14, 28] }),
      keyboard: false,
    }).addTo(map);
  }
  map.setView(latLng, Math.max(map.getZoom(), POINT_ZOOM));
}

onMounted(async () => {
  try {
    L = await loadLeaflet();
  } catch (err) {
    error.value = err.message;
    return;
  }
  if (!el.value) return; // unmounted while loading

  map = L.map(el.value, {
    zoomControl: props.interactive,
    dragging: props.interactive,
    scrollWheelZoom: props.interactive,
    doubleClickZoom: props.interactive,
    touchZoom: props.interactive,
    boxZoom: false,
    keyboard: props.interactive,
    attributionControl: true,
  });
  map.attributionControl.setPrefix(false);
  L.tileLayer(props.tileUrl, {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>',
  }).addTo(map);

  if (hasPoint()) map.setView([props.lat, props.lng], POINT_ZOOM);
  else map.setView(FALLBACK.center, FALLBACK.zoom);
  placeMarker();

  if (props.interactive) {
    map.on('click', (e) => emit('pick', { lat: e.latlng.lat, lng: e.latlng.lng }));
  }
});

watch(() => [props.lat, props.lng], placeMarker);

onBeforeUnmount(() => {
  if (map) map.remove();
  map = null;
});
</script>

<style scoped>
.mapview {
  position: relative;
  /* Keep Leaflet's high z-index panes and controls inside the map. */
  isolation: isolate;
  height: 100%;
  min-height: 160px;
  overflow: hidden;
  background: #dbe6f0;
  border-radius: 12px;
}

.mapview__canvas {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.mapview__error {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  margin: 0;
  padding: 16px;
  font-size: 14px;
  text-align: center;
  color: var(--muted);
}
</style>

<style>
/* Leaflet builds the marker element itself, so this can't be scoped. */
.circle-pin span {
  display: block;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, var(--teal), var(--primary));
  border: 3px solid #fff;
  border-radius: 50% 50% 50% 0;
  box-shadow: 0 4px 10px rgba(8, 19, 31, 0.3);
  transform: rotate(-45deg);
}

.circle-pin {
  background: none;
  border: 0;
}
</style>
