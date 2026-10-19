<!--
  A form field for a place: shows the chosen location (with a small map
  when it has a pin) and a Set/Change button that opens LocationPicker —
  in a popup, or `inline` below the field (use inline inside another popup).
  v-model is { label, lat, lng }.
  Usage: <LocationField v-model="place" :tile-url="mapTileUrl" :search-api="mapSearchApi" :reverse-api="mapReverseApi" />
-->
<template>
  <div class="lfield">
    <span class="lfield__label">{{ label }}</span>

    <template v-if="!editingInline">
      <div v-if="modelValue.lat != null" class="lfield__map">
        <MapView :key="`${modelValue.lat},${modelValue.lng}`" :tile-url="tileUrl" :lat="modelValue.lat" :lng="modelValue.lng" />
      </div>
      <div class="lfield__row">
        <span class="lfield__value" :class="{ 'lfield__value--empty': !modelValue.label }">
          <Icon name="pin" :size="16" /> {{ modelValue.label || 'Not set' }}
        </span>
        <ActionButton
          :icon="modelValue.label ? 'edit' : 'pin'"
          :label="modelValue.label ? 'Change' : 'Set location'"
          size="sm"
          variant="secondary"
          @click="open"
        />
        <ActionButton v-if="modelValue.label" icon="trash" label="Remove" size="sm" variant="secondary" compact @click="clear" />
      </div>
    </template>

    <!-- Inline editor (inside another popup) -->
    <div v-else class="lfield__inline">
      <LocationPicker v-model="draft" :tile-url="tileUrl" :search-api="searchApi" :reverse-api="reverseApi" />
      <div class="lfield__inline-actions">
        <ActionButton icon="close" label="Cancel" size="sm" variant="secondary" @click="editingInline = false" />
        <ActionButton icon="check" label="Use this location" size="sm" :disabled="!draft.label.trim()" @click="apply" />
      </div>
    </div>

    <p v-if="error" class="lfield__error">{{ error }}</p>

    <Modal v-if="popupOpen" :title="title" wide @close="popupOpen = false">
      <LocationPicker v-model="draft" :tile-url="tileUrl" :search-api="searchApi" :reverse-api="reverseApi" />
      <template #footer>
        <ActionButton icon="close" label="Cancel" variant="secondary" @click="popupOpen = false" />
        <ActionButton icon="check" label="Use this location" :disabled="!draft.label.trim()" @click="apply" />
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import ActionButton from './ActionButton.vue';
import Icon from './Icon.vue';
import LocationPicker from './LocationPicker.vue';
import MapView from './MapView.vue';
import Modal from './Modal.vue';

const props = defineProps({
  modelValue: { type: Object, required: true },
  tileUrl: { type: String, required: true },
  searchApi: { type: String, required: true },
  reverseApi: { type: String, required: true },
  label: { type: String, default: 'Location' },
  title: { type: String, default: 'Location' },
  inline: { type: Boolean, default: false },
  error: { type: String, default: '' },
});
const emit = defineEmits(['update:modelValue']);

const draft = ref({ label: '', lat: null, lng: null });
const popupOpen = ref(false);
const editingInline = ref(false);

function open() {
  draft.value = { ...props.modelValue };
  if (props.inline) editingInline.value = true;
  else popupOpen.value = true;
}

function apply() {
  emit('update:modelValue', { ...draft.value, label: draft.value.label.trim() });
  popupOpen.value = false;
  editingInline.value = false;
}

function clear() {
  emit('update:modelValue', { label: '', lat: null, lng: null });
}
</script>

<style scoped>
.lfield {
  margin-bottom: 16px;
}

.lfield__label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 600;
}

.lfield__map {
  height: 150px;
  margin-bottom: 8px;
}

.lfield__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 6px 6px 6px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.lfield__value {
  display: inline-flex;
  flex: 1;
  align-items: center;
  gap: 6px;
  min-width: 0;
  font-weight: 500;
  overflow-wrap: anywhere;
}

.lfield__value--empty {
  font-weight: 400;
  font-style: italic;
  color: var(--muted);
}

.lfield__inline {
  padding: 12px;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.lfield__inline-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.lfield__error {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--danger);
}
</style>
