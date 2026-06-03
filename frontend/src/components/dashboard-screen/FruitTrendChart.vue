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
const formatAxisLabel = (value) => String(value || '').replace(/^(?:\d{4}-)?(\d{2}-\d{2})T.*$/, '$1')

const buildOption = () => ({
  animationDuration: 1200,
  animationEasing: 'cubicOut',
  color: ['#10b981', '#c4b5fd'],
  grid: { left: 42, right: 42, top: 36, bottom: 32 },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(1, 26, 19, 0.95)',
    borderColor: 'rgba(74, 222, 128, 0.35)',
    textStyle: { color: '#ecfdf5' }
  },
  legend: { top: 0, textStyle: { color: 'rgba(236, 253, 245, 0.7)' } },
  xAxis: {
    type: 'category',
    data: props.data.map((item) => item.label),
    axisLine: { lineStyle: { color: 'rgba(209, 250, 229, 0.25)' } },
    axisTick: { show: false },
    axisLabel: { color: 'rgba(236, 253, 245, 0.7)', formatter: formatAxisLabel }
  },
  yAxis: [
    {
      type: 'value',
      name: '价格',
      nameTextStyle: { color: 'rgba(236, 253, 245, 0.65)' },
      splitLine: { lineStyle: { color: 'rgba(209, 250, 229, 0.1)' } },
      axisLabel: { color: 'rgba(236, 253, 245, 0.68)' }
    },
    {
      type: 'value',
      name: '关注度',
      nameTextStyle: { color: 'rgba(196, 181, 253, 0.9)' },
      splitLine: { show: false },
      axisLabel: { color: 'rgba(196, 181, 253, 0.82)' }
    }
  ],
  series: [
    {
      name: '水果均价',
      type: 'bar',
      barWidth: 16,
      itemStyle: { borderRadius: [5, 5, 0, 0], color: '#10b981' },
      data: props.data.map((item) => item.price)
    },
    {
      name: '关注度',
      type: 'line',
      yAxisIndex: 1,
      smooth: true,
      symbolSize: 8,
      lineStyle: { width: 3, color: '#c4b5fd' },
      itemStyle: { color: '#f0abfc', shadowBlur: 12, shadowColor: '#f0abfc' },
      data: props.data.map((item) => item.attention)
    }
  ]
})

const { setOption } = useScreenChart(chartRef, buildOption, hookRef)
watch(() => props.data, () => setOption(), { deep: true })
defineExpose({ setOption })
</script>

<template>
  <ScreenPanel title="水果类价格分析及关注度走势" subtitle="价格柱状与关注度折线混合分析">
    <div ref="chartRef" class="fruit-trend" />
  </ScreenPanel>
</template>

<style scoped>
.fruit-trend {
  width: 100%;
  height: 100%;
}
</style>
