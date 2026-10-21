<!--
  A post. The community is the title; the member who wrote it is tagged
  under it ("by @alice"). Like, Comment (opens the threads) and Share
  (the phone's share sheet, or copies the link).
  Usage: <PostCard :post="p" :posts-api="postsApi" :user="user" @deleted="..." />
-->
<template>
  <article class="post">
    <header class="post__head">
      <img v-if="p.community.image" :src="p.community.image" alt="" class="post__badge post__badge--img" />
      <span v-else class="post__badge" aria-hidden="true">{{ p.community.name.charAt(0).toUpperCase() }}</span>

      <div class="post__heading">
        <h2 class="post__community">{{ p.community.name }}</h2>
        <p class="post__by">
          <UserAvatar :user="p.author" :size="18" />
          <span class="post__author">by <strong>{{ p.author ? `@${p.author.username}` : 'a former member' }}</strong></span>
          <span aria-hidden="true">·</span>
          <a :href="p.url" class="post__time" :title="fullDate(p.created_at)">
            <time :datetime="p.created_at">{{ timeAgo(p.created_at) }}</time>
          </a>
        </p>
      </div>

      <button
        v-if="p.is_author"
        type="button"
        class="post__delete"
        aria-label="Delete post"
        title="Delete post"
        :disabled="deleting"
        @click="remove"
      >
        <Icon name="trash" :size="16" />
      </button>
    </header>

    <p v-if="p.body" class="post__body">{{ p.body }}</p>
    <img v-if="p.image" :src="p.image" alt="" class="post__image" loading="lazy" />
    <video
      v-else-if="p.video"
      :src="p.video"
      class="post__image post__video"
      controls
      playsinline
      preload="metadata"
    ></video>

    <div v-if="p.likes_count || p.comments_count || p.shares_count" class="post__stats">
      <span v-if="p.likes_count">{{ plural(p.likes_count, 'like') }}</span>
      <button v-if="p.comments_count" type="button" @click="commentsOpen = true">{{ plural(p.comments_count, 'comment') }}</button>
      <span v-if="p.shares_count">{{ plural(p.shares_count, 'share') }}</span>
    </div>

    <div class="post__actions">
      <button type="button" class="post__action" :class="{ 'post__action--liked': p.liked }" :aria-pressed="p.liked" @click="toggleLike">
        <Icon name="heart" :size="18" /> {{ p.liked ? 'Liked' : 'Like' }}
      </button>
      <button type="button" class="post__action" :aria-expanded="commentsOpen" @click="commentsOpen = !commentsOpen">
        <Icon name="chat" :size="18" /> Comment
      </button>
      <button type="button" class="post__action" @click="share">
        <Icon :name="shared ? 'check' : 'share'" :size="18" /> {{ shared || 'Share' }}
      </button>
    </div>

    <CommentSection
      v-if="commentsOpen"
      :api="`${postsApi}${p.id}/comments/`"
      :user="user"
      :autofocus="!showComments"
      @count="p.comments_count = $event"
    />
  </article>
</template>

<script setup>
import { ref } from 'vue';
import { apiDelete, apiPost } from '../api.mjs';
import { fullDate, timeAgo } from '../time.mjs';
import CommentSection from './CommentSection.vue';
import Icon from './Icon.vue';
import UserAvatar from './UserAvatar.vue';

// post: see PostSerializer in backend/apps/posts/serializers.py
const props = defineProps({
  post: { type: Object, required: true },
  postsApi: { type: String, required: true },
  user: { type: Object, required: true },
  // Start with the comments open (the post's own page).
  showComments: { type: Boolean, default: false },
});
const emit = defineEmits(['deleted']);

const p = ref({ ...props.post });
const commentsOpen = ref(props.showComments);
const deleting = ref(false);
// "Link copied" / "Shared" for a moment after sharing.
const shared = ref('');

const postApi = () => `${props.postsApi}${p.value.id}/`;
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

// Show the change straight away; put it back if the server says no.
async function toggleLike() {
  const liked = !p.value.liked;
  p.value.liked = liked;
  p.value.likes_count += liked ? 1 : -1;
  try {
    const res = await (liked ? apiPost : apiDelete)(`${postApi()}like/`);
    p.value.liked = res.liked;
    p.value.likes_count = res.likes_count;
  } catch {
    p.value.liked = !liked;
    p.value.likes_count += liked ? -1 : 1;
  }
}

async function share() {
  const url = new URL(p.value.url, window.location.origin).href;
  if (navigator.share) {
    try {
      await navigator.share({ title: p.value.community.name, text: p.value.body.slice(0, 140), url });
    } catch {
      return; // closed the share sheet
    }
    flash('Shared');
  } else if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(url);
    flash('Link copied');
  } else {
    window.prompt('Copy this link to share the post:', url);
  }
  try {
    p.value.shares_count = (await apiPost(`${postApi()}share/`)).shares_count;
  } catch {
    // The count is only a nice-to-have.
  }
}

let flashTimer;
function flash(text) {
  shared.value = text;
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => (shared.value = ''), 2000);
}

async function remove() {
  if (!window.confirm('Delete this post? Its comments will be deleted too.')) return;
  deleting.value = true;
  try {
    await apiDelete(postApi());
    emit('deleted', p.value.id);
  } catch {
    window.alert('Could not delete the post. Please try again.');
    deleting.value = false;
  }
}
</script>

<style scoped>
button {
  font: inherit;
  cursor: pointer;
}

.post {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 20px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
}

/* ---------- header: community is the title ---------- */
.post__head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.post__badge {
  display: grid;
  flex: none;
  place-items: center;
  width: 44px;
  height: 44px;
  font-size: 19px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--teal), var(--primary));
  border-radius: 12px;
}

.post__badge--img {
  object-fit: cover;
  background: var(--surface-muted);
}

.post__heading {
  flex: 1;
  min-width: 0;
}

.post__community {
  margin: 0;
  overflow: hidden;
  font-size: 17px;
  font-weight: 600;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post__by {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: 3px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.post__author strong {
  font-weight: 600;
  color: var(--text);
}

.post__time {
  font-weight: 400;
  color: var(--muted);
}

.post__delete {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  color: var(--muted);
  background: none;
  border: 0;
  border-radius: 9px;
}

.post__delete:hover {
  color: var(--danger);
  background: var(--danger-bg);
}

/* ---------- content ---------- */
.post__body {
  margin: 0;
  font-size: 15px;
  line-height: 1.55;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.post__image {
  display: block;
  width: 100%;
  max-height: 520px;
  object-fit: cover;
  background: var(--surface-muted);
  border-radius: 12px;
}

.post__video {
  object-fit: contain;
  background: #000;
}

.post__stats {
  display: flex;
  gap: 14px;
  font-size: 13px;
  color: var(--muted);
}

.post__stats button {
  padding: 0;
  color: inherit;
  background: none;
  border: 0;
}

.post__stats button:hover {
  text-decoration: underline;
}

/* ---------- like / comment / share ---------- */
.post__actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  padding-top: 6px;
  border-top: 1px solid var(--border);
}

.post__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 8px 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--muted);
  background: none;
  border: 0;
  border-radius: 10px;
  transition: background 0.15s, color 0.15s;
}

.post__action:hover {
  color: var(--text);
  background: var(--surface-muted);
}

.post__action--liked,
.post__action--liked:hover {
  color: var(--red);
}

.post__action--liked .icon {
  fill: currentColor;
}

@media (max-width: 480px) {
  .post {
    padding: 14px 14px 10px;
  }
}
</style>
