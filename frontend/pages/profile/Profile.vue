<!--
  The Profile page (/profile/). Every change is saved straight away via
  PATCH meApi; the sidebar (name, avatar, location) updates with it.
-->
<template>
  <BaseLayout
    :user="me"
    active="profile"
    :home-url="homeUrl"
    :profile-url="profileUrl"
    :signout-api="signoutApi"
    :signin-url="signinUrl"
    :map-tile-url="mapTileUrl"
    :chats-api="chatsApi"
    :chat-socket-path="chatSocketPath"
    :chat-max-file-mb="chatMaxFileMb"
    :map-people="mapPeople"
    :events="events"
  >
    <section class="profile">
      <h1 class="profile__title">My Profile</h1>

      <!-- One full-page box holding every profile section. -->
      <div class="sheet">

      <!-- ---------- Header card ---------- -->
      <article class="hero">
        <div class="hero__cover" aria-hidden="true"></div>

        <div class="hero__row">
          <div class="photo">
            <img v-if="me.profile_picture" :src="me.profile_picture" alt="" class="photo__img" />
            <span v-else class="photo__initial">{{ initial }}</span>
            <button
              type="button"
              class="photo__btn"
              :disabled="savingAvatar"
              :aria-label="me.avatar ? 'Change avatar' : 'Choose an avatar'"
              @click="avatarOpen = true"
            >
              <Icon name="camera" :size="16" />
            </button>
            <span v-if="savingAvatar" class="photo__busy">Saving…</span>
          </div>

          <div class="hero__info">
            <h2 class="hero__name">{{ displayName }}</h2>
            <p class="hero__meta">
              <span>@{{ me.username }}</span>
              <span v-if="me.location"><Icon name="pin" :size="14" /> {{ shortLocation }}</span>
            </p>
          </div>

          <ActionButton class="hero__edit" icon="edit" label="Edit profile" compact @click="openEdit" />
        </div>

        <div class="hero__stats">
          <button type="button" class="stat" @click="scrollToCard(communitiesCard)">
            <span class="stat__text">
              <strong>{{ communities.length }}</strong>
              <span>{{ communities.length === 1 ? 'Community' : 'Communities' }}</span>
            </span>
          </button>
          <button type="button" class="stat" @click="scrollToCard(interestsCard)">
            <span class="stat__text">
              <strong>{{ interests.length }}</strong>
              <span>{{ interests.length === 1 ? 'Interest' : 'Interests' }}</span>
            </span>
          </button>
        </div>
      </article>

      <div class="cards">
        <!-- ---------- Basic info ---------- -->
        <article class="card">
          <header class="card__head">
            <h2 class="card__title">Basic info</h2>
            <ActionButton icon="edit" label="Edit" size="sm" compact @click="openEdit" />
          </header>
          <dl class="info">
            <div class="info__row">
              <dt><Icon name="user" :size="16" /> Name</dt>
              <dd :class="{ 'info__empty': !fullName }">{{ fullName || 'Not set' }}</dd>
            </div>
            <div class="info__row">
              <dt><Icon name="at" :size="16" /> Username</dt>
              <dd>{{ me.username }}</dd>
            </div>
            <div class="info__row">
              <dt><Icon name="mail" :size="16" /> Email</dt>
              <dd>
                <span>{{ me.email.split('@')[0] }}<wbr />@{{ me.email.split('@')[1] }}</span>
                <span class="locked" title="Your email can't be changed"><Icon name="lock" :size="12" /></span>
              </dd>
            </div>
            <div class="info__row">
              <dt><Icon name="pin" :size="16" /> Location</dt>
              <dd :class="{ 'info__empty': !me.location }">{{ me.location || 'Not set' }}</dd>
            </div>
          </dl>
        </article>

        <!-- ---------- Location ---------- -->
        <article class="card">
          <header class="card__head">
            <h2 class="card__title">Location</h2>
            <ActionButton v-if="me.location" icon="edit" label="Change" size="sm" compact @click="openLocation" />
          </header>
          <template v-if="hasPoint">
            <div class="card__map">
              <MapView :key="`${me.latitude},${me.longitude}`" :tile-url="mapTileUrl" :lat="me.latitude" :lng="me.longitude" />
            </div>
            <p class="card__caption"><Icon name="pin" :size="14" /> {{ me.location }}</p>
          </template>
          <div v-else-if="me.location" class="blank">
            <Icon name="pin" :size="28" />
            <p>{{ me.location }}</p>
            <ActionButton icon="pin" label="Pin it on the map" @click="openLocation" />
          </div>
          <div v-else class="blank">
            <Icon name="pin" :size="28" />
            <p>Add your location to find people and activities near you.</p>
            <ActionButton icon="pin" label="Set location" @click="openLocation" />
          </div>
        </article>

        <!-- ---------- Interests ---------- -->
        <article ref="interestsCard" class="card card--interests" :class="{ 'card--flash': flashing === interestsCard }">
          <header class="card__head">
            <h2 class="card__title">Interests <span class="card__count">{{ interests.length }} / {{ communityCategories.length }}</span></h2>
            <!-- When empty, only the button in the middle of the card is shown. -->
            <ActionButton
              v-if="interests.length"
              icon="edit"
              label="Edit interests"
              size="sm"
              compact
              @click="openInterests"
            />
          </header>

          <ul v-if="interests.length" class="tags">
            <li v-for="key in interests" :key="key" class="tag">
              <span>{{ labelOf(key) }}</span>
              <button type="button" class="tag__x" :aria-label="`Remove ${labelOf(key)}`" @click="removeInterest(key)">
                <Icon name="close" :size="12" />
              </button>
            </li>
          </ul>
          <div v-else class="blank">
            <Icon name="heart" :size="28" />
            <p>Add a few interests so others with the same hobbies can find you.</p>
            <ActionButton icon="plus" label="Add interests" @click="openInterests" />
          </div>
        </article>

        <!-- ---------- Communities ---------- -->
        <article ref="communitiesCard" class="card card--wide" :class="{ 'card--flash': flashing === communitiesCard }">
          <header class="card__head">
            <h2 class="card__title">My Communities</h2>
            <span class="card__count">{{ communities.length }}</span>
          </header>

          <ul v-if="communities.length" class="groups">
            <li v-for="c in communities" :key="c.id" class="group">
              <img v-if="c.image" :src="c.image" alt="" class="group__img" />
              <span v-else class="group__img group__img--initial" :style="gradientFor(c.name)">{{ c.name.charAt(0) }}</span>
              <div class="group__info">
                <a :href="c.url" class="group__name">{{ c.name }}</a>
                <span>
                  <template v-if="c.category_label">{{ c.category_label }} · </template>
                  {{ c.members_count }} {{ c.members_count === 1 ? 'member' : 'members' }}
                </span>
              </div>
              <div class="group__actions">
                <template v-if="confirmLeave === c.id">
                  <ActionButton icon="logout" label="Leave" size="sm" @click="leaveCommunity(c)" />
                  <ActionButton icon="close" label="Cancel" variant="secondary" size="sm" @click="confirmLeave = null" />
                </template>
                <ActionButton v-else icon="logout" label="Leave" size="sm" @click="confirmLeave = c.id" />
              </div>
            </li>
          </ul>
          <div v-else class="blank">
            <Icon name="users" :size="28" />
            <p>You haven't joined any communities yet.</p>
            <ActionButton icon="compass" label="Discover communities" @click="goHome" />
          </div>
        </article>
      </div>
      </div>

      <!-- ---------- Choose avatar ---------- -->
      <Modal v-if="avatarOpen" title="Choose an avatar" @close="avatarOpen = false">
        <AvatarPicker :model-value="me.avatar" :avatars="avatars" :disabled="savingAvatar" @update:model-value="pickAvatar" />
        <template #footer>
          <ActionButton
            v-if="me.avatar"
            icon="trash"
            label="Use my initial"
            variant="secondary"
            :disabled="savingAvatar"
            @click="pickAvatar('')"
          />
          <ActionButton icon="check" label="Done" @click="avatarOpen = false" />
        </template>
      </Modal>

      <!-- ---------- Edit basic info ---------- -->
      <Modal v-if="editOpen" title="Edit profile" @close="editOpen = false">
        <form id="edit-form" @submit.prevent="saveEdit">
          <div class="edit-photo">
            <div class="edit-photo__head">
              <img v-if="me.profile_picture" :src="me.profile_picture" alt="" class="edit-photo__img" />
              <span v-else class="edit-photo__img edit-photo__img--initial">{{ initial }}</span>
              <span class="edit-photo__label">Avatar</span>
              <ActionButton
                v-if="me.avatar"
                icon="trash"
                label="Use my initial"
                size="sm"
                variant="secondary"
                :disabled="savingAvatar"
                @click="pickAvatar('')"
              />
            </div>
            <AvatarPicker :model-value="me.avatar" :avatars="avatars" :disabled="savingAvatar" @update:model-value="pickAvatar" />
          </div>

          <FormField id="edit-name" v-model="form.name" label="Name" placeholder="Your name" :error="formErrors.name" />
          <FormField id="edit-username" v-model="form.username" label="Username" :error="formErrors.username || usernameError" />
          <p v-if="usernameStatus" class="hint" :class="`hint--${usernameStatus.kind}`">{{ usernameStatus.text }}</p>

          <div class="readonly">
            <span class="readonly__label">Email</span>
            <div class="readonly__value"><Icon name="lock" :size="14" /> {{ me.email }}</div>
            <p class="readonly__hint">Your email can't be changed.</p>
          </div>

          <p v-if="formMessage" class="form-error" role="alert">{{ formMessage }}</p>
        </form>

        <template #footer>
          <ActionButton icon="close" label="Cancel" variant="secondary" @click="editOpen = false" />
          <ActionButton
            type="submit"
            form="edit-form"
            icon="check"
            :label="saving ? 'Saving…' : 'Save changes'"
            :disabled="saving || !canSaveEdit"
          />
        </template>
      </Modal>

      <!-- ---------- Interests (community categories) ---------- -->
      <Modal v-if="interestsOpen" title="Your interests" wide @close="interestsOpen = false">
        <p class="pick-hint">Pick the kinds of communities you like. These are the same categories communities use.</p>
        <div class="suggest" role="group" aria-label="Interests">
          <button
            v-for="c in communityCategories"
            :key="c.value"
            type="button"
            class="suggest__chip"
            :class="{ 'suggest__chip--on': picked.includes(c.value) }"
            :aria-pressed="picked.includes(c.value)"
            @click="togglePicked(c.value)"
          >
            <Icon :name="picked.includes(c.value) ? 'check' : 'plus'" :size="12" /> {{ c.label }}
          </button>
        </div>

        <p v-if="interestError" class="form-error" role="alert">{{ interestError }}</p>
        <p v-else class="pick-hint">{{ picked.length }} selected</p>

        <template #footer>
          <ActionButton icon="close" label="Cancel" variant="secondary" @click="interestsOpen = false" />
          <ActionButton
            icon="check"
            :label="saving ? 'Saving…' : 'Save interests'"
            :disabled="saving || !interestsChanged"
            @click="saveInterests"
          />
        </template>
      </Modal>

      <!-- ---------- Location picker ---------- -->
      <Modal v-if="locationOpen" title="Your location" wide @close="locationOpen = false">
        <div class="loc-search">
          <label class="loc-search__box">
            <Icon name="search" :size="18" />
            <input
              v-model="placeQuery"
              type="search"
              placeholder="Search for a city or area"
              aria-label="Search for a place"
              @input="searchPlaces"
            />
          </label>
          <ul v-if="placeResults.length" class="loc-results">
            <li v-for="(r, i) in placeResults" :key="i">
              <button type="button" @click="choosePlace(r)">
                <Icon name="pin" :size="14" /> {{ r.label }}
              </button>
            </li>
          </ul>
          <p v-else-if="placeSearching" class="loc-status">Searching…</p>
          <p v-else-if="placeQuery.trim() && placeSearched" class="loc-status">No places found.</p>
        </div>

        <div class="loc-map">
          <MapView :tile-url="mapTileUrl" :lat="draft.lat" :lng="draft.lng" interactive @pick="pickPoint" />
        </div>
        <p class="loc-tip"><Icon name="target" :size="14" /> Click the map to drop your pin.</p>

        <label class="loc-label">
          <span>Location name</span>
          <input v-model="draft.label" type="text" maxlength="255" placeholder="e.g. Bandra West, Mumbai" />
        </label>
        <p v-if="draftLookingUp" class="loc-status">Finding the place name…</p>
        <p v-if="locationError" class="form-error" role="alert">{{ locationError }}</p>

        <template #footer>
          <ActionButton
            v-if="me.location"
            icon="trash"
            label="Remove location"
            :disabled="saving"
            @click="clearLocation"
          />
          <span class="spacer"></span>
          <ActionButton icon="close" label="Cancel" variant="secondary" @click="locationOpen = false" />
          <ActionButton
            icon="check"
            :label="saving ? 'Saving…' : 'Save location'"
            :disabled="saving || !draft.label.trim()"
            @click="saveLocation"
          />
        </template>
      </Modal>

      <!-- ---------- Toast ---------- -->
      <Teleport to="body">
        <div v-if="toast" class="toast" :class="`toast--${toast.kind}`" role="status">
          <Icon :name="toast.kind === 'error' ? 'close' : 'check'" :size="16" /> {{ toast.text }}
        </div>
      </Teleport>
    </section>
  </BaseLayout>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { apiGet, apiPatch, parseErrors } from '../../api.mjs';
