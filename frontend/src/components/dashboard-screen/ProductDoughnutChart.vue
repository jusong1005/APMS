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
  color: props.data.map((item) => item.color),
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(1, 26, 19, 0.94)',
    borderColor: 'rgba(74, 222, 128, 0.35)',
    textStyle: { color: '#ecfdf5' }
  },
  series: [
    {
      type: 'pie',
      radius: ['50%', '72%'],
      center: ['50%', '52%'],
      avoidLabelOverlap: true,
      label: {
        color: '#d1fae5',
        fontSize: 12,
        formatter: '{b}\n{d}%'
      },
      labelLine: { lineStyle: { color: 'rgba(209, 250, 229, 0.34)' } },
      itemStyle: { borderColor: '#042f24', borderWidth: 3 },
      data: props.data.map((item) => ({ name: item.name, value: item.value }))
    }
  ],
  graphic: [
    {
      type: 'text',
      left: 'center',
      top: '45%',
      style: { text: props.data.reduce((sum, item) => sum + Number(item.value || 0), 0).toLocaleString('zh-CN'), fill: '#ecfdf5', fontSize: 26, fontWeight: 800, textAlign: 'center' }
    },
    {
      type: 'text',
      left: 'center',
      top: '55%',
      style: { text: '总数', fill: 'rgba(209, 250, 229, 0.56)', fontSize: 12, textAlign: 'center' }
    }
  ]
})

const { setOption } = useScreenChart(chartRef, buildOption, hookRef)
watch(() => props.data, () => setOption(), { deep: true })
defineExpose({ setOption })
</script>

<template>
  <ScreenPanel title="产品类型" subtitle="种植业、渔业、畜牧业构成比例">
    <div ref="chartRef" class="doughnut-chart" />
  </ScreenPanel>
</template>

<style scoped>
.doughnut-chart {
  width: 100%;
  height: 100%;
}
</style>
