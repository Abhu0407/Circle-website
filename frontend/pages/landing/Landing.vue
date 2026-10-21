<template>
  <div class="landing">
    <!-- ---------- top bar ---------- -->
    <header class="topbar">
      <div class="wrap topbar__inner">
        <a href="/" class="topbar__brand" aria-label="Circle home"><BrandLogo :size="28" /></a>
        <nav class="topbar__nav" aria-label="Page sections">
          <a href="#features">Features</a>
          <a href="#how">How it works</a>
        </nav>
        <div class="topbar__actions">
          <a :href="signinUrl" class="btn btn--ghost">Sign in</a>
          <a :href="signupUrl" class="btn btn--primary">Sign up</a>
        </div>
      </div>
    </header>

    <!-- ---------- hero ---------- -->
    <section class="hero">
      <div class="wrap hero__inner">
        <div class="hero__copy">
          <span class="pill"><Icon name="pin" :size="13" /> Communities near you</span>
          <h1 class="hero__title">
            Discover people &amp; activities
            <span class="grad">around you</span>
          </h1>
          <p class="hero__lead">
            Circle connects you with people nearby who share your interests. Join local
            communities, chat live, share photos and videos, and see what's happening
            close to where you are.
          </p>
          <div class="hero__cta">
            <a :href="signupUrl" class="btn btn--primary btn--lg">Create free account</a>
            <a :href="signinUrl" class="btn btn--outline btn--lg">I already have an account</a>
          </div>
          <div class="chips">
            <span v-for="tag in tags" :key="tag" class="chip">{{ tag }}</span>
          </div>
        </div>

        <!-- Preview: a few sample community cards + a chat bubble -->
        <div class="preview" aria-hidden="true">
          <div class="preview__card preview__card--main">
            <img :src="covers['sports-football']" alt="" class="preview__cover" />
            <div class="preview__body">
              <span class="tag">Sports</span>
              <strong>Sunday Football Crew</strong>
              <span class="meta"><Icon name="users" :size="14" /> 48 members · 2 km away</span>
            </div>
          </div>

          <div class="preview__row">
            <div class="preview__card preview__card--mini">
              <img :src="covers['tech-code']" alt="" class="preview__cover" />
              <div class="preview__body">
                <strong>Tech Meetups</strong>
                <span class="meta">126 members</span>
              </div>
            </div>
            <div class="preview__card preview__card--mini">
              <img :src="covers['music-guitar']" alt="" class="preview__cover" />
              <div class="preview__body">
                <strong>Jam Sessions</strong>
                <span class="meta">32 members</span>
              </div>
            </div>
          </div>

          <div class="bubble">
            <span class="bubble__avatar">A</span>
            <div>
              <strong>alex_vibes</strong>
              <p>Who's in for a game at 6? ⚽</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ---------- people meeting up ---------- -->
    <section class="section section--tight">
      <div class="wrap">
        <div class="section__head">
          <span class="eyebrow">Meet your circle</span>
          <h2>From strangers to friends</h2>
          <p>Hang out with your friends, meet new people who love what you love, and turn a group chat into real plans.</p>
        </div>

        <div class="gallery">
          <figure v-for="m in moments" :key="m.scene" class="moment" :class="{ 'moment--big': m.big, 'moment--wide': m.wide }">
            <img :src="scenes[m.scene]" :alt="m.alt" loading="lazy" />
            <figcaption>
              <strong>{{ m.title }}</strong>
              <span>{{ m.text }}</span>
            </figcaption>
          </figure>
        </div>
      </div>
    </section>

    <!-- ---------- features ---------- -->
    <section id="features" class="section">
      <div class="wrap">
        <div class="section__head">
          <span class="eyebrow">Features</span>
          <h2>Everything you need to find your people</h2>
          <p>Circle brings your local scene into one place, from finding a group to talking with it.</p>
        </div>

        <ul class="features">
          <li v-for="f in features" :key="f.title" class="feature">
            <span class="feature__icon"><Icon :name="f.icon" /></span>
            <h3>{{ f.title }}</h3>
            <p>{{ f.text }}</p>
          </li>
        </ul>
      </div>
    </section>

    <!-- ---------- how it works ---------- -->
    <section id="how" class="section section--light">
      <div class="wrap">
        <div class="section__head">
          <span class="eyebrow">How it works</span>
          <h2>Get started in three steps</h2>
        </div>

        <ol class="steps">
          <li v-for="(s, i) in steps" :key="s.title" class="step">
            <span class="step__num">{{ i + 1 }}</span>
            <h3>{{ s.title }}</h3>
            <p>{{ s.text }}</p>
          </li>
        </ol>
      </div>
    </section>

    <!-- ---------- final call to action ---------- -->
    <section class="section">
      <div class="wrap">
        <div class="cta">
          <img :src="scenes['circle-of-friends']" alt="" class="cta__art" aria-hidden="true" />
          <div class="cta__copy">
            <h2>Your circle is waiting</h2>
            <p>Join Circle today. It's free, and setup takes under a minute.</p>
          </div>
          <div class="cta__actions">
            <a :href="signupUrl" class="btn btn--primary btn--lg">Sign up</a>
            <a :href="signinUrl" class="btn btn--outline btn--lg">Sign in</a>
          </div>
        </div>
      </div>
    </section>

    <footer class="footer">
      <div class="wrap footer__inner">
        <BrandLogo :size="22" />
        <span>Find people &amp; activities near you.</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import BrandLogo from '../../components/BrandLogo.vue';
