<script setup>
import { computed, ref, watch } from 'vue'
import ScreenPanel from './ScreenPanel.vue'
import { useScreenChart } from './useScreenChart'

const props = defineProps({
  data: { type: Array, required: true },
  optionHook: { type: Function, default: null }
})

const chartRef = ref(null)
const hookRef = computed(() => props.optionHook)
const formatPercent = (value) => `${Number(value || 0).toFixed(1)}%`

const buildOption = () => {
  const rows = props.data.slice(0, 8).reverse()
  return {
    animationDuration: 1200,
    animationEasing: 'cubicOut',
    grid: { left: 72, right: 28, top: 16, bottom: 20 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(1, 26, 19, 0.95)',
      borderColor: 'rgba(74, 222, 128, 0.35)',
      textStyle: { color: '#ecfdf5' }
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(209, 250, 229, 0.1)' } },
      axisLabel: { color: 'rgba(236, 253, 245, 0.62)' }
    },
    yAxis: {
      type: 'category',
      data: rows.map((item) => item.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: 'rgba(236, 253, 245, 0.78)', fontWeight: 700 }
    },
    series: [
      {
        type: 'bar',
        barWidth: 11,
        data: rows.map((item, index) => ({
          value: item.value,
          itemStyle: { color: index > 4 ? '#f59e0b' : index > 2 ? '#4ade80' : '#10b981', borderRadius: 8 }
        })),
        label: { show: true, position: 'right', color: '#ecfdf5', formatter: ({ value }) => formatPercent(value) },
        backgroundStyle: { color: 'rgba(255, 255, 255, 0.07)', borderRadius: 8 },
        showBackground: true
      }
    ]
  }
}

const { setOption } = useScreenChart(chartRef, buildOption, hookRef)
watch(() => props.data, () => setOption(), { deep: true })
defineExpose({ setOption })
</script>

<template>
  <ScreenPanel title="粮食类历史涨幅排名 TOP 8" subtitle="按已入库价格样本排序">
    <div ref="chartRef" class="grain-ranking" />
  </ScreenPanel>
</template>

<style scoped>
.grain-ranking {
  width: 100%;
  height: 100%;
}
</style>
