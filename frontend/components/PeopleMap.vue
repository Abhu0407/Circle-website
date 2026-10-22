<!--
  OpenStreetMap map with a pin for every person who has set a location.
  Hovering (or tapping) a pin shows that person's username.
  Usage: <PeopleMap :tile-url="..." :people="mapPeople" :me="user" [large] [:place="..."] />
    large: a tall map that also zooms with the scroll wheel (for a popup)
    people: [{ id, username, lat, lng }]   (everyone else)
    me:     the signed-in user ({ username, latitude, longitude }); shown as "You"
    place:  { label, lat, lng } a square pin for a place (e.g. where a community meets)
-->
<template>
  <div class="peoplemap" :class="{ 'peoplemap--large': large }">
    <div ref="el" class="peoplemap__canvas"></div>
    <p v-if="error" class="peoplemap__error">{{ error }}</p>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { loadLeaflet } from '../leaflet.mjs';

const props = defineProps({
  tileUrl: { type: String, required: true },
  people: { type: Array, default: () => [] },
  me: { type: Object, default: null },
  large: { type: Boolean, default: false },
  place: { type: Object, default: null },
});

// Shown when nobody has a point yet (India).
const FALLBACK = { center: [21.0, 78.0], zoom: 4 };
const MAX_FIT_ZOOM = 12;
const GRADIENTS = [
  ['#22b8c9', '#1f6fe5'],
  ['#f59f00', '#e8590c'],
  ['#be4bdb', '#7048e8'],
  ['#2fb36d', '#0c8599'],
  ['#e0475b', '#c2255c'],
];

const el = ref(null);
const error = ref('');
let map = null;
let layer = null;
let L = null;

// Tooltip content as a DOM node, so usernames are never parsed as HTML.
function label(text) {
  const span = document.createElement('span');
  span.textContent = text;
  return span;
}

function pin(letter, colors, isMe, isPlace = false) {
  const span = document.createElement('span');
  span.className = isPlace ? 'people-pin__dot people-pin__dot--place' : isMe ? 'people-pin__dot people-pin__dot--me' : 'people-pin__dot';
  span.style.setProperty('--a', colors[0]);
  span.style.setProperty('--b', colors[1]);
  const inner = document.createElement('span');
  inner.textContent = letter;
  span.appendChild(inner);
  return L.divIcon({ className: 'people-pin', html: span, iconSize: [28, 28], iconAnchor: [14, 28] });
}

function addPin(lat, lng, username, colors, isMe) {
  L.marker([lat, lng], { icon: pin(isMe ? '★' : username.charAt(0).toUpperCase(), colors, isMe), keyboard: false })
    .bindTooltip(label(isMe ? `${username} (you)` : username), {
      direction: 'top',
      offset: [0, -28],
      className: 'people-pin__tip',
    })
    .addTo(layer);
}

function drawPins() {
  if (!map) return;
  layer.clearLayers();
  const points = [];
  for (const p of props.people) {
    addPin(p.lat, p.lng, p.username, GRADIENTS[p.id % GRADIENTS.length], false);
    points.push([p.lat, p.lng]);
  }
  const place = props.place;
  if (place && place.lat != null && place.lng != null) {
    L.marker([place.lat, place.lng], { icon: pin('⌂', ['#13284a', '#1f6fe5'], false, true), keyboard: false })
      .bindTooltip(label(place.label), { direction: 'top', offset: [0, -28], className: 'people-pin__tip' })
      .addTo(layer);
    points.push([place.lat, place.lng]);
  }
  const me = props.me;
  if (me && me.latitude != null && me.longitude != null) {
    addPin(me.latitude, me.longitude, me.username, ['#1f6fe5', '#0b3d91'], true);
    points.push([me.latitude, me.longitude]);
  }

  if (points.length) map.fitBounds(points, { padding: [24, 24], maxZoom: MAX_FIT_ZOOM });
  else map.setView(FALLBACK.center, FALLBACK.zoom);
}

onMounted(async () => {
  try {
    L = await loadLeaflet();
  } catch (err) {
    error.value = err.message;
    return;
  }
  if (!el.value) return; // unmounted while loading

  map = L.map(el.value, { scrollWheelZoom: props.large, boxZoom: false, attributionControl: false });
  L.tileLayer(props.tileUrl, {
    maxZoom: 19,
  }).addTo(map);
  layer = L.layerGroup().addTo(map);
  drawPins();
});

// Redraw when the signed-in user moves their own point (Profile page).
watch(() => [props.people, props.me?.latitude, props.me?.longitude, props.me?.username, props.place?.lat, props.place?.lng], drawPins);

onBeforeUnmount(() => {
  if (map) map.remove();
  map = null;
});
</script>

<style scoped>
.peoplemap {
  position: relative;
  /* Keep Leaflet's high z-index panes and controls inside the map. */
  isolation: isolate;
  height: 230px;
  overflow: hidden;
  background: #dbe6f0;
  border-radius: 12px;
}

.peoplemap--large {
  height: min(72vh, 720px);
  min-height: 320px;
}

.peoplemap__canvas {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.peoplemap__error {
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
/* Leaflet builds the marker and tooltip elements itself, so these can't be scoped. */
.people-pin {
  background: none;
  border: 0;
}

.people-pin__dot {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--a), var(--b));
  border: 2px solid #fff;
  border-radius: 50% 50% 50% 0;
  box-shadow: 0 4px 10px rgba(8, 19, 31, 0.3);
  transform: rotate(-45deg);
  cursor: pointer;
}

/* Keep the letter upright inside the rotated pin. */
.people-pin__dot > span {
  transform: rotate(45deg);
}

.people-pin__dot--me {
  border-width: 3px;
  box-shadow: 0 0 0 5px rgba(31, 111, 229, 0.25), 0 4px 10px rgba(8, 19, 31, 0.3);
}

/* A place (not a person): square-ish dark pin. */
.people-pin__dot--place {
  font-size: 15px;
  border-radius: 8px 8px 8px 0;
}

.people-pin__tip {
  padding: 4px 10px;
  font: 600 13px/1.3 Inter, system-ui, sans-serif;
  color: #fff;
  background: var(--night-800, #0b1a2b);
  border: 0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(8, 19, 31, 0.3);
}

.people-pin__tip.leaflet-tooltip-top::before {
  border-top-color: var(--night-800, #0b1a2b);
}
</style>