import ActionButton from '../../components/ActionButton.vue';
import AvatarPicker from '../../components/AvatarPicker.vue';
import BaseLayout from '../../components/BaseLayout.vue';
import FormField from '../../components/FormField.vue';
import Icon from '../../components/Icon.vue';
import MapView from '../../components/MapView.vue';
import Modal from '../../components/Modal.vue';

// Props come from ProfilePageView.get_page_props() in Django.
const props = defineProps({
  user: { type: Object, required: true },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  mapPeople: { type: Array, default: () => [] },
  events: { type: Array, default: () => [] },
  meApi: { type: String, required: true },
  usernameCheckApi: { type: String, required: true },
  mapTileUrl: { type: String, required: true },
  chatsApi: { type: String, default: '' },
  chatSocketPath: { type: String, default: '' },
  chatMaxFileMb: { type: Number, default: 25 },
  mapSearchApi: { type: String, required: true },
  mapReverseApi: { type: String, required: true },
  // [{ value, label }]: the community categories; interests are picked from these.
  communityCategories: { type: Array, default: () => [] },
  // [{ value, label, url }]: the avatars a profile picture is picked from.
  avatars: { type: Array, default: () => [] },
});

const GRADIENTS = [
  ['#22b8c9', '#1f6fe5'],
  ['#f59f00', '#e8590c'],
  ['#be4bdb', '#7048e8'],
  ['#2fb36d', '#0c8599'],
  ['#e0475b', '#c2255c'],
];

