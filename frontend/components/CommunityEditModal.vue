<!--
  Edit a community (its creator only): picture (one of `covers`, the
  site's drawings for its category), name, location (picked like on
  Profile, right in this popup), description.
  The category is shown but locked; it can't be changed after creating.
  Emits `saved` with the updated community, `close` to dismiss.
  Usage:
    <CommunityEditModal v-if="editing" :community="c" :api="communityApi" :covers="communityCovers[c.category]" :map-tile-url="mapTileUrl"
                        :map-search-api="mapSearchApi" :map-reverse-api="mapReverseApi" @saved="..." @close="editing = false" />
-->
<template>
  <Modal title="Edit community" wide @close="close">
    <form id="community-edit" class="edit" novalidate @submit.prevent="save">
      <div class="picture">
        <span class="picture__label">Picture</span>
        <CoverPicker v-model="form.cover" :covers="covers" />
        <p v-if="errors.cover" class="field-error">{{ errors.cover }}</p>
      </div>

      <FormField id="edit-community-name" v-model="form.name" label="Name" required :error="errors.name" />

      <div class="locked">
        <span class="locked__label">Category</span>
        <div class="locked__value">
          <span>{{ community.category_label }}</span>
          <Icon name="lock" :size="14" />
        </div>
        <p class="locked__hint">The category is set when the community is created and can't be changed.</p>
      </div>

      <LocationField
        v-model="place"
        inline
        :tile-url="mapTileUrl"
        :search-api="mapSearchApi"
        :reverse-api="mapReverseApi"
        :error="errors.location || errors.latitude"
      />

      <div class="area">
        <label for="edit-community-description" class="area__label">Description</label>
        <textarea
          id="edit-community-description"
          v-model="form.description"
          rows="5"
          placeholder="What is this community about? When and where do you meet?"
        ></textarea>
        <p v-if="errors.description" class="field-error">{{ errors.description }}</p>
      </div>

      <p v-if="message" class="alert" role="alert">{{ message }}</p>
    </form>

    <template #footer>
      <ActionButton icon="close" label="Cancel" variant="secondary" @click="close" />
      <ActionButton type="submit" form="community-edit" icon="check" :label="saving ? 'Saving…' : 'Save changes'" :disabled="saving || !form.name.trim()" />
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { apiPatch, parseErrors } from '../api.mjs';
import ActionButton from './ActionButton.vue';
import CoverPicker from './CoverPicker.vue';
import FormField from './FormField.vue';
import Icon from './Icon.vue';
import LocationField from './LocationField.vue';
import Modal from './Modal.vue';

// community: see CommunityDetailSerializer; api: PATCH /api/communities/<id>/
const props = defineProps({
  community: { type: Object, required: true },
  api: { type: String, required: true },
  // [{ value, label, url }]: the pictures for the community's category.
  covers: { type: Array, required: true },
  mapTileUrl: { type: String, required: true },
  mapSearchApi: { type: String, required: true },
  mapReverseApi: { type: String, required: true },
});
const emit = defineEmits(['saved', 'close']);

const form = reactive({
  name: props.community.name,
  cover: props.community.cover,
  description: props.community.description,
});
const place = ref({ label: props.community.location, lat: props.community.latitude, lng: props.community.longitude });
const errors = ref({});
const message = ref('');
const saving = ref(false);

const dirty = computed(() =>
  form.cover !== props.community.cover
  || form.name !== props.community.name
  || place.value.label !== props.community.location
  || place.value.lat !== props.community.latitude
  || form.description !== props.community.description
);

function close() {
  if (saving.value) return;
  if (dirty.value && !window.confirm('Discard your changes?')) return;
  emit('close');
}

async function save() {
  if (saving.value) return;
  saving.value = true;
  errors.value = {};
  message.value = '';
  const { lat, lng } = place.value;
  const data = {
    ...form,
    location: place.value.label,
    latitude: lat == null ? null : +lat.toFixed(6),
    longitude: lng == null ? null : +lng.toFixed(6),
  };
  try {
    emit('saved', await apiPatch(props.api, data));
  } catch (err) {
    const { fieldErrors, message: text } = parseErrors(err);
    errors.value = fieldErrors;
    message.value = text;
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.edit {
  padding-bottom: 4px;
}

.picture {
  margin-bottom: 18px;
}

.picture__label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
}

/* Category: shown like a field, but locked (as the email on Profile). */
.locked {
  margin-bottom: 16px;
}

.locked__label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 600;
}

.locked__value {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 14px;
  color: var(--muted);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.locked__value span {
  font-weight: 500;
  color: var(--text);
}

.locked__hint {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.area__label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 600;
}

.area textarea {
  display: block;
  width: 100%;
  padding: 10px 14px;
  font: inherit;
  line-height: 1.5;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  outline: none;
  resize: vertical;
}

.area textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.field-error {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--danger);
}

.alert {
  margin: 16px 0 0;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--danger);
  background: var(--danger-bg);
  border-radius: 10px;
}
</style>
