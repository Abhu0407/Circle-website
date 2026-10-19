<template>
  <main class="auth">
    <div class="frame">
      <!-- Left: dark showcase panel (brand + what the app does) -->
      <section class="showcase" aria-hidden="true">
        <BrandLogo />
        <span class="location"><Icon name="pin" :size="13" /> Mumbai</span>

        <h2 class="showcase__title">Discover people &amp; activities near you</h2>

        <div class="chips">
          <span class="chip">Sports</span>
          <span class="chip">Tech</span>
          <span class="chip">Arts</span>
          <span class="chip">Within 10km</span>
        </div>

        <ul class="features">
          <li class="feature">
            <span class="feature__icon"><Icon name="compass" /></span>
            <div>
              <strong>Find your people</strong>
              <p>Meet people nearby who share your interests.</p>
            </div>
          </li>
          <li class="feature">
            <span class="feature__icon"><Icon name="users" /></span>
            <div>
              <strong>Join communities</strong>
              <p>Sports, tech, arts and more, close to where you are.</p>
            </div>
          </li>
          <li class="feature">
            <span class="feature__icon"><Icon name="clock" /></span>
            <div>
              <strong>See what's happening</strong>
              <p>Spot activities happening around you today.</p>
            </div>
          </li>
        </ul>
      </section>

      <!-- Right: the form -->
      <section class="panel">
        <div class="card">
          <div class="card__brand">
            <BrandLogo dark :size="26" />
          </div>
          <slot />

          <footer v-if="$slots.footer" class="card__footer">
            <slot name="footer" />
          </footer>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup>
import BrandLogo from './BrandLogo.vue';
import Icon from './Icon.vue';
</script>

<style scoped>
/* ---------- page + frame ---------- */
.auth {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 32px 16px;
  background:
    radial-gradient(1200px 600px at 10% 0%, #0f3b47 0%, transparent 60%),
    radial-gradient(900px 600px at 100% 100%, #10284a 0%, transparent 55%),
    var(--night-900);
}

.frame {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  width: 100%;
  max-width: 1080px;
  overflow: hidden;
  background: var(--night-800);
  border: 1px solid var(--night-border);
  border-radius: 24px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
}

/* ---------- showcase (left) ---------- */
.showcase {
  display: flex;
  flex-direction: column;
  padding: 36px 36px 32px;
  color: var(--night-text);
  background: linear-gradient(165deg, var(--night-700) 0%, var(--night-800) 65%);
}

.location {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  align-self: flex-start;
  margin: 10px 0 0 42px;
  padding: 2px 10px;
  font-size: 12px;
  color: var(--night-muted);
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
}

.showcase__title {
  margin: 32px 0 14px;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--night-border);
  border-radius: 12px;
}

.chip {
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 8px;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 24px 0 0;
  padding: 0;
  list-style: none;
}

.feature {
  display: flex;
  gap: 14px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--night-border);
  border-radius: 14px;
}

.feature__icon {
  display: grid;
  flex: none;
  place-items: center;
  width: 40px;
  height: 40px;
  color: #fff;
  background: linear-gradient(135deg, var(--teal), var(--primary));
  border-radius: 12px;
}

.feature strong {
  font-size: 15px;
  font-weight: 600;
}

.feature p {
  margin: 2px 0 0;
  font-size: 13px;
  color: var(--night-muted);
}

/* ---------- form panel (right) ---------- */
.panel {
  display: grid;
  place-items: center;
  padding: 32px;
  background: linear-gradient(180deg, #e6eef7 0%, var(--bg) 100%);
}

.card {
  width: 100%;
  max-width: 400px;
  padding: 32px 28px;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.card__brand {
  display: none;
  margin-bottom: 16px;
}

.card__footer {
  margin-top: 22px;
  padding-top: 18px;
  text-align: center;
  color: var(--muted);
  border-top: 1px solid var(--border);
}

/* ---------- responsive ---------- */
@media (max-width: 900px) {
  .frame {
    grid-template-columns: 1fr;
    max-width: 480px;
  }
  .showcase {
    display: none;
  }
  .card__brand {
    display: block;
  }
  .panel {
    padding: 20px;
  }
}

@media (max-width: 420px) {
  .auth {
    padding: 0;
  }
  .frame {
    min-height: 100vh;
    border: 0;
    border-radius: 0;
  }
  .card {
    padding: 24px 18px;
  }
}
</style>