// The signed-in user; replaced whenever the profile is saved.
const me = ref(props.user);

function goHome() {
  window.circleNavigate(props.homeUrl);
}

// ---------- derived ----------
// Accounts made before `name` existed (or via Google) may only have first/last name.
const fullName = computed(
  () => me.value.name || [me.value.first_name, me.value.last_name].filter(Boolean).join(' ')
);
const displayName = computed(() => fullName.value || me.value.username);
const initial = computed(() => displayName.value.charAt(0).toUpperCase());
const interests = computed(() => me.value.interested_category || []);
const communities = computed(() => me.value.join_community || []);
const hasPoint = computed(() => me.value.latitude != null && me.value.longitude != null);
const shortLocation = computed(() => me.value.location.split(',').slice(0, 2).join(','));
function gradientFor(name) {
  const sum = [...name].reduce((n, ch) => n + ch.charCodeAt(0), 0);
  const [a, b] = GRADIENTS[sum % GRADIENTS.length];
  return { background: `linear-gradient(135deg, ${a}, ${b})` };
}

// ---------- saving ----------
const saving = ref(false);
const toast = ref(null);
let toastTimer = null;

function notify(text, kind = 'success') {
  toast.value = { text, kind };
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.value = null), 3000);
}

// PATCH the profile; returns true on success. Errors go to the toast unless
// `onError` handles them.
async function save(data, { success, onError } = {}) {
  try {
    me.value = await apiPatch(props.meApi, data);
    if (success) notify(success);
    return true;
  } catch (err) {
    const parsed = parseErrors(err);
    if (onError) onError(parsed);
    else notify(parsed.message || Object.values(parsed.fieldErrors)[0], 'error');
    return false;
  }
}

