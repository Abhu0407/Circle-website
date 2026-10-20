<!--
  Create a community (inside the page's PageSheet). The header previews the
  community as you type; its picture (cover and round picture) is one of the
  site's drawings for the chosen category (`covers`), changeable later.
  The creator joins it, and the browser goes to the new community's page.
  The category is picked from `categories` (required, can't be changed later).
  The location is picked like on Profile (search or click the map).
  Usage:
    <CommunityForm :communities-api="communitiesApi" :categories="communityCategories" :covers="communityCovers"
                   :user="user" :map-tile-url="mapTileUrl" :map-search-api="mapSearchApi" :map-reverse-api="mapReverseApi" />
-->
<template>
  <form class="cform" novalidate @submit.prevent="submit">
    <!-- ---------- Live preview ---------- -->
    <PageHero
      :name="form.name.trim() || 'Community name'"
      :placeholder="!form.name.trim()"
      :cover="coverUrl"
      :picture="coverUrl"
      :initial="initial"
    >
      <template #meta>
        <span><Icon name="compass" :size="14" /> {{ categoryLabel || 'No category yet' }}</span>
        <span><Icon name="pin" :size="14" /> {{ place.label || 'No location' }}</span>
      </template>
    </PageHero>

    <CardGrid>
      <!-- ---------- Basic info ---------- -->
      <SectionCard title="Basic info">
        <FormField id="community-name" v-model="form.name" label="Name" placeholder="e.g. Sunday Hikers" required :error="errors.name" />
        <fieldset class="category" :class="{ 'category--error': errors.category }">
          <legend class="category__label">Category <span class="category__req">required</span></legend>
          <div class="category__list" role="group" aria-label="Category">
            <FilterChip
              v-for="c in categories"
              :key="c.value"
              :on="form.category === c.value"
              @click="pickCategory(c.value)"
            >{{ c.label }}</FilterChip>
          </div>
          <p v-if="errors.category" class="category__error">{{ errors.category }}</p>
          <p v-else class="category__hint"><Icon name="lock" :size="12" /> You can't change the category after creating the community.</p>
        </fieldset>
      </SectionCard>

      <!-- ---------- Details ---------- -->
      <SectionCard title="Details">
        <LocationField
          v-model="place"
          title="Where does the community meet?"
          :tile-url="mapTileUrl"
          :search-api="mapSearchApi"
          :reverse-api="mapReverseApi"
          :error="errors.location || errors.latitude"
        />
        <div class="area" :class="{ 'area--error': errors.description }">
          <label for="community-description" class="area__label">Description</label>
          <textarea
            id="community-description"
            v-model="form.description"
            rows="5"
            placeholder="What is this community about? When and where do you meet?"
          ></textarea>
          <p v-if="errors.description" class="area__error">{{ errors.description }}</p>
        </div>
      </SectionCard>

      <!-- ---------- Picture ---------- -->
      <SectionCard title="Picture" wide>
        <CoverPicker v-if="categoryCovers.length" v-model="form.cover" :covers="categoryCovers" />
        <p v-else class="hint">Pick a category to see its pictures.</p>
        <p v-if="errors.cover" class="area__error">{{ errors.cover }}</p>
      </SectionCard>
    </CardGrid>

    <p v-if="message" class="error" role="alert">{{ message }}</p>

    <div class="actions">
      <span class="actions__hint">You'll be the first member.</span>
      <ActionButton
        type="submit"
        icon="plus"
        :label="saving ? 'Creating…' : 'Create community'"
        :disabled="saving || !form.name.trim() || !form.category"
      />
    </div>
  </form>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { apiPost, parseErrors } from '../api.mjs';
import ActionButton from './ActionButton.vue';
import CardGrid from './CardGrid.vue';
import CoverPicker from './CoverPicker.vue';
import FilterChip from './FilterChip.vue';
import FormField from './FormField.vue';
import Icon from './Icon.vue';
import LocationField from './LocationField.vue';
import PageHero from './PageHero.vue';
import SectionCard from './SectionCard.vue';

const props = defineProps({
  communitiesApi: { type: String, required: true },
  // [{ value, label }] from the server; the last one is "Other".
  categories: { type: Array, required: true },
  // { category: [{ value, label, url }] } from the server; the first is the default.
  covers: { type: Object, required: true },
  mapTileUrl: { type: String, required: true },
  mapSearchApi: { type: String, required: true },
  mapReverseApi: { type: String, required: true },
  user: { type: Object, required: true },
});

const form = reactive({ name: '', category: '', cover: '', description: '' });
// Starts at your own location from Profile.
const place = ref({ label: props.user.location || '', lat: props.user.latitude ?? null, lng: props.user.longitude ?? null });
const errors = ref({});
const message = ref('');
const saving = ref(false);

const categoryLabel = computed(() => (props.categories.find((c) => c.value === form.category) || {}).label);
const initial = computed(() => (form.name.trim().charAt(0) || '?').toUpperCase());
const categoryCovers = computed(() => props.covers[form.category] || []);
const coverUrl = computed(() => (categoryCovers.value.find((c) => c.value === form.cover) || {}).url || '');

// Each category has its own pictures; start on its first one.
function pickCategory(value) {
  if (form.category === value) return;
  form.category = value;
  form.cover = (categoryCovers.value[0] || {}).value || '';
}

async function submit() {
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
    const community = await apiPost(props.communitiesApi, data);
    window.circleNavigate(community.url);
  } catch (err) {
    const { fieldErrors, message: text } = parseErrors(err);
    errors.value = fieldErrors;
    message.value = text;
    saving.value = false;
  }
}
</script>

<style scoped>
.cform {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ---------- fields ---------- */
.category {
  margin: 0;
  padding: 0;
  border: 0;
}

.category__label {
  margin-bottom: 8px;
  padding: 0;
  font-size: 14px;
  font-weight: 600;
}

.category__req {
  margin-left: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--muted);
}

.category__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category--error .category__list {
  padding: 6px;
  border: 1px solid var(--danger);
  border-radius: 12px;
}

.category__hint,
.category__error {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.category__error {
  color: var(--danger);
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
  transition: border-color 0.15s, box-shadow 0.15s;
}

.area textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.area--error textarea {
  border-color: var(--danger);
}

.hint {
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}

.area__error {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--danger);
}

.error {
  margin: 0;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--danger);
  background: var(--danger-bg);
  border-radius: 10px;
}

/* ---------- submit ---------- */
.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.actions__hint {
  margin-right: auto;
  font-size: 14px;
  color: var(--muted);
}
</style>
