<!--
  Chats tab: a box for each community the user joined, latest message
  first, with the number of unread messages. Updates live (see chat.mjs).
  Usage: <ChatList @open="openChat" @navigate="go" />
-->
<template>
  <div class="chatlist">
    <label v-if="chat.chats.length > 4" class="search">
      <Icon name="search" :size="16" />
      <input v-model="query" type="search" placeholder="Search chats" aria-label="Search chats" />
    </label>

    <p v-if="!chat.loaded" class="note">Loading chats…</p>
    <p v-else-if="chat.loadError && !chat.chats.length" class="note note--error">{{ chat.loadError }}</p>

    <EmptyState v-else-if="!chat.chats.length" icon="chat" text="Join a community to chat with its members.">
      <ActionButton icon="compass" label="Discover communities" @click="$emit('navigate', 'discover')" />
    </EmptyState>

    <ul v-else class="boxes">
      <li v-for="c in shown" :key="c.id">
        <a
          :href="`?tab=chats&community=${c.id}`"
          class="box"
          :class="{ 'box--unread': c.unread_count }"
          @click.prevent="$emit('open', c.id)"
        >
          <img :src="c.image" alt="" class="box__pic" />
          <span class="box__body">
            <span class="box__top">
              <strong class="box__name">{{ c.name }}</strong>
              <time v-if="c.last_message" class="box__time" :datetime="c.last_message.created_at">
                {{ shortTime(c.last_message.created_at) }}
              </time>
            </span>
            <span class="box__bottom">
              <span class="box__preview">
                <template v-if="c.last_message">
                  <b>{{ authorLabel(c.last_message.author) }}:</b> {{ messagePreview(c.last_message) }}
                </template>
                <template v-else>{{ c.members_count }} {{ c.members_count === 1 ? 'member' : 'members' }} · Say hello 👋</template>
              </span>
              <span v-if="c.unread_count" class="box__badge" :aria-label="`${c.unread_count} unread messages`">
                {{ c.unread_count > 99 ? '99+' : c.unread_count }}
              </span>
            </span>
          </span>
        </a>
      </li>
      <li v-if="!shown.length" class="note">No chats match “{{ query }}”.</li>
    </ul>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { chat, messagePreview } from '../chat.mjs';
import { clockTime, timeAgo } from '../time.mjs';
import ActionButton from './ActionButton.vue';
import EmptyState from './EmptyState.vue';
import Icon from './Icon.vue';

const props = defineProps({
  user: { type: Object, required: true },
});
defineEmits(['open', 'navigate']);

const query = ref('');
const shown = computed(() => {
  const q = query.value.trim().toLowerCase();
  return q ? chat.chats.filter((c) => c.name.toLowerCase().includes(q)) : chat.chats;
});

function authorLabel(author) {
  if (!author) return 'Deleted user';
  if (author.id === props.user.id) return 'You';
  return author.name || author.username;
}

// Today: "14:05"; older: "2d", "12 Oct".
function shortTime(iso) {
  return new Date(iso).toDateString() === new Date().toDateString() ? clockTime(iso) : timeAgo(iso);
}
</script>

<style scoped>
.chatlist {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  color: var(--muted);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.search:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--focus);
}

.search input {
  flex: 1;
  min-width: 0;
  padding: 10px 0;
  font: inherit;
  color: var(--text);
  background: none;
  border: 0;
  outline: none;
}

.note {
  margin: 0;
  padding: 16px;
  text-align: center;
  color: var(--muted);
  list-style: none;
}

.note--error {
  color: var(--danger);
}

.boxes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  font-weight: 400;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}

.box:hover {
  text-decoration: none;
  border-color: #c9dafa;
  box-shadow: 0 0 0 4px var(--focus);
}

.box--unread {
  background: var(--primary-soft);
  border-color: #c9dafa;
}

.box__pic {
  flex: none;
  width: 52px;
  height: 52px;
  object-fit: cover;
  border-radius: 50%;
  background: var(--surface-muted);
}

.box__body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.box__top,
.box__bottom {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.box__name {
  flex: 1;
  overflow: hidden;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.box__time {
  flex: none;
  font-size: 12px;
  color: var(--muted);
}

.box--unread .box__time {
  font-weight: 600;
  color: var(--primary);
}

.box__preview {
  flex: 1;
  overflow: hidden;
  font-size: 14px;
  color: var(--muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.box__preview b {
  font-weight: 600;
}

.box--unread .box__preview {
  color: var(--text);
}

.box__badge {
  flex: none;
  min-width: 22px;
  padding: 2px 7px;
  font-size: 12px;
  font-weight: 700;
  line-height: 18px;
  text-align: center;
  color: #fff;
  background: var(--primary);
  border-radius: 999px;
}
</style>