// ---------- avatar ----------
const avatarOpen = ref(false);
const savingAvatar = ref(false);

// Saved straight away; '' goes back to the initial.
async function pickAvatar(key) {
  if (savingAvatar.value || key === me.value.avatar) return;
  savingAvatar.value = true;
  await save({ avatar: key }, { success: key ? 'Avatar updated' : 'Avatar removed' });
  savingAvatar.value = false;
}

// ---------- edit basic info ----------
const editOpen = ref(false);
const form = reactive({ name: '', username: '' });
const formErrors = ref({});
const formMessage = ref('');
const usernameStatus = ref(null); // { kind: 'ok' | 'checking', text }
const usernameError = ref('');
let usernameTimer = null;

function openEdit() {
  form.name = fullName.value;
  form.username = me.value.username;
  formErrors.value = {};
  formMessage.value = '';
  usernameStatus.value = null;
  usernameError.value = '';
  editOpen.value = true;
}

watch(() => form.username, (value) => {
  clearTimeout(usernameTimer);
  formErrors.value = { ...formErrors.value, username: '' };
  usernameError.value = '';
  usernameStatus.value = null;
  const username = value.trim();
  if (!editOpen.value || username.toLowerCase() === me.value.username.toLowerCase()) return;
  if (!username) {
    usernameError.value = 'Username is required.';
    return;
  }
  usernameStatus.value = { kind: 'checking', text: 'Checking availability…' };
  usernameTimer = setTimeout(async () => {
    try {
      const res = await apiGet(props.usernameCheckApi, { username });
      if (form.username.trim() !== username) return; // typed again since
      usernameStatus.value = res.available ? { kind: 'ok', text: 'Username is available.' } : null;
      usernameError.value = res.available ? '' : res.message;
    } catch {
      usernameStatus.value = null; // the save will validate it anyway
    }
  }, 400);
});

