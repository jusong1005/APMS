<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  dense: { type: Boolean, default: false }
})
</script>

<template>
  <section :class="['screen-panel', dense && 'screen-panel--dense']">
    <div class="screen-panel__titlebar">
      <span class="screen-panel__line" />
      <div class="screen-panel__heading">
        <h3>{{ title }}</h3>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
      <span class="screen-panel__line screen-panel__line--right" />
    </div>
    <div class="screen-panel__body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.screen-panel {
  position: relative;
  min-height: 0;
  overflow: hidden;
  border: 1px solid rgba(16, 185, 129, 0.38);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.065), rgba(255, 255, 255, 0.026));
  box-shadow: 0 0 28px rgba(16, 185, 129, 0.14), inset 0 0 30px rgba(16, 185, 129, 0.055);
  clip-path: polygon(0 18px, 18px 0, calc(100% - 18px) 0, 100% 18px, 100% calc(100% - 18px), calc(100% - 18px) 100%, 18px 100%, 0 calc(100% - 18px));
}

.screen-panel::before,
.screen-panel::after {
  content: '';
  position: absolute;
  pointer-events: none;
}

.screen-panel::before {
  inset: 0;
  border: 1px solid rgba(74, 222, 128, 0.16);
  clip-path: polygon(0 18px, 18px 0, calc(100% - 18px) 0, 100% 18px, 100% calc(100% - 18px), calc(100% - 18px) 100%, 18px 100%, 0 calc(100% - 18px));
}

.screen-panel::after {
  left: 20px;
  right: 20px;
  bottom: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(74, 222, 128, 0.75), transparent);
}

.screen-panel__titlebar {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 48px;
  padding: 0 18px;
}

.screen-panel__line {
  width: 58px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(74, 222, 128, 0.9));
}

.screen-panel__line--right {
  background: linear-gradient(90deg, rgba(74, 222, 128, 0.9), transparent);
}

.screen-panel__heading {
  min-width: 0;
  flex: 1;
  text-align: center;
}

.screen-panel__heading h3 {
  margin: 0;
  overflow: hidden;
  color: #d1fae5;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.screen-panel__heading p {
  margin: 3px 0 0;
  overflow: hidden;
  color: rgba(209, 250, 229, 0.58);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.screen-panel__body {
  position: relative;
  min-height: 0;
  height: calc(100% - 48px);
  padding: 12px 16px 16px;
}

.screen-panel--dense .screen-panel__body {
  padding: 8px 14px 14px;
}
</style>
