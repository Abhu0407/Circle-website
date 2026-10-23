<!--
  A private letter, shown only to the SPECIAL_EMAIL account. It doesn't use
  BaseLayout: no sidebar, no links to the rest of Circle except the one
  button that goes on to the main page.

  To change the words, edit LETTER below. Lines wrapped in “quotes” are
  shown as little love notes after the story.

  Photos live in frontend/special-photos/ (from Unsplash, free licence).
-->
<template>
  <main class="special">
    <!-- Photo collage behind everything. -->
    <div class="special__collage" aria-hidden="true">
      <figure v-for="p in polaroids" :key="p.src" class="special__polaroid" :style="p.style">
        <img :src="p.src" alt="" loading="lazy" />
      </figure>
    </div>

    <div class="special__hearts" aria-hidden="true">
      <span v-for="h in hearts" :key="h.id" class="special__heart" :style="h.style">{{ h.char }}</span>
    </div>

    <article class="special__card">
      <div class="special__card-bg" aria-hidden="true"></div>

      <div class="special__card-body">
        <p class="special__eyebrow">✿ Just for you ✿</p>
        <h1 class="special__title">Hey {{ name }} <span aria-hidden="true">♥</span></h1>

        <div class="special__letter">
          <p
            v-for="(line, i) in story"
            :key="i"
            :style="{ animationDelay: `${0.4 + i * 0.35}s` }"
          >{{ line }}</p>
        </div>

        <div
          class="special__divider"
          aria-hidden="true"
          :style="{ animationDelay: `${0.4 + story.length * 0.35}s` }"
        >
          <span></span>❀<span></span>
        </div>

        <ul class="special__notes">
          <li
            v-for="(line, i) in notes"
            :key="i"
            :style="{ animationDelay: `${0.6 + (story.length + i) * 0.35}s` }"
          >{{ line }}</li>
        </ul>

        <p class="special__sign" :style="{ animationDelay: `${0.6 + LETTER.length * 0.35}s` }">
          Forever yours ♥
        </p>

        <a class="special__go" :href="homeUrl">Go to Circle →</a>
      </div>
    </article>
  </main>
</template>

<script setup>
defineProps({
  name: { type: String, default: '' },
  homeUrl: { type: String, default: '/' },
});

// The words on the page, one paragraph per line.
const LETTER = [
  "I want to share some of my feelings with you.",

"When I saw you for the first time, I really liked the way you talked. In our very first meeting, you told me everything you wanted to share, so openly and honestly.",

"In our next conversation, I was completely confused when you started telling me about yourself. But after some time, I realized that you had shared everything about yourself without me even asking. That meant a lot to me.",

"By our next conversation, I felt free to talk to you and ask you anything.",

"After a few days of talking, you asked me to pause our conversations for a while, because you wanted us to first make our relationship clear before we continued. I felt bad at that moment, but then I understood it was the right thing for both of us.",

"After that, we met at my home, and I saw a completely different side of you, more than I had ever imagined.",

"Then we both committed to our relationship.",

"Since then, every conversation with you has felt calm and relaxing. Our time talking together has become the best and most important part of my life.",

"But I still feel regret about one thing: I forgot your exam date. I was so angry with myself for forgetting, and for not even wishing you luck. I’m truly sorry for that. I promise I’ll remember the things that matter to you.",


"“You came into my life so naturally, like you were always meant to be part of it.”",

"“Talking to you is the part of my day I look forward to the most.”",

"“Thank you for being honest with me from the very first day. That’s when I knew you were special.”",

"“I may make mistakes sometimes, but my feelings for you will never change.”",

"“Every conversation with you feels like home.”",

"“I don’t just love you for who you are, but for who I become when I’m with you.”"
];

const isNote = (line) => line.startsWith('“');
const story = LETTER.filter((line) => !isNote(line));
const notes = LETTER.filter(isNote).map((line) => line.replace(/^“|”$/g, ''));

// Tilted photos scattered around the edges of the page.
const PHOTO = (file) => `/static/special-photos/${file}`;
const polaroids = [
  { src: PHOTO('doll-pink.jpg'), style: { top: '6%', left: '3%', '--tilt': '-8deg', '--w': '190px' } },
  { src: PHOTO('flowers-ranunculus.jpg'), style: { top: '52%', left: '6%', '--tilt': '6deg', '--w': '170px' } },
  { src: PHOTO('flowers-petals.jpg'), style: { top: '8%', right: '4%', '--tilt': '7deg', '--w': '170px' } },
  { src: PHOTO('couple-flowers.jpg'), style: { top: '56%', right: '3%', '--tilt': '-5deg', '--w': '210px' } },
];

// Hearts and petals floating up, each with its own spot and speed.
const FLOATERS = ['♥', '❀', '♥', '✿', '♥', '❁'];
const hearts = Array.from({ length: 22 }, (_, id) => ({
  id,
  char: FLOATERS[id % FLOATERS.length],
  style: {
    left: `${(id * 53) % 100}%`,
    fontSize: `${14 + ((id * 7) % 22)}px`,
    animationDuration: `${9 + ((id * 3) % 8)}s`,
    animationDelay: `${-((id * 1.7) % 12)}s`,
  },
}));
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');

.special {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 48px 16px;
  overflow: hidden;
  background:
    linear-gradient(160deg, rgba(255, 227, 236, 0.55), rgba(247, 198, 224, 0.6)),
    url('/static/special-photos/flowers-pink.jpg') center / cover fixed,
    #ffd1dc;
  font-family: 'Lora', Georgia, serif;
}

/* ---------- Collage ---------- */

