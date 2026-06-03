<script setup>
import ScreenPanel from './ScreenPanel.vue'

defineProps({
  data: { type: Array, required: true }
})
</script>

<template>
  <ScreenPanel title="肉类最新入库价" subtitle="优先展示 Redis 实时价，无缓存时展示最新入库价" dense>
    <div class="meat-list">
      <div class="meat-list__track">
        <div v-for="(row, index) in [...data, ...data]" :key="`${row.name}-${index}`" class="meat-list__row">
          <span class="meat-list__rank">{{ (index % data.length) + 1 }}</span>
          <span class="meat-list__name">{{ row.name }}</span>
          <span>{{ row.market }}</span>
          <strong>{{ Number(row.price || 0).toFixed(1) }}元/斤</strong>
          <span :class="Number(row.change || 0) >= 0 ? 'meat-up' : 'meat-down'">{{ Number(row.change || 0) >= 0 ? '+' : '' }}{{ Number(row.change || 0).toFixed(1) }}%</span>
        </div>
      </div>
    </div>
  </ScreenPanel>
</template>

<style scoped>
.meat-list {
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.meat-list__track {
  animation: meatScroll 14s linear infinite;
}

.meat-list__row {
  display: grid;
  grid-template-columns: 28px 1fr 1fr 78px 58px;
  align-items: center;
  gap: 8px;
  min-height: 36px;
  border-bottom: 1px dashed rgba(74, 222, 128, 0.2);
  color: rgba(236, 253, 245, 0.84);
  font-size: 13px;
}

.meat-list__row span,
.meat-list__row strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meat-list__rank {
  display: inline-flex;
  width: 22px;
  height: 22px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(74, 222, 128, 0.32);
  color: #4ade80;
  font-size: 12px;
}

.meat-list__name { color: #ecfdf5; font-weight: 700; }
.meat-list__row strong { color: #fbbf24; }
.meat-up { color: #4ade80; }
.meat-down { color: #c4b5fd; }

@keyframes meatScroll {
  from { transform: translateY(0); }
  to { transform: translateY(-50%); }
}
</style>
