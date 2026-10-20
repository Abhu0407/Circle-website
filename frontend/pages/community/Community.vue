<!-- A community: its information, Join/Leave, members, and its posts (members can post). -->
<template>
  <BaseLayout
    :user="user"
    active="communities"
    :home-url="homeUrl"
    :profile-url="profileUrl"
    :signout-api="signoutApi"
    :signin-url="signinUrl"
    :map-tile-url="mapTileUrl"
    :map-people="mapPeople"
  >
    <PageSheet title="Community" :back-url="communitiesUrl" back-label="My Communities">
      <!-- ---------- Header ---------- -->
      <PageHero :name="c.name" :cover="c.image" :picture="c.image" :initial="c.name.charAt(0).toUpperCase()">
        <template #meta>
          <span><Icon name="compass" :size="14" /> {{ c.category_label }}</span>
          <span v-if="c.location"><Icon name="pin" :size="14" /> {{ c.location }}</span>
          <span v-if="c.is_creator" class="badge badge--owner">You created this</span>
          <span v-else-if="c.is_member" class="badge badge--member">Member</span>
        </template>

        <template #actions>
          <!-- Joined is only a status box; leaving is done with the button beside the description. -->
          <span v-if="c.is_member" class="joined">Joined</span>
          <ActionButton v-else icon="userPlus" :label="busy ? 'Joining…' : 'Join community'" size="sm" :disabled="busy" @click="setMember(true)" />
        </template>

        <template #about>
          <div class="about">
            <p v-if="c.description" class="description">{{ c.description }}</p>
            <p v-else class="description description--empty">
              No description yet.
              <button v-if="c.is_creator" type="button" class="description__add" @click="editing = true">Add one</button>
            </p>

            <div v-if="c.is_member" class="about__leave">
              <template v-if="confirmLeave">
                <ActionButton icon="logout" :label="busy ? 'Leaving…' : 'Yes, leave'" size="sm" :disabled="busy" @click="setMember(false)" />
                <ActionButton icon="close" label="Cancel" size="sm" variant="secondary" @click="confirmLeave = false" />
              </template>
              <ActionButton v-else icon="logout" label="Leave" size="sm" variant="secondary" @click="confirmLeave = true" />
            </div>
          </div>
        </template>

        <template #stats>
          <HeroStat :value="c.members_count" :label="c.members_count === 1 ? 'Member' : 'Members'" @click="scrollTo(membersCard)" />
          <HeroStat :value="c.posts_count" :label="c.posts_count === 1 ? 'Post' : 'Posts'" @click="scrollTo(postsCard)" />
        </template>
      </PageHero>
      <p v-if="error" class="error" role="alert">{{ error }}</p>

      <CardGrid>
        <!-- ---------- Details ---------- -->
        <SectionCard title="Details">
          <template v-if="c.is_creator" #action>
            <ActionButton icon="edit" label="Edit" size="sm" compact @click="editing = true" />
          </template>
          <dl class="info">
            <div class="info__row">
              <dt><Icon name="compass" :size="16" /> Category</dt>
              <dd>
                {{ c.category_label }}
                <span class="locked" title="The category can't be changed"><Icon name="lock" :size="12" /></span>
              </dd>
            </div>
            <div class="info__row">
              <dt><Icon name="pin" :size="16" /> Location</dt>
              <dd :class="{ 'info__empty': !c.location }">{{ c.location || 'Not set' }}</dd>
            </div>
            <div class="info__row">
              <dt><Icon name="user" :size="16" /> Created by</dt>
              <dd :class="{ 'info__empty': !c.created_by }">{{ c.created_by ? `@${c.created_by.username}` : 'Unknown' }}</dd>
            </div>
            <div class="info__row">
              <dt><Icon name="clock" :size="16" /> Since</dt>
              <dd>{{ since }}</dd>
            </div>
          </dl>
        </SectionCard>

        <!-- ---------- Members ---------- -->
        <div ref="membersCard" class="anchor">
          <SectionCard title="Members" :count="c.members_count" class="fill">
            <ul v-if="c.members.length" class="members">
              <li v-for="m in c.members" :key="m.id" class="member" :title="m.name || m.username">
                <UserAvatar :user="m" :size="44" />
                <span>{{ m.id === user.id ? 'You' : `@${m.username}` }}</span>
              </li>
              <li v-if="c.members_count > c.members.length" class="member">
                <span class="member__more">+{{ c.members_count - c.members.length }}</span>
                <span>more</span>
              </li>
            </ul>
            <EmptyState v-else icon="users" text="No members yet. Be the first to join.">
              <ActionButton icon="userPlus" label="Join community" :disabled="busy" @click="setMember(true)" />
            </EmptyState>
          </SectionCard>
        </div>

        <!-- ---------- Members map ---------- -->
        <SectionCard title="Members map" :count="mapCount" wide>
          <template v-if="hasMap" #action>
            <ActionButton icon="expand" label="Open large map" size="sm" compact @click="mapOpen = true" />
          </template>
          <template v-if="hasMap">
            <PeopleMap :tile-url="mapTileUrl" :people="memberPoints" :me="mePin" :place="placePin" />
            <p class="map-note">
              <span v-if="placePin"><span class="key key--place">⌂</span> Where {{ c.name }} meets</span>
              <span><span class="key">A</span> Members who shared a location (about 1 km)</span>
            </p>
          </template>
          <EmptyState v-else icon="pin" text="No members have shared their location yet. Members set it on their Profile." />
        </SectionCard>

        <!-- ---------- Posts ---------- -->
        <div ref="postsCard" class="anchor anchor--wide">
          <SectionCard title="Posts" :count="c.posts_count">
            <div v-if="!c.is_member" class="note">
              <Icon name="lock" :size="16" />
              <span>Only members can post here. Join {{ c.name }} to share something.</span>
            </div>
            <PostFeed
              :posts-api="postsApi"
              :user="user"
              :community="c"
              :can-post="c.is_member"
              @created="c.posts_count++"
              @deleted="c.posts_count--"
            />
          </SectionCard>
        </div>
      </CardGrid>
    </PageSheet>

    <CommunityEditModal
      v-if="editing"
      :community="c"
      :api="communityApi"
      :covers="communityCovers[c.category] || []"
      :map-tile-url="mapTileUrl"
      :map-search-api="mapSearchApi"
      :map-reverse-api="mapReverseApi"
      @saved="onSaved"
      @close="editing = false"
    />

    <Modal v-if="mapOpen" :title="`${c.name} · members map`" large @close="mapOpen = false">
      <PeopleMap :tile-url="mapTileUrl" :people="memberPoints" :me="mePin" :place="placePin" large />
    </Modal>
  </BaseLayout>
