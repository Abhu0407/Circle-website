<!-- One post with its comments open: where a shared post link leads. -->
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
    <PageSheet title="Post" :back-url="post.community.url" :back-label="post.community.name">
      <PostCard :post="post" :posts-api="postsApi" :user="user" show-comments @deleted="leave" />
    </PageSheet>
  </BaseLayout>
</template>

<script setup>
import BaseLayout from '../../components/BaseLayout.vue';
import PageSheet from '../../components/PageSheet.vue';
import PostCard from '../../components/PostCard.vue';

// Props come from PostPageView.get_page_props() in Django.
const props = defineProps({
  user: { type: Object, required: true },
  post: { type: Object, required: true },
  postsApi: { type: String, required: true },
  homeUrl: { type: String, required: true },
  profileUrl: { type: String, required: true },
  signoutApi: { type: String, required: true },
  signinUrl: { type: String, required: true },
  mapTileUrl: { type: String, required: true },
  mapPeople: { type: Array, default: () => [] },
});

// After deleting the post, go back to its community.
function leave() {
  window.circleNavigate(props.post.community.url);
}
</script>
