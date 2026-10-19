<!--
  One comment and, under it, its replies — each reply is another
  CommentNode, so threads nest to any depth. Indentation stops growing
  after MAX_INDENT levels so deep threads still fit on a phone.
  Actions (reply, edit, delete) go through the functions CommentSection
  provides as 'comments'.
-->
<template>
  <li class="cnode">
    <div class="cnode__row">
      <UserAvatar :user="comment.is_deleted ? null : comment.author" :size="depth ? 26 : 32" />
      <div class="cnode__main">
        <CommentForm
          v-if="editing"
          :initial="comment.body"
          :send="saveEdit"
          submit-label="Save"
          autofocus
          cancelable
          @cancel="editing = false"
        />
        <div v-else class="cnode__bubble" :class="{ 'cnode__bubble--deleted': comment.is_deleted }">
          <em v-if="comment.is_deleted">This comment was deleted.</em>
          <template v-else>
            <span class="cnode__author">{{ authorName }}</span>
            <p class="cnode__body">{{ comment.body }}</p>
          </template>
        </div>

        <div v-if="!editing" class="cnode__meta">
          <time :datetime="comment.created_at" :title="fullDate(comment.created_at)">{{ timeAgo(comment.created_at) }}</time>
          <template v-if="!comment.is_deleted">
            <button type="button" @click="replying = !replying">Reply</button>
            <template v-if="comment.is_author">
              <button type="button" @click="editing = true">Edit</button>
              <button type="button" class="cnode__danger" :disabled="deleting" @click="remove">Delete</button>
            </template>
          </template>
        </div>

        <CommentForm
          v-if="replying"
          class="cnode__reply-form"
          :placeholder="`Reply to ${authorName}…`"
          submit-label="Post reply"
          :send="reply"
          autofocus
          cancelable
          @cancel="replying = false"
        />
      </div>
    </div>

    <template v-if="comment.replies.length">
      <button type="button" class="cnode__toggle" :class="{ 'cnode__toggle--flat': flat }" :aria-expanded="open" @click="open = !open">
        <Icon name="chevron" :size="14" :class="{ 'cnode__chev--open': open }" />
        {{ open ? 'Hide replies' : `View ${replyCount} ${replyCount === 1 ? 'reply' : 'replies'}` }}
      </button>
      <ul v-if="open" class="cnode__replies" :class="{ 'cnode__replies--flat': flat }">
        <CommentNode v-for="r in comment.replies" :key="r.id" :comment="r" :depth="depth + 1" />
      </ul>
    </template>
  </li>
</template>

<script setup>
import { computed, inject, ref } from 'vue';
import { fullDate, timeAgo } from '../time.mjs';
import CommentForm from './CommentForm.vue';
import Icon from './Icon.vue';
import UserAvatar from './UserAvatar.vue';

// The template refers to itself as <CommentNode> for the replies.
defineOptions({ name: 'CommentNode' });

// Replies deeper than this line up with their parent instead of indenting further.
const MAX_INDENT = 4;
// Threads deeper than this start collapsed ("View 3 replies").
const OPEN_DEPTH = 2;

// comment: { id, parent, body, author, is_deleted, is_author, created_at, replies: [...] }
const props = defineProps({
  comment: { type: Object, required: true },
  depth: { type: Number, default: 0 },
});

const { add, edit, remove: removeComment } = inject('comments');

const replying = ref(false);
const editing = ref(false);
const deleting = ref(false);
const open = ref(props.depth < OPEN_DEPTH);
const flat = computed(() => props.depth + 1 >= MAX_INDENT);

const authorName = computed(() => (props.comment.author ? `@${props.comment.author.username}` : 'Deleted user'));

// Every reply below this comment, at any depth.
const replyCount = computed(() => {
  const count = (nodes) => nodes.reduce((n, c) => n + 1 + count(c.replies), 0);
  return count(props.comment.replies);
});

async function reply(body) {
  await add(body, props.comment);
  replying.value = false;
  open.value = true;
}

async function saveEdit(body) {
  await edit(props.comment, body);
  editing.value = false;
}

async function remove() {
  if (!window.confirm('Delete this comment?')) return;
  deleting.value = true;
  try {
    await removeComment(props.comment);
  } catch {
    window.alert('Could not delete the comment. Please try again.');
  } finally {
    deleting.value = false;
  }
}
</script>

<style scoped>
.cnode {
  list-style: none;
}

.cnode__row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.cnode__main {
  flex: 1;
  min-width: 0;
}

.cnode__bubble {
  display: inline-block;
  max-width: 100%;
  padding: 7px 12px 8px;
  background: var(--surface-muted);
  border-radius: 4px 16px 16px 16px;
}

.cnode__bubble--deleted {
  font-size: 13px;
  color: var(--muted);
}

.cnode__author {
  font-size: 13px;
  font-weight: 600;
}

.cnode__body {
  margin: 1px 0 0;
  font-size: 14px;
  line-height: 1.45;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.cnode__meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 3px 0 0 12px;
  font-size: 12px;
  color: var(--muted);
}

.cnode__meta button,
.cnode__toggle {
  padding: 0;
  font: inherit;
  font-weight: 600;
  color: var(--muted);
  background: none;
  border: 0;
  cursor: pointer;
}

.cnode__meta button:hover {
  color: var(--primary);
}

.cnode__meta .cnode__danger:hover {
  color: var(--danger);
}

.cnode__reply-form {
  margin-top: 8px;
}

.cnode__toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 6px 0 0 40px;
  font-size: 12px;
  color: var(--primary);
}

.cnode__toggle--flat {
  margin-left: 0;
}

.cnode__toggle .icon {
  transform: rotate(-90deg);
  transition: transform 0.15s;
}

.cnode__toggle .cnode__chev--open {
  transform: none;
}

/* Replies hang off a thread line under the parent's avatar. */
.cnode__replies {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 10px 0 0 15px;
  padding: 0 0 0 23px;
  border-left: 2px solid var(--border);
}

.cnode__replies--flat {
  margin-left: 0;
  padding-left: 0;
  border-left: 0;
}

@media (max-width: 480px) {
  .cnode__replies {
    padding-left: 12px;
  }
  .cnode__toggle {
    margin-left: 34px;
  }
}
</style>