import Icon from '../../components/Icon.vue';

// Props come from LandingPageView.get_page_props() in Django.
defineProps({
  signinUrl: { type: String, required: true },
  signupUrl: { type: String, required: true },
  covers: { type: Object, default: () => ({}) }, // {cover key: image url}
  scenes: { type: Object, default: () => ({}) }, // {scene name: image url}
});

const moments = [
  { scene: 'friends-circle', big: true, title: 'Your friend circle', text: 'Campfires, game nights and weekend plans with your crew.', alt: 'Friends sitting around a campfire at night' },
  { scene: 'meet-new-people', title: 'Meet new people', text: 'Say hi to strangers nearby who share your interests.', alt: 'Two groups of people meeting and shaking hands in a park' },
  { scene: 'coffee-meetup', title: 'Coffee catch-ups', text: 'Turn a chat into a meetup at the café around the corner.', alt: 'Four friends chatting over coffee in a café' },
  { scene: 'celebrate-together', wide: true, title: 'Play & celebrate', text: 'Find a team, play a match, cheer together.', alt: 'A group of friends cheering after a football game' },
];

const tags = ['Sports', 'Tech', 'Arts', 'Music', 'Outdoors', 'Within 10km'];

const features = [
  { icon: 'sparkle', title: 'For You feed', text: 'Posts from every community, picked for your interests, with new groups to join in between.' },
  { icon: 'compass', title: 'Discover communities', text: 'Browse and filter groups by category and distance to find the ones near you.' },
  { icon: 'chat', title: 'Live community chat', text: 'Talk with your community in real time. Share files, photos and emoji as you go.' },
  { icon: 'video', title: 'Photo & video posts', text: 'Share moments with your groups, then like and comment in threaded discussions.' },
  { icon: 'pin', title: 'Activity map', text: "See who's active around you on a map. Locations are rounded to about 1 km so exact addresses stay private." },
  { icon: 'plus', title: 'Create your own', text: 'Start a community in seconds: pick a category, a cover and a location.' },
  { icon: 'bell', title: 'Notifications', text: 'Stay in the loop when new posts and communities show up.' },
  { icon: 'user', title: 'Your profile', text: 'Choose an avatar, add your interests and location, and show the communities you belong to.' },
];

const steps = [
  { title: 'Create your account', text: 'Sign up with your email or Google in under a minute.' },
  { title: 'Add your interests', text: 'Tell us what you love and where you are, and we tailor your feed.' },
  { title: 'Join & connect', text: 'Join nearby communities, chat live and meet up in real life.' },
];
</script>

