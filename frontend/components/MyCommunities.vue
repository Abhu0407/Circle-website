<!--
  Home's My Communities tab (inside the page's PageSheet): a card for each
  community the user joined (opens its page), then the latest posts from
  all of them.
  Usage: <MyCommunities :posts-api="postsApi" :user="user" @navigate="go" />
-->
<template>
  <CardGrid>
    <SectionCard title="Your communities" :count="communities.length" wide>
      <template v-if="communities.length" #action>
        <ActionButton icon="plus" label="Create community" size="sm" compact @click="$emit('navigate', 'create')" />
      </template>

      <div v-if="communities.length" class="grid">
        <a v-for="c in communities" :key="c.id" :href="c.url" class="ccard">
          <img v-if="c.image" :src="c.image" alt="" class="ccard__pic" />
          <span v-else class="ccard__pic ccard__pic--initial">{{ c.name.charAt(0).toUpperCase() }}</span>
          <span class="ccard__info">
            <strong>{{ c.name }}</strong>
            <span>
              <template v-if="c.category_label">{{ c.category_label }} · </template>
              {{ c.members_count }} {{ c.members_count === 1 ? 'member' : 'members' }}
            </span>
            <span v-if="c.location" class="ccard__place"><Icon name="pin" :size="12" /> {{ c.location }}</span>
          </span>
          <Icon name="chevron" :size="16" class="ccard__go" />
        </a>
      </div>

      <EmptyState v-else icon="users" text="You haven't joined any communities yet.">
        <ActionButton icon="plus" label="Create a community" @click="$emit('navigate', 'create')" />
        <ActionButton icon="compass" label="Discover" variant="secondary" @click="$emit('navigate', 'discover')" />
      </EmptyState>
    </SectionCard>

    <SectionCard v-if="communities.length" title="Latest posts" wide>
      <PostFeed :posts-api="postsApi" :user="user" />
    </SectionCard>
  </CardGrid>
</template>

<script setup>
import { computed } from 'vue';
import ActionButton from './ActionButton.vue';
import CardGrid from './CardGrid.vue';
import EmptyState from './EmptyState.vue';
import Icon from './Icon.vue';
import PostFeed from './PostFeed.vue';
import SectionCard from './SectionCard.vue';

const props = defineProps({
  postsApi: { type: String, required: true },
  user: { type: Object, required: true },
});
defineEmits(['navigate']);

const communities = computed(() => props.user.join_community || []);
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}

/* Same row look as the communities list on Profile. */
.ccard {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  padding: 12px;
  font-weight: 400;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.ccard:hover {
  text-decoration: none;
  border-color: #c9dafa;
  box-shadow: 0 0 0 4px var(--focus);
}

.ccard__pic {
  flex: none;
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 50%;
}

.ccard__pic--initial {
  display: grid;
  place-items: center;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--teal), var(--primary));
}

.ccard__info {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.ccard__info strong,
.ccard__info span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ccard__info strong {
  font-weight: 600;
}

.ccard__info span {
  font-size: 13px;
  color: var(--muted);
}

.ccard__place {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.ccard__go {
  color: var(--muted);
  transform: rotate(-90deg);
}
</style>
