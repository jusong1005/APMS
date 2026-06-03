<script setup>
import MiniRingChart from './MiniRingChart.vue'
import ScreenPanel from './ScreenPanel.vue'

defineProps({
  data: { type: Array, required: true },
  optionHook: { type: Function, default: null }
})
</script>

<template>
  <ScreenPanel title="农产品总览" subtitle="MongoDB 累计入库分类指标">
    <div class="category-rings">
      <MiniRingChart v-for="item in data" :key="item.label" :item="item" :option-hook="optionHook" />
    </div>
  </ScreenPanel>
</template>

<style scoped>
.category-rings {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: center;
  height: 100%;
  gap: 8px;
}
</style>