<style scoped>
.landing {
  min-height: 100vh;
  overflow-x: clip;
  color: var(--night-text);
  background:
    radial-gradient(1200px 600px at 10% 0%, #0f3b47 0%, transparent 60%),
    radial-gradient(900px 600px at 100% 30%, #10284a 0%, transparent 55%),
    var(--night-900);
}

.wrap {
  width: 100%;
  max-width: 1160px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ---------- buttons ---------- */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  padding: 0 18px;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  border-radius: 10px;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.btn:hover {
  text-decoration: none;
}

.btn--lg {
  height: 48px;
  padding: 0 24px;
  font-size: 15px;
}

.btn--primary {
  color: #fff;
  background: var(--primary);
}

.btn--primary:hover {
  background: var(--primary-hover);
}

.btn--ghost {
  color: var(--night-text);
}

.btn--ghost:hover {
  background: rgba(255, 255, 255, 0.08);
}

.btn--outline {
  color: var(--night-text);
  border: 1px solid rgba(255, 255, 255, 0.22);
}

.btn--outline:hover {
  background: rgba(255, 255, 255, 0.08);
}

/* ---------- top bar ---------- */
.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(8, 19, 31, 0.72);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--night-border);
}

.topbar__inner {
  display: flex;
  align-items: center;
  gap: 24px;
  height: 64px;
}

.topbar__brand:hover {
  text-decoration: none;
}

.topbar__nav {
  display: flex;
  gap: 24px;
  margin-left: 16px;
}

.topbar__nav a {
  font-size: 14px;
  font-weight: 500;
  color: var(--night-muted);
}

.topbar__nav a:hover {
  color: var(--night-text);
  text-decoration: none;
}

.topbar__actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

/* ---------- hero ---------- */
.hero {
  padding: 72px 0 88px;
}

.hero__inner {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 56px;
  align-items: center;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  font-size: 13px;
  color: var(--night-muted);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--night-border);
  border-radius: 999px;
}

.hero__title {
  margin: 18px 0 16px;
  overflow-wrap: break-word;
  font-size: clamp(34px, 5vw, 54px);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.025em;
}

.grad {
  background: linear-gradient(90deg, var(--teal), #5a9bff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero__lead {
  max-width: 540px;
  margin: 0;
  font-size: 17px;
  color: var(--night-muted);
}

.hero__cta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 28px;
}

.chip {
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 8px;
}

/* ---------- preview cards ---------- */
.preview {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--night-border);
  border-radius: 24px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
}

.preview__card {
  overflow: hidden;
  color: var(--text);
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.preview__cover {
  display: block;
  width: 100%;
  height: 150px;
  object-fit: cover;
  background: var(--surface-muted);
}

.preview__card--mini .preview__cover {
  height: 90px;
}

.preview__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px 14px;
}

.preview__body strong {
  font-size: 15px;
}

.preview__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.tag {
  align-self: flex-start;
  padding: 1px 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-soft);
  border-radius: 6px;
}

.meta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--muted);
}

.bubble {
  position: absolute;
  bottom: 120px;
  left: -36px;
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  color: var(--text);
  background: var(--surface);
  border-radius: 14px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35);
}

.bubble strong {
  font-size: 13px;
}

.bubble p {
  margin: 0;
  font-size: 13px;
  color: var(--muted);
}

.bubble__avatar {
  display: grid;
  flex: none;
  place-items: center;
  width: 32px;
  height: 32px;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--teal), var(--primary));
  border-radius: 50%;
}

/* ---------- sections ---------- */
.section {
  padding: 88px 0;
}