const canSaveEdit = computed(() => {
  const changed = form.name.trim() !== (me.value.name || '') || form.username.trim() !== me.value.username;
  return changed && !usernameError.value && usernameStatus.value?.kind !== 'checking';
});

async function saveEdit() {
  if (!canSaveEdit.value) return;
  saving.value = true;
  formMessage.value = '';
  const ok = await save(
    { name: form.name.trim(), username: form.username.trim() },
    {
      success: 'Profile updated',
      onError: ({ fieldErrors, message }) => {
        formErrors.value = fieldErrors;
        formMessage.value = message;
      },
    },
  );
  saving.value = false;
  if (ok) editOpen.value = false;
}

// ---------- jump to a card ----------
const interestsCard = ref(null);
const communitiesCard = ref(null);
const flashing = ref(null);
let flashTimer = null;

function scrollToCard(card) {
  if (!card) return;
  card.scrollIntoView({ behavior: 'smooth', block: 'start' });
  flashing.value = card;
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => (flashing.value = null), 1400);
}

// ---------- interests (community category keys, e.g. "sports") ----------
const interestsOpen = ref(false);
const picked = ref([]); // keys chosen in the popup, saved together
const interestError = ref('');

const labelOf = (key) => (props.communityCategories.find((c) => c.value === key) || {}).label || key;
const interestsChanged = computed(
  () => picked.value.length !== interests.value.length || picked.value.some((key) => !interests.value.includes(key))
);

function openInterests() {
  picked.value = [...interests.value];
  interestError.value = '';
  interestsOpen.value = true;
}

function togglePicked(key) {
  picked.value = picked.value.includes(key) ? picked.value.filter((k) => k !== key) : [...picked.value, key];
}

async function saveInterests() {
  saving.value = true;
  const ok = await save(
    { interested_category: picked.value },
    {
      success: 'Interests saved',
      onError: ({ fieldErrors, message }) => {
        interestError.value = fieldErrors.interested_category || message;
      },
    },
  );
  saving.value = false;
  if (ok) interestsOpen.value = false;
}

async function removeInterest(key) {
  await save({ interested_category: interests.value.filter((k) => k !== key) });
}

// ---------- communities ----------
const confirmLeave = ref(null);

async function leaveCommunity(community) {
  confirmLeave.value = null;
  const ids = communities.value.filter((c) => c.id !== community.id).map((c) => c.id);
  await save({ join_community: ids }, { success: `You left ${community.name}` });
}

