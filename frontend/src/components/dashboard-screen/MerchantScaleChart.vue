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

const buildOption = () => ({
  animationDuration: 1200,
  animationEasing: 'cubicOut',
  color: ['#10b981', '#f59e0b'],
  grid: { left: 40, right: 18, top: 28, bottom: 30 },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(1, 26, 19, 0.95)',
    borderColor: 'rgba(74, 222, 128, 0.35)',
    textStyle: { color: '#ecfdf5' }
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: props.data.map((item) => item.range),
    axisLine: { lineStyle: { color: 'rgba(209, 250, 229, 0.24)' } },
    axisTick: { show: false },
    axisLabel: { color: 'rgba(236, 253, 245, 0.65)', fontSize: 11 }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'rgba(209, 250, 229, 0.1)' } },
    axisLabel: { color: 'rgba(236, 253, 245, 0.65)' }
  },
  series: [
    {
      name: '批发商户',
      type: 'line',
      smooth: true,
      symbolSize: 6,
      lineStyle: { width: 3, color: '#10b981' },
      areaStyle: { color: 'rgba(16, 185, 129, 0.28)' },
      data: props.data.map((item) => item.wholesale)
    },
    {
      name: '零售商户',
      type: 'line',
      smooth: true,
      symbolSize: 6,
      lineStyle: { width: 2, color: '#f59e0b' },
      areaStyle: { color: 'rgba(245, 158, 11, 0.22)' },
      data: props.data.map((item) => item.retail)
    }
  ]
})

const { setOption } = useScreenChart(chartRef, buildOption, hookRef)
watch(() => props.data, () => setOption(), { deep: true })
defineExpose({ setOption })
</script>

<template>
  <ScreenPanel title="市场商户规模分析" subtitle="批发与零售市场规模波形对照">
    <div ref="chartRef" class="merchant-scale" />
  </ScreenPanel>
</template>

<style scoped>
.merchant-scale {
  width: 100%;
  height: 100%;
}
</style>
