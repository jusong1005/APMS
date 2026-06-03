<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { registerMap } from 'echarts/core'
import ScreenPanel from './ScreenPanel.vue'
import { useScreenChart } from './useScreenChart'

const props = defineProps({
  data: { type: Array, required: true },
  optionHook: { type: Function, default: null }
})

const CHINA_GEOJSON_URL = 'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json'
const fallbackChinaGeoJson = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: '中国' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [73.5, 39.5], [76.8, 43.8], [82.4, 48.8], [90.5, 47.7], [96.8, 49.2], [103.5, 45.7], [111.2, 47.9], [119.5, 52.0], [127.4, 49.6], [134.2, 47.4], [130.6, 42.3], [124.3, 39.4], [122.2, 35.0], [119.4, 31.1], [121.8, 25.1], [116.2, 22.7], [110.3, 20.1], [105.2, 21.9], [100.0, 24.5], [96.0, 28.3], [91.2, 29.1], [86.4, 27.6], [81.6, 31.2], [78.2, 34.8], [73.5, 39.5]
        ]]
      }
    }
  ]
}

registerMap('agriChina', fallbackChinaGeoJson)

const chartRef = ref(null)
const hookRef = computed(() => props.optionHook)

const buildOption = () => ({
  animationDuration: 1300,
  animationEasing: 'cubicOut',
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(1, 26, 19, 0.95)',
    borderColor: 'rgba(74, 222, 128, 0.4)',
    textStyle: { color: '#ecfdf5' },
    formatter: (params) => params.data?.name ? `${params.data.name}<br/>市场数：${params.data.value?.[2] || params.data.value || 0}` : '中国市场分布'
  },
  geo: {
    map: 'agriChina',
    left: 24,
    right: 24,
    top: 8,
    bottom: 8,
    roam: false,
    aspectScale: 0.85,
    itemStyle: {
      areaColor: 'rgba(16, 185, 129, 0.13)',
      borderColor: 'rgba(74, 222, 128, 0.75)',
      borderWidth: 1.3,
      shadowBlur: 24,
      shadowColor: 'rgba(16, 185, 129, 0.25)'
    },
    emphasis: {
      itemStyle: { areaColor: 'rgba(74, 222, 128, 0.24)' },
      label: { show: false }
    },
    label: { show: false }
  },
  series: [
    {
      type: 'effectScatter',
      coordinateSystem: 'geo',
      rippleEffect: { brushType: 'stroke', period: 4, scale: 4 },
      symbolSize: (value) => Math.max(9, Math.min(26, Number(value[2] || 0) / 7)),
      itemStyle: { color: '#4ade80', shadowBlur: 18, shadowColor: '#4ade80' },
      label: { show: true, formatter: '{b}', color: '#ecfdf5', fontSize: 12, position: 'right' },
      data: props.data.map((item) => ({ name: item.name, value: [item.lng, item.lat, item.count] }))
    }
  ]
})

const { setOption } = useScreenChart(chartRef, buildOption, hookRef)
watch(() => props.data, () => setOption(), { deep: true })
onMounted(async () => {
  try {
    const response = await fetch(CHINA_GEOJSON_URL)
    if (!response.ok) return
    registerMap('agriChina', await response.json())
    setOption()
  } catch {
    setOption()
  }
})
defineExpose({ setOption })
</script>

<template>
  <ScreenPanel title="各地区市场数量分布" subtitle="全国重点监测省份与批发市场点位">
    <div ref="chartRef" class="china-map" />
  </ScreenPanel>
</template>

<style scoped>
.china-map {
  width: 100%;
  height: 100%;
}
</style>