.special__collage {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.special__polaroid {
  position: absolute;
  width: var(--w);
  margin: 0;
  padding: 10px 10px 34px;
  background: #fffaf7;
  border-radius: 4px;
  box-shadow: 0 14px 30px rgba(120, 30, 60, 0.25);
  transform: rotate(var(--tilt));
  animation: special-sway 7s ease-in-out infinite alternate;
}

.special__polaroid img {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 5;
  object-fit: cover;
  border-radius: 2px;
}

/* Little tape strip on top of each photo. */
.special__polaroid::before {
  content: '';
  position: absolute;
  top: -10px;
  left: 50%;
  width: 70px;
  height: 22px;
  translate: -50% 0;
  background: rgba(255, 200, 215, 0.75);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

@keyframes special-sway {
  from { transform: rotate(var(--tilt)) translateY(0); }
  to { transform: rotate(calc(var(--tilt) * -0.4)) translateY(-10px); }
}

/* ---------- Floating hearts ---------- */

.special__hearts {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.special__heart {
  position: absolute;
  bottom: -40px;
  color: rgba(224, 71, 107, 0.45);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.7);
  animation: special-float linear infinite;
}

@keyframes special-float {
  from { transform: translateY(0) rotate(0deg); opacity: 0; }
  10% { opacity: 1; }
  to { transform: translateY(-115vh) rotate(25deg); opacity: 0; }
}

/* ---------- Letter card ---------- */

.special__card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 600px;
  border-radius: 28px;
  overflow: hidden;
  box-shadow:
    0 0 0 6px rgba(255, 255, 255, 0.55),
    0 30px 70px rgba(160, 40, 80, 0.35);
  text-align: center;
  color: #4a1f2e;
}

/* The couple-in-nature photo, softly blurred so faces stay dreamy. */
.special__card-bg {
  position: absolute;
  inset: -12px;
  background: url('/static/special-photos/couple-flowers.jpg') center 35% / cover;
  filter: blur(3px) saturate(1.1);
}

.special__card-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(255, 244, 248, 0.45) 0,
    rgba(255, 244, 248, 0.82) 260px,
    rgba(255, 244, 248, 0.86) 100%
  );
}

.special__card-body {
  position: relative;
  padding: 56px 36px 44px;
}

.special__eyebrow {
  margin: 0 0 6px;
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #c2335e;
  text-shadow: 0 1px 6px rgba(255, 255, 255, 0.9);
}

.special__title {
  margin: 0 0 32px;
  font-family: 'Dancing Script', cursive;
  font-size: clamp(40px, 9vw, 58px);
  font-weight: 700;
  color: #8e1d43;
  text-shadow: 0 2px 12px rgba(255, 255, 255, 0.95);
}

.special__title span {
  color: #e0476b;
  display: inline-block;
  animation: special-beat 1.4s ease-in-out infinite;
}

@keyframes special-beat {
  0%, 100% { transform: scale(1); }
  20% { transform: scale(1.25); }
  40% { transform: scale(1); }
}

.special__letter p,
.special__divider,
.special__notes li,
.special__sign {
  opacity: 0;
  animation: special-in 0.8s ease forwards;
}

.special__letter {
  text-align: left;
}

.special__letter p {
  margin: 0 0 18px;
  font-size: 17px;
  line-height: 1.85;
}

/* Fancy first letter of the letter. */
.special__letter p:first-child::first-letter {
  float: left;
  margin: 6px 8px 0 0;
  font-family: 'Dancing Script', cursive;
  font-size: 56px;
  line-height: 0.8;
  color: #d0466f;
}

.special__divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 32px 0 24px;
  font-size: 22px;
  color: #d0466f;
}

.special__divider span {
  flex: 1;
  height: 1px;
  background: linear-gradient(to right, transparent, #e88aa5, transparent);
}

.special__notes {
  display: grid;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.special__notes li {
  position: relative;
  padding: 16px 22px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(224, 71, 107, 0.2);
  box-shadow: 0 6px 18px rgba(160, 40, 80, 0.1);
  font-size: 17px;
  font-style: italic;
  line-height: 1.6;
  color: #7a2442;
}

.special__notes li::before {
  content: '♥';
  position: absolute;
  top: -10px;
  left: 50%;
  translate: -50% 0;
  font-style: normal;
  font-size: 15px;
  color: #e0476b;
}

.special__sign {
  margin: 36px 0 32px;
  font-family: 'Dancing Script', cursive;
  font-size: 34px;
  font-weight: 700;
  color: #c2335e;
}

@keyframes special-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}

.special__go {
  display: inline-block;
  padding: 13px 30px;
  border-radius: 999px;
  background: linear-gradient(135deg, #f06292, #d0466f);
  box-shadow: 0 8px 20px rgba(208, 70, 111, 0.35);
  color: #fff;
  font-family: 'Inter', system-ui, sans-serif;
  font-weight: 600;
  text-decoration: none;
  transition: transform 0.15s, box-shadow 0.15s;
}

.special__go:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 26px rgba(208, 70, 111, 0.45);
}

/* On smaller screens the photos would crowd the letter, so shrink and fade them. */
@media (max-width: 1100px) {
  .special__polaroid { --w: 130px !important; opacity: 0.55; }
}

@media (max-width: 640px) {
  .special { padding: 24px 12px; background-attachment: scroll; }
  .special__polaroid { --w: 100px !important; opacity: 0.4; }
  .special__card-body { padding: 44px 22px 36px; }
  .special__letter p,
  .special__notes li { font-size: 16px; }
}

@media (prefers-reduced-motion: reduce) {
  .special__heart,
  .special__polaroid,
  .special__title span { animation: none; }
  .special__letter p,
  .special__divider,
  .special__notes li,
  .special__sign { animation: none; opacity: 1; }
}
</style>