// ---------- location ----------
const locationOpen = ref(false);
const draft = reactive({ label: '', lat: null, lng: null });
const locationError = ref('');
const draftLookingUp = ref(false);
const placeQuery = ref('');
const placeResults = ref([]);
const placeSearching = ref(false);
const placeSearched = ref(false);
let searchTimer = null;
let lookupId = 0;

function openLocation() {
  draft.label = me.value.location || '';
  draft.lat = me.value.latitude;
  draft.lng = me.value.longitude;
  locationError.value = '';
  placeQuery.value = '';
  placeResults.value = [];
  placeSearched.value = false;
  locationOpen.value = true;
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
  const q = placeQuery.value.trim();
  placeSearched.value = false;
  if (!q) {
    placeResults.value = [];
    return;
  }
  placeSearching.value = true;
  searchTimer = setTimeout(async () => {
    const params = { q };
    if (draft.lat != null) Object.assign(params, { lat: draft.lat, lon: draft.lng });
    try {
      const res = await apiGet(props.mapSearchApi, params);
      if (placeQuery.value.trim() !== q) return;
      placeResults.value = (res.features || []).map(toPlace);
    } catch (err) {
      placeResults.value = [];
      locationError.value = parseErrors(err).message;
    } finally {
      placeSearching.value = false;
      placeSearched.value = true;
    }
  }, 350);
}

function choosePlace(place) {
  Object.assign(draft, place);
  placeResults.value = [];
  placeQuery.value = '';
  placeSearched.value = false;
}

async function pickPoint({ lat, lng }) {
  draft.lat = lat;
  draft.lng = lng;
  locationError.value = '';
  const id = ++lookupId;
  draftLookingUp.value = true;
  try {
    const res = await apiGet(props.mapReverseApi, { lat, lon: lng });
    const feature = (res.features || [])[0];
    if (id === lookupId && feature) draft.label = toPlace(feature).label;
  } catch {
    // Keep whatever name is typed; the pin is still saved.
  } finally {
    if (id === lookupId) draftLookingUp.value = false;
  }
}

async function saveLocation() {
  saving.value = true;
  locationError.value = '';
  const ok = await save(
    {
      location: draft.label.trim(),
      latitude: draft.lat == null ? null : Number(draft.lat.toFixed(6)),
      longitude: draft.lng == null ? null : Number(draft.lng.toFixed(6)),
    },
    {
      success: 'Location saved',
      onError: ({ fieldErrors, message }) => {
        locationError.value = message || Object.values(fieldErrors)[0];
      },
    },
  );
  saving.value = false;
  if (ok) locationOpen.value = false;
}

async function clearLocation() {
  saving.value = true;
  const ok = await save({ location: '', latitude: null, longitude: null }, { success: 'Location removed' });
  saving.value = false;
  if (ok) locationOpen.value = false;
}
</script>

<style scoped>
button {
  font: inherit;
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.sheet {
  padding: 24px;
  background: var(--surface);
  border-radius: 22px;
  box-shadow: 0 10px 30px rgba(8, 19, 31, 0.14);
}

.profile__title {
  margin: 0 0 16px;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--night-text);
}

.muted {
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}

.spacer {
  flex: 1;
}

/* ---------- hero ---------- */
.hero {
  overflow: hidden;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
}

.hero__cover {
  height: 96px;
  background:
    radial-gradient(400px 120px at 85% 0%, rgba(34, 184, 201, 0.55), transparent 70%),
    linear-gradient(120deg, #1f6fe5 0%, #13284a 100%);
}

.hero__row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 16px;
  padding: 0 24px;
  margin-top: -44px;
}

.photo {
  position: relative;
  flex: none;
  width: 104px;
  height: 104px;
}

.photo__img,
.photo__initial {
  width: 100%;
  height: 100%;
  border: 4px solid var(--surface);
  border-radius: 50%;
  box-shadow: 0 6px 16px rgba(8, 19, 31, 0.18);
}

.photo__img {
  object-fit: cover;
  background: var(--surface-muted);
}

.photo__initial {
  display: grid;
  place-items: center;
  font-size: 40px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--teal), var(--primary));
}

.photo__btn {
  position: absolute;
  right: 2px;
  bottom: 2px;
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  color: #fff;
  background: var(--night-700);
  border: 3px solid var(--surface);
  border-radius: 50%;
}

.photo__btn:hover:not(:disabled) {
  background: var(--primary);
}

