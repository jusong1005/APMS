<script setup>
import AnimatedNumber from './AnimatedNumber.vue'
import ScreenPanel from './ScreenPanel.vue'

defineProps({
  title: { type: String, default: '蔬菜类最新入库报价' },
  data: { type: Array, required: true }
})
</script>

<template>
  <ScreenPanel :title="title" subtitle="优先展示 Redis 实时价，无缓存时展示最新入库价" dense>
    <div class="quote-list">
      <div class="quote-list__head">
        <span>品名</span>
        <span>地区</span>
        <span>单价</span>
        <span>波动</span>
      </div>
      <div class="quote-list__viewport">
        <div class="quote-list__track">
          <div v-for="(row, index) in [...data, ...data]" :key="`${row.name}-${index}`" class="quote-list__row">
            <span>{{ row.name }}</span>
            <span>{{ row.region }}</span>
            <span><AnimatedNumber :value="Number(row.price || 0)" :decimals="1" suffix="元/斤" /></span>
            <span :class="Number(row.change || 0) >= 0 ? 'quote-up' : 'quote-down'">{{ Number(row.change || 0) >= 0 ? '+' : '' }}{{ Number(row.change || 0).toFixed(1) }}%</span>
          </div>
        </div>
      </div>
    </div>
  </ScreenPanel>
</template>

<style scoped>
.quote-list {
  display: grid;
  grid-template-rows: 28px minmax(0, 1fr);
  height: 100%;
  min-height: 0;
}

.quote-list__head,
.quote-list__row {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr 1fr 0.7fr;
  align-items: center;
  gap: 8px;
}

.quote-list__head {
  border-bottom: 1px solid rgba(74, 222, 128, 0.18);
  color: rgba(209, 250, 229, 0.54);
  font-size: 12px;
}

.quote-list__viewport {
  min-height: 0;
  overflow: hidden;
}

.quote-list__track {
  animation: quoteScroll 16s linear infinite;
}

.quote-list__row {
  min-height: 34px;
  border-bottom: 1px dashed rgba(74, 222, 128, 0.2);
  color: rgba(236, 253, 245, 0.9);
  font-size: 13px;
}

.quote-list__row span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quote-up { color: #4ade80; }
.quote-down { color: #fbbf24; }

@keyframes quoteScroll {
  from { transform: translateY(0); }
  to { transform: translateY(-50%); }
}
</style>