</template>

<script setup>
import { computed, ref } from 'vue';
import { apiDelete, apiGet, apiPost } from '../../api.mjs';
import ActionButton from '../../components/ActionButton.vue';
import BaseLayout from '../../components/BaseLayout.vue';
import CardGrid from '../../components/CardGrid.vue';
import CommunityEditModal from '../../components/CommunityEditModal.vue';
import EmptyState from '../../components/EmptyState.vue';
import HeroStat from '../../components/HeroStat.vue';
import Icon from '../../components/Icon.vue';
import PageHero from '../../components/PageHero.vue';
import Modal from '../../components/Modal.vue';
import PageSheet from '../../components/PageSheet.vue';
import PeopleMap from '../../components/PeopleMap.vue';
import PostFeed from '../../components/PostFeed.vue';
import SectionCard from '../../components/SectionCard.vue';
import UserAvatar from '../../components/UserAvatar.vue';

// Props come from CommunityPageView.get_page_props() in Django.
// community: see CommunityDetailSerializer in backend/apps/communities/serializers.py
const props = defineProps({
  user: { type: Object, required: true },
  community: { type: Object, required: true },
  communityApi: { type: String, required: true },
  joinApi: { type: String, required: true },
  postsApi: { type: String, required: true },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  mapTileUrl: { type: String, required: true },
  mapPeople: { type: Array, default: () => [] },
  mapSearchApi: { type: String, required: true },
  mapReverseApi: { type: String, required: true },
  // { category: [{ value, label, url }] }: pictures a community can pick.
  communityCovers: { type: Object, default: () => ({}) },
  // Other members' pins: [{ id, username, lat, lng }]
  memberPoints: { type: Array, default: () => [] },
});