.section--light {
  color: var(--text);
  background: linear-gradient(180deg, #e6eef7 0%, var(--bg) 100%);
}

.section__head {
  max-width: 640px;
  margin: 0 auto 48px;
  text-align: center;
}

.section__head h2 {
  margin: 8px 0 12px;
  font-size: clamp(26px, 3.5vw, 36px);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.section__head p {
  margin: 0;
  font-size: 16px;
  color: var(--night-muted);
}

.eyebrow {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--teal);
}

.section--tight {
  padding-top: 24px;
}

/* ---------- gallery of people meeting up ---------- */
.gallery {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr;
  grid-template-rows: 240px 240px;
  gap: 18px;
}

.moment {
  position: relative;
  margin: 0;
  overflow: hidden;
  border: 1px solid var(--night-border);
  border-radius: 20px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
}

.moment--big {
  grid-row: span 2;
}

.moment--wide {
  grid-column: span 2;
}

.moment img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.moment:hover img {
  transform: scale(1.04);
}

.moment figcaption {
  position: absolute;
  inset: auto 0 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 40px 18px 16px;
  background: linear-gradient(180deg, transparent, rgba(8, 19, 31, 0.85));
}

.moment figcaption strong {
  font-size: 16px;
  font-weight: 600;
}

.moment figcaption span {
  font-size: 13px;
  color: var(--night-muted);
}

/* ---------- features ---------- */
.features {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.feature {
  padding: 22px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--night-border);
  border-radius: 16px;
  transition: transform 0.15s, background 0.15s;
}

.feature:hover {
  background: rgba(255, 255, 255, 0.09);
  transform: translateY(-2px);
}

.feature__icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  color: #fff;
  background: linear-gradient(135deg, var(--teal), var(--primary));
  border-radius: 12px;
}

.feature h3 {
  margin: 16px 0 6px;
  font-size: 16px;
  font-weight: 600;
}

.feature p {
  margin: 0;
  font-size: 14px;
  color: var(--night-muted);
}

/* ---------- steps ---------- */
.steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.step {
  padding: 28px 24px;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.step__num {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  font-weight: 700;
  color: var(--primary);
  background: var(--primary-soft);
  border-radius: 10px;
}

.step h3 {
  margin: 16px 0 6px;
  font-size: 17px;
  font-weight: 600;
}

.step p {
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}

/* ---------- final CTA ---------- */
.cta {
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 32px 36px;
  background: linear-gradient(135deg, var(--night-700), var(--night-800));
  border: 1px solid var(--night-border);
  border-radius: 24px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
}

.cta__art {
  flex: none;
  width: 112px;
  height: 112px;
  border-radius: 26px;
  box-shadow: 0 12px 30px rgba(31, 111, 229, 0.35);
}

.cta__copy h2 {
  margin: 0 0 6px;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.cta__copy p {
  margin: 0;
  color: var(--night-muted);
}

.cta__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-left: auto;
}

/* ---------- footer ---------- */
.footer {
  padding: 28px 0;
  border-top: 1px solid var(--night-border);
}

.footer__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  color: var(--night-muted);
}

/* ---------- responsive ---------- */
@media (max-width: 1024px) {
  .features {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .hero {
    padding: 48px 0 64px;
  }
  .hero__inner {
    grid-template-columns: minmax(0, 1fr);
    gap: 40px;
  }
  .bubble {
    left: 12px;
  }
  .steps {
    grid-template-columns: 1fr;
  }
  .gallery {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 320px 220px 220px;
  }
  .moment--big,
  .moment--wide {
    grid-column: span 2;
    grid-row: auto;
  }
  .cta {
    flex-direction: column;
    text-align: center;
  }
  .cta__actions {
    justify-content: center;
    margin-left: 0;
  }
}

@media (max-width: 640px) {
  .wrap {
    padding: 0 16px;
  }
  .topbar__nav {
    display: none;
  }
  .topbar__actions .btn {
    padding: 0 12px;
  }
  .section {
    padding: 64px 0;
  }
  .features {
    grid-template-columns: 1fr;
  }
  .gallery {
    grid-template-columns: 1fr;
    grid-template-rows: none;
    grid-auto-rows: 240px;
  }
  .moment--big,
  .moment--wide {
    grid-column: auto;
  }
  .hero__cta .btn {
    width: 100%;
  }
  .preview {
    padding: 14px;
  }
  .bubble {
    position: static;
  }
}
</style>
