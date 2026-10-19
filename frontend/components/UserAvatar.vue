<!--
  A round avatar: the profile picture, or the first letter on a colour
  picked from the user's id. `user` may be null (deleted account/comment).
  Usage: <UserAvatar :user="post.author" :size="32" />
-->
<template>
  <img v-if="user && user.profile_picture" :src="user.profile_picture" alt="" class="uavatar uavatar--img" :style="box" />
  <span v-else class="uavatar" :style="{ ...box, '--a': colors[0], '--b': colors[1] }" aria-hidden="true">{{ initial }}</span>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  user: { type: Object, default: null },
  size: { type: Number, default: 32 },
});

const PALETTE = [
  ['#22b8c9', '#1f6fe5'],
  ['#f59f00', '#e8590c'],
  ['#be4bdb', '#7048e8'],
  ['#2fb36d', '#0c8599'],
  ['#e0475b', '#c2255c'],
];

const box = computed(() => ({ width: `${props.size}px`, height: `${props.size}px`, fontSize: `${props.size * 0.42}px` }));
const colors = computed(() => (props.user ? PALETTE[props.user.id % PALETTE.length] : ['#adb5bd', '#868e96']));
const initial = computed(() => {
  if (!props.user) return '?';
  return (props.user.name || props.user.username || '?').charAt(0).toUpperCase();
});
</script>

<style scoped>
.uavatar {
  display: grid;
  flex: none;
  place-items: center;
  font-weight: 700;
  line-height: 1;
  color: #fff;
  background: linear-gradient(135deg, var(--a), var(--b));
  border-radius: 50%;
}

.uavatar--img {
  object-fit: cover;
  background: var(--surface-muted);
}
</style>
