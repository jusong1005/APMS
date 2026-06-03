<script setup>
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  suffix: { type: String, default: '' },
  decimals: { type: Number, default: 0 }
})

const displayed = ref(0)
let frameId = 0

const formatted = computed(() => {
  const value = Number(displayed.value || 0)
  return `${value.toLocaleString('zh-CN', {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals
  })}${props.suffix}`
})

const animateTo = (target) => {
  window.cancelAnimationFrame(frameId)
  if (document.hidden) {
    displayed.value = target
    return
  }
  const start = displayed.value
  const distance = target - start
  const startTime = performance.now()
  const duration = 760

  const tick = (time) => {
    const progress = Math.min(1, (time - startTime) / duration)
    const eased = 1 - Math.pow(1 - progress, 3)
    displayed.value = start + distance * eased
    if (progress < 1) frameId = window.requestAnimationFrame(tick)
  }
  frameId = window.requestAnimationFrame(tick)
}

watch(() => props.value, (value) => animateTo(Number(value || 0)))

onMounted(() => animateTo(Number(props.value || 0)))
</script>

<template>
  <span class="animated-number">{{ formatted }}</span>
</template>

<style scoped>
.animated-number {
  display: inline-block;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  text-shadow: 0 0 18px rgba(74, 222, 128, 0.42);
}
</style>
