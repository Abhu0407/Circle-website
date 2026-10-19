<!--
  A post's comments: a box to comment, then the threads (CommentNode).
  Loads the whole tree from `api` (/api/posts/<id>/comments/) and keeps it
  here; nested CommentNodes reach add/edit/remove through provide/inject.
  Emits `count` with the number of (not deleted) comments whenever it changes.
-->
<template>
  <section class="comments" aria-label="Comments">
    <div class="comments__new">
      <UserAvatar :user="user" :size="32" />
      <CommentForm class="comments__form" :send="(body) => add(body)" :autofocus="autofocus" />
    </div>

    <p v-if="loading" class="comments__note">Loading comments…</p>
    <p v-else-if="loadError" class="comments__note">
      {{ loadError }} <button type="button" @click="load">Try again</button>
    </p>
    <ul v-else-if="tree.length" class="comments__list">
      <CommentNode v-for="c in tree" :key="c.id" :comment="c" />
    </ul>
    <p v-else class="comments__note">No comments yet. Start the conversation.</p>
  </section>
</template>

<script setup>
import { onMounted, provide, ref, watch } from 'vue';
import { apiDelete, apiGet, apiPatch, apiPost } from '../api.mjs';
import CommentForm from './CommentForm.vue';
import CommentNode from './CommentNode.vue';
import UserAvatar from './UserAvatar.vue';

const props = defineProps({
  api: { type: String, required: true },
  user: { type: Object, required: true },
  autofocus: { type: Boolean, default: false },
});
const emit = defineEmits(['count']);

const tree = ref([]);
const loading = ref(true);
const loadError = ref('');

async function load() {
  loading.value = true;
  loadError.value = '';
  try {
    tree.value = await apiGet(props.api);
  } catch {
    loadError.value = 'Could not load comments.';
  } finally {
    loading.value = false;
  }
}

onMounted(load);

const countLive = (nodes) => nodes.reduce((n, c) => n + (c.is_deleted ? 0 : 1) + countLive(c.replies), 0);
watch(tree, (nodes) => emit('count', countLive(nodes)), { deep: true });

// Comment on the post, or reply to `parent` (a comment in the tree).
async function add(body, parent = null) {
  const node = await apiPost(props.api, { body, parent: parent ? parent.id : null });
  (parent ? parent.replies : tree.value).push(node);
}

async function edit(comment, body) {
  const updated = await apiPatch(`${props.api}${comment.id}/`, { body });
  comment.body = updated.body;
}

// The server may keep the comment as "deleted" (it has replies) or also
// clear out deleted parents, so reload the tree rather than guess.
async function remove(comment) {
  await apiDelete(`${props.api}${comment.id}/`);
  tree.value = await apiGet(props.api);
}

provide('comments', { add, edit, remove });
</script>

<style scoped>
.comments {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}

.comments__new {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.comments__form {
  flex: 1;
  min-width: 0;
}

.comments__list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0;
  padding: 0;
}

.comments__note {
  margin: 0;
  padding: 8px 0;
  font-size: 14px;
  text-align: center;
  color: var(--muted);
}

.comments__note button {
  padding: 0;
  font: inherit;
  font-weight: 600;
  color: var(--primary);
  background: none;
  border: 0;
  cursor: pointer;
}
</style>
