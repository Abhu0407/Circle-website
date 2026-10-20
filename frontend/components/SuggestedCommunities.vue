<!--
  A row of community cards that scrolls sideways (with ‹ › buttons on wide
  screens), shown between posts on For You. Each card says why it was
  suggested and has a Join button.
  Emits `joined` with the community, so the page can update My Communities.
  Usage: <SuggestedCommunities :communities="slice" :communities-api="communitiesApi" @joined="..." />
-->
<template>
  <section class="suggest" aria-label="Communities you might like">
    <div class="suggest__head">
      <h2 class="suggest__title"><Icon name="sparkle" :size="16" /> Communities you might like</h2>
      <div class="suggest__arrows">
        <button type="button" class="arrow arrow--prev" aria-label="Scroll left" @click="scroll(-1)">
          <Icon name="chevron" :size="16" />
        </button>
        <button type="button" class="arrow arrow--next" aria-label="Scroll right" @click="scroll(1)">
          <Icon name="chevron" :size="16" />
        </button>
      </div>
    </div>

    <ul ref="track" class="track">
      <li v-for="c in communities" :key="c.id" class="card">
        <a :href="c.url" class="card__cover" :style="c.image ? { backgroundImage: `url(${c.image})` } : null" tabindex="-1" aria-hidden="true">
          <span class="card__badge">{{ c.category_label }}</span>
        </a>
        <div class="card__body">
          <h3 class="card__name"><a :href="c.url">{{ c.name }}</a></h3>
          <p class="card__reason">{{ c.reason }}</p>
          <p class="card__meta">
            <Icon name="users" :size="13" /> {{ c.members_count }} {{ c.members_count === 1 ? 'member' : 'members' }}
            <template v-if="c.distance_km != null"> · {{ formatKm(c.distance_km) }}</template>
          </p>
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
          <p v-if="errors[c.id]" class="card__error">{{ errors[c.id] }}</p>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { ref } from 'vue';
import { apiPost, parseErrors } from '../api.mjs';
import ActionButton from './ActionButton.vue';
import Icon from './Icon.vue';

const props = defineProps({
  // [{ id, name, category_label, image, url, members_count, distance_km, reason, is_member }]
  communities: { type: Array, required: true },
  communitiesApi: { type: String, required: true },
});
const emit = defineEmits(['joined']);

const track = ref(null);
const joining = ref(null);
const errors = ref({});

// Move by most of the visible width.
function scroll(direction) {
  const el = track.value;
  if (el) el.scrollBy({ left: direction * el.clientWidth * 0.8, behavior: 'smooth' });
}

async function join(community) {
  joining.value = community.id;
  errors.value = { ...errors.value, [community.id]: '' };
  try {
    const res = await apiPost(`${props.communitiesApi}${community.id}/join/`);
    community.is_member = res.is_member;
    community.members_count = res.members_count;
    emit('joined', { ...community });
  } catch (err) {
    errors.value = { ...errors.value, [community.id]: parseErrors(err).message || 'Could not join.' };
  } finally {
    joining.value = null;
  }
}

function open(community) {
  window.circleNavigate(community.url);
}

const formatKm = (km) => (km < 1 ? `${Math.round(km * 1000)} m` : `${km < 10 ? km.toFixed(1) : Math.round(km)} km`);
</script>

<style scoped>
.suggest {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  padding: 16px 0 16px 16px;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 16px;
}

.suggest__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-right: 16px;
}

.suggest__title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.suggest__title :deep(svg) {
  color: var(--teal);
}

.suggest__arrows {
  display: flex;
  gap: 6px;
}

.arrow {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  font: inherit;
  color: var(--muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 50%;
  cursor: pointer;
}

.arrow:hover {
  color: var(--primary);
  border-color: var(--primary);
}

.arrow--prev :deep(svg) {
  transform: rotate(90deg);
}

.arrow--next :deep(svg) {
  transform: rotate(-90deg);
}

/* Sideways scrolling row; cards snap into place. */
.track {
  display: flex;
  gap: 12px;
  margin: 0;
  padding: 2px 16px 6px 0;
  overflow-x: auto;
  list-style: none;
  scroll-snap-type: x mandatory;
  scrollbar-width: thin;
}

.card {
  display: flex;
  flex: 0 0 200px;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  scroll-snap-align: start;
}

.card__cover {
  position: relative;
  height: 80px;
  background: linear-gradient(120deg, #1f6fe5 0%, #13284a 100%);
  background-position: center;
  background-size: cover;
}

.card__badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 9px;
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
  align-items: flex-start;
  gap: 6px;
  padding: 12px;
}

.card__name {
  margin: 0;
  overflow: hidden;
  max-width: 100%;
  font-size: 15px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card__name a {
  color: var(--text);
}

.card__reason {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--primary);
}

.card__meta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--muted);
}

.card__error {
  margin: 0;
  font-size: 12px;
  color: var(--danger);
}

@media (max-width: 560px) {
  .suggest__arrows {
    display: none;
  }
  .card {
    flex-basis: 170px;
  }
}
</style>
