<script setup>
import { computed, ref, watch } from 'vue'
import AnimatedNumber from './AnimatedNumber.vue'
import { useScreenChart } from './useScreenChart'

const props = defineProps({
  item: { type: Object, required: true },
  optionHook: { type: Function, default: null }
})

const chartRef = ref(null)
const hookRef = computed(() => props.optionHook)

const buildOption = () => {
  const percent = Math.max(0, Math.min(100, Number(props.item.percent || 0)))
  return {
    animationDuration: 1000,
    animationEasing: 'cubicOut',
    series: [
      {
        type: 'pie',
        radius: ['72%', '86%'],
        center: ['50%', '50%'],
        startAngle: 92,
        clockwise: true,
        silent: true,
        label: { show: false },
        data: [
          { value: percent, itemStyle: { color: props.item.color || '#4ade80', shadowBlur: 16, shadowColor: props.item.color || '#4ade80' } },
          { value: 100 - percent, itemStyle: { color: 'rgba(209, 250, 229, 0.12)' } }
        ]
      },
      {
        type: 'pie',
        radius: ['58%', '60%'],
        silent: true,
        label: { show: false },
        data: [{ value: 1, itemStyle: { color: 'rgba(74, 222, 128, 0.22)' } }]
      }
    ]
  }
}

const { setOption } = useScreenChart(chartRef, buildOption, hookRef)
watch(() => props.item, () => setOption(), { deep: true })
defineExpose({ setOption })
</script>

<template>
  <div class="mini-ring">
    <div ref="chartRef" class="mini-ring__chart" />
    <div class="mini-ring__value">
      <AnimatedNumber :value="Number(item.value || 0)" />
      <span>{{ item.unit || '' }}</span>
    </div>
    <p>{{ item.label }}</p>
  </div>
</template>

<style scoped>
.mini-ring {
  position: relative;
  display: grid;
  justify-items: center;
  min-width: 0;
}

.mini-ring__chart {
  width: 96px;
  height: 96px;
}

.mini-ring__value {
  position: absolute;
  top: 35px;
  display: flex;
  align-items: baseline;
  gap: 2px;
  color: #ecfdf5;
  font-size: 20px;
  font-weight: 800;
}

.mini-ring__value span:last-child {
  color: rgba(209, 250, 229, 0.62);
  font-size: 11px;
}

.mini-ring p {
  margin: 4px 0 0;
  color: rgba(209, 250, 229, 0.78);
  font-size: 13px;
  font-weight: 700;
}
</style>
