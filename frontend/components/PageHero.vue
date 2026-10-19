<!--
  The header box at the top of a PageSheet (same look as Profile's): a
  gradient cover (or a cover photo), a round picture overlapping it, the
  name with a meta line, actions on the right, and an optional stats row.
  Usage:
    <PageHero :name="c.name" :cover="c.image" :picture="c.image" :initial="c.name[0]">
      <template #meta><span>Tech</span></template>
      <template #actions><ActionButton ... /></template>
      <template #stats><HeroStat :value="12" label="Members" @click="..." /></template>
    </PageHero>
  Slot `picture` replaces the round picture (e.g. to add a camera button);
  slot `about` adds text (e.g. a description) under the name.
-->
<template>
  <article class="hero">
    <div class="hero__cover" :class="{ 'hero__cover--photo': cover }" :style="cover ? { backgroundImage: `url(${cover})` } : null">
      <slot name="cover" />
    </div>

    <div class="hero__row">
      <div class="hero__picture">
        <slot name="picture">
          <img v-if="picture" :src="picture" alt="" class="hero__img" />
          <span v-else class="hero__img hero__img--initial">{{ initial }}</span>
        </slot>
      </div>

      <div class="hero__info">
        <h2 class="hero__name" :class="{ 'hero__name--placeholder': placeholder }">{{ name }}</h2>
        <p v-if="$slots.meta" class="hero__meta"><slot name="meta" /></p>
      </div>

      <div v-if="$slots.actions" class="hero__actions"><slot name="actions" /></div>
    </div>

    <div v-if="$slots.about" class="hero__about"><slot name="about" /></div>

    <div v-if="$slots.stats" class="hero__stats"><slot name="stats" /></div>
    <div v-else class="hero__end"></div>
  </article>
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  // Grey the name (e.g. "Community name" before one is typed).
  placeholder: { type: Boolean, default: false },
  cover: { type: String, default: '' },
  picture: { type: String, default: '' },
  initial: { type: String, default: '' },
});
</script>

<style scoped>
.hero {
  overflow: hidden;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
}

.hero__cover {
  position: relative;
  height: 96px;
  background:
    radial-gradient(400px 120px at 85% 0%, rgba(34, 184, 201, 0.55), transparent 70%),
    linear-gradient(120deg, #1f6fe5 0%, #13284a 100%);
  background-position: center;
  background-size: cover;
}

.hero__cover--photo {
  height: 150px;
}

/* The picture overlaps the cover; the name always starts below it. */
.hero__row {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 16px;
  padding: 0 24px;
  margin-top: -44px;
}

.hero__picture {
  position: relative;
  flex: none;
  width: 104px;
  height: 104px;
}

.hero__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: var(--surface-muted);
  border: 4px solid var(--surface);
  border-radius: 50%;
  box-shadow: 0 6px 16px rgba(8, 19, 31, 0.18);
}

.hero__img--initial {
  display: grid;
  place-items: center;
  font-size: 40px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--teal), var(--primary));
}

.hero__info {
  flex: 1 1 200px;
  align-self: flex-start;
  min-width: 0;
  padding: 54px 0 4px;
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

.hero__name--placeholder {
  color: var(--muted);
}

.hero__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  margin: 4px 0 0;
  font-size: 14px;
  color: var(--muted);
}

.hero__meta :slotted(span) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.hero__actions {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.hero__end {
  height: 20px;
}

.hero__about {
  padding: 16px 24px 0;
}

/* ---------- stats (HeroStat buttons) ---------- */
.hero__stats {
  display: grid;
  grid-auto-columns: minmax(0, 1fr);
  grid-auto-flow: column;
  gap: 12px;
  margin-top: 20px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border);
}

@media (max-width: 560px) {
  .hero__row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    padding: 0 16px;
  }
  .hero__info {
    flex: none;
    width: 100%;
    padding-top: 0;
  }
  .hero__about {
    padding: 14px 16px 0;
  }
  .hero__stats {
    gap: 8px;
    padding: 14px 16px 16px;
  }
}
</style>