.photo__busy {
  position: absolute;
  inset: 4px;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: rgba(8, 19, 31, 0.55);
  border-radius: 50%;
}

.hero__info {
  flex: 1 1 200px;
  min-width: 0;
  padding-bottom: 4px;
}

.hero__name {
  margin: 0;
  overflow: hidden;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hero__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  margin: 4px 0 0;
  font-size: 14px;
  color: var(--muted);
}

.hero__meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.hero__edit {
  margin-bottom: 4px;
}

.hero__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 20px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border);
}

.stat {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  text-align: center;
  color: var(--text);
  background: var(--surface-muted);
  border: 1px solid transparent;
  border-radius: 12px;
  transition: background 0.15s, border-color 0.15s;
}

.stat:hover {
  background: var(--primary-soft);
  border-color: #c9dafa;
}

.stat__text {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat strong {
  font-size: 20px;
  line-height: 1.2;
}

.stat__text span {
  font-size: 13px;
  color: var(--muted);
}

/* ---------- cards ---------- */
.cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  margin-top: 20px;
}

/* Wide screens: basic info, location and interests side by side. */
@media (min-width: 1600px) {
  .cards {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1599px) {
  .card--interests {
    grid-column: 1 / -1;
  }
}

.card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 18px 20px 20px;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 16px;
  scroll-margin-top: 16px;
}

/* Briefly outlined after jumping to it from the stats. */
.card--flash {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
  transition: border-color 0.3s, box-shadow 0.3s;
}

.card--wide {
  grid-column: 1 / -1;
}

.card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.card__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.card__title .card__count {
  margin-left: 6px;
  vertical-align: 2px;
}

.card__count {
  padding: 1px 9px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  background: var(--surface-muted);
  border-radius: 99px;
}

.card__map {
  height: 180px;
}

.card__caption {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 10px 0 0;
  font-size: 14px;
  color: var(--muted);
}

.blank {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px 16px;
  text-align: center;
  color: var(--muted);
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: 12px;
}

.blank p {
  max-width: 320px;
  margin: 0;
  font-size: 14px;
}

/* ---------- basic info ---------- */
.info {
  margin: 0;
}

.info__row {
  display: grid;
  grid-template-columns: 116px minmax(0, 1fr);
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}

.info__row:last-child {
  border-bottom: 0;
}

.info dt {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--muted);
}

.info dd {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  overflow-wrap: break-word;
  min-width: 0;
  font-weight: 500;
}

.info__empty {
  font-weight: 400;
  font-style: italic;
  color: var(--muted);
}

.locked {
  display: inline-grid;
  color: var(--muted);
}

/* ---------- interests ---------- */
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 0;
  /* Room for the remove button that sits on each tag's corner. */
  padding: 8px 8px 0 0;
  list-style: none;
}

/* Same shape as the buttons (ActionButton.vue). */
.tag {
  position: relative;
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 14px;
  font-size: 14px;
  font-weight: 500;
  color: var(--primary);
  background: var(--primary-soft);
  border: 1px solid #c9dafa;
  border-radius: 10px;
  transition: border-color 0.15s;
}

.tag:hover,
.tag:focus-within {
  border-color: var(--primary);
}