const communitiesUrl = `${props.homeUrl}?tab=communities`;

const c = ref({ ...props.community });
const busy = ref(false);
const confirmLeave = ref(false);
const editing = ref(false);
const mapOpen = ref(false);

// You appear on the members map only while you are a member.
const mePin = computed(() => (c.value.is_member ? props.user : null));
const placePin = computed(() =>
  c.value.latitude != null ? { label: c.value.location || c.value.name, lat: c.value.latitude, lng: c.value.longitude } : null
);
const mapCount = computed(() => {
  const me = mePin.value && mePin.value.latitude != null ? 1 : 0;
  return props.memberPoints.length + me;
});
const hasMap = computed(() => mapCount.value > 0 || placePin.value);
const error = ref('');
const membersCard = ref(null);
const postsCard = ref(null);

const since = computed(() =>
  new Date(c.value.created_at).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
);

function scrollTo(el) {
  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function onSaved(community) {
  c.value = community;
  editing.value = false;
  document.title = `${community.name} · Circle`;
}

async function setMember(join) {
  busy.value = true;
  error.value = '';
  try {
    await (join ? apiPost : apiDelete)(props.joinApi);
    // Fresh copy, so the member list and counts include the change.
    c.value = await apiGet(props.communityApi);
    confirmLeave.value = false;
  } catch {
    error.value = join ? 'Could not join. Please try again.' : 'Could not leave. Please try again.';
  } finally {
    busy.value = false;
  }
}
</script>

<style scoped>
.error {
  margin: -8px 0 0;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--danger);
  background: var(--danger-bg);
  border-radius: 10px;
}

.badge {
  padding: 1px 10px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 99px;
}

.badge--member {
  color: var(--green-dark);
  background: var(--green-soft);
}

.badge--owner {
  color: var(--primary);
  background: var(--primary-soft);
}

/* Wrappers the stats scroll to. */
.anchor {
  display: flex;
  min-width: 0;
  scroll-margin-top: 16px;
}

.anchor > * {
  flex: 1;
}

.anchor--wide {
  grid-column: 1 / -1;
}

/* Status box in the header actions (not a button). */
.joined {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--green-dark);
  background: var(--green-soft);
  border-radius: 10px;
  cursor: default;
  user-select: none;
}

/* ---------- description (in the header) + Leave on its right ---------- */
.about {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.about__leave {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}

.description {
  flex: 1;
  min-width: 0;
  margin: 0;
  padding: 14px 16px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: var(--surface-muted);
  border-radius: 12px;
}

.description--empty {
  font-style: italic;
  color: var(--muted);
}

.description__add {
  padding: 0;
  font: inherit;
  font-style: normal;
  font-weight: 600;
  color: var(--primary);
  background: none;
  border: 0;
  cursor: pointer;
}

/* ---------- details ---------- */
.locked {
  display: inline-grid;
  margin-left: 4px;
  vertical-align: -1px;
  color: var(--muted);
}

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
  margin: 0;
  min-width: 0;
  font-weight: 500;
  overflow-wrap: break-word;
}

.info__empty {
  font-weight: 400;
  font-style: italic;
  color: var(--muted);
}

/* ---------- members ---------- */
.members {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(76px, 1fr));
  gap: 14px 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.member {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 0;
  font-size: 12px;
  color: var(--muted);
}

.member > span:last-child {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member__more {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 50%;
}

/* ---------- members map ---------- */
.map-note {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.map-note > span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.key {
  display: inline-grid;
  place-items: center;
  width: 18px;
  height: 18px;
  font-size: 10px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--teal), var(--primary));
  border-radius: 50% 50% 50% 0;
}

.key--place {
  background: linear-gradient(135deg, #13284a, var(--primary));
  border-radius: 5px 5px 5px 0;
}

/* ---------- posts ---------- */
.note {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--primary);
  background: var(--primary-soft);
  border: 1px solid #c9dafa;
  border-radius: 10px;
}

@media (max-width: 560px) {
  .about {
    flex-direction: column;
    align-items: stretch;
  }
  .info__row {
    grid-template-columns: minmax(0, 1fr);
    gap: 2px;
  }
}
</style>