/* Remove button: on the tag's top-right corner, shown on hover/focus. */
.tag__x {
  position: absolute;
  top: -9px;
  right: -9px;
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  padding: 0;
  color: var(--muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(8, 19, 31, 0.15);
  opacity: 0;
  transform: scale(0.7);
  transition: opacity 0.15s, transform 0.15s, background 0.15s, color 0.15s;
}

.tag:hover .tag__x,
.tag:focus-within .tag__x {
  opacity: 1;
  transform: scale(1);
}

.tag__x:hover,
.tag__x:focus-visible {
  color: #fff;
  background: var(--primary);
  border-color: var(--primary);
  outline: none;
}

/* Touch screens can't hover, so keep it visible there. */
@media (hover: none) {
  .tag__x {
    opacity: 1;
    transform: none;
  }
}

.add {
  display: flex;
  gap: 8px;
}

.add input,
.loc-label input {
  flex: 1;
  min-width: 0;
  height: 40px;
  padding: 0 14px;
  font: inherit;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  outline: none;
}

.add input:focus,
.loc-label input:focus {
  background: var(--surface);
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.suggest {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
}

.suggest__label {
  font-size: 13px;
  color: var(--muted);
}

.suggest__chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 10px;
  font-size: 13px;
  color: var(--muted);
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: 99px;
}

.suggest__chip:hover:not(:disabled) {
  color: var(--primary);
  border-color: var(--primary);
}

/* ---------- communities ---------- */
.groups {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.group {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 14px;
}

.group__img {
  flex: none;
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 12px;
}

.group__img--initial {
  display: grid;
  place-items: center;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.group__info {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.group__name {
  overflow: hidden;
  font-weight: 600;
  color: var(--text);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group__info span {
  font-size: 13px;
  color: var(--muted);
}

.group__actions {
  display: flex;
  gap: 6px;
}

.suggest__chip--on,
.suggest__chip--on:hover:not(:disabled) {
  color: var(--green-dark);
  background: var(--green-soft);
  border-style: solid;
  border-color: #bfe8d0;
}

/* ---------- add interests popup ---------- */
.pick {
  margin-top: 16px;
}

.pick__label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
}

.pick .suggest {
  margin-top: 0;
}

.pick-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.tag--new {
  color: var(--green-dark);
  background: var(--green-soft);
  border-color: #bfe8d0;
}

.tag--new:hover,
.tag--new:focus-within {
  border-color: var(--green-dark);
}

.tag--new .tag__x:hover,
.tag--new .tag__x:focus-visible {
  background: var(--green-dark);
  border-color: var(--green-dark);
}

/* ---------- edit modal ---------- */
.edit-photo {
  margin-bottom: 18px;
}

.edit-photo__head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.edit-photo__label {
  margin-right: auto;
  font-size: 14px;
  font-weight: 600;
}

.edit-photo__img {
  flex: none;
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 50%;
}

.edit-photo__img--initial {
  display: grid;
  place-items: center;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--teal), var(--primary));
}

.hint {
  margin: -10px 0 16px;
  font-size: 13px;
}

.hint--ok {
  color: var(--green-dark);
}

.hint--checking {
  color: var(--muted);
}

.readonly {
  margin-bottom: 8px;
}

.readonly__label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 600;
}

.readonly__value {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 44px;
  padding: 0 14px;
  overflow: hidden;
  color: var(--muted);
  white-space: nowrap;
  background: var(--surface-muted);
  border: 1px dashed var(--border);
  border-radius: 10px;
}

.readonly__hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.form-error {
  margin: 12px 0 0;
  padding: 10px 12px;
  font-size: 14px;
  color: var(--danger);
  background: var(--danger-bg);
  border-radius: 10px;
}

/* ---------- location modal ---------- */
.loc-search {
  position: relative;
  margin-bottom: 12px;
}

.loc-search__box {
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

.loc-search__box:focus-within {
  background: var(--surface);
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.loc-search__box input {
  flex: 1;
  min-width: 0;
  height: 100%;
  font: inherit;
  color: var(--text);
  background: none;
  border: 0;
  outline: none;
}

.loc-results {
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

.loc-results button {
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

.loc-results button:hover {
  background: var(--surface-muted);
}

.loc-status {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.loc-map {
  height: 300px;
}

.loc-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 8px 0 14px;
  font-size: 13px;
  color: var(--muted);
}

.loc-label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
}

.loc-label input {
  flex: none;
  height: 44px;
  font-weight: 400;
}

/* ---------- toast ---------- */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  z-index: 1100;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  background: var(--night-800);
  border-radius: 12px;
  box-shadow: var(--shadow);
  transform: translateX(-50%);
}

.toast--success :deep(.icon) {
  color: var(--green);
}

.toast--error {
  background: var(--danger);
}

/* ---------- responsive ---------- */
@media (max-width: 900px) {
  .cards {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 560px) {
  .sheet {
    padding: 12px;
    border-radius: 18px;
  }
  .hero__row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    padding: 0 16px;
  }
  .hero__info {
    flex: none;
    width: 100%;
  }
  .hero__stats {
    grid-template-columns: 1fr 1fr;
    padding: 14px 16px 16px;
  }
  .card {
    padding: 16px;
  }
  .info__row {
    grid-template-columns: minmax(0, 1fr);
    gap: 2px;
  }
  .loc-map {
    height: 240px;
  }
}
</style>
