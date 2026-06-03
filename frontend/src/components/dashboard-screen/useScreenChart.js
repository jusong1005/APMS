import { nextTick, onMounted, onUnmounted, unref } from 'vue'
import { BarChart, EffectScatterChart, LineChart, MapChart, PieChart } from 'echarts/charts'
import { GeoComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

use([BarChart, CanvasRenderer, EffectScatterChart, GeoComponent, GridComponent, LegendComponent, LineChart, MapChart, PieChart, TooltipComponent])

export function useScreenChart(chartRef, buildOption, optionHook) {
  let chart = null

  const ensureChart = () => {
    if (!chartRef.value) return null
    if (!chart) chart = init(chartRef.value)
    return chart
  }

  const setOption = (nextOption) => {
    const instance = ensureChart()
    if (!instance) return
    const baseOption = nextOption || buildOption()
    const hook = unref(optionHook)
    instance.setOption(hook ? hook(baseOption, instance) || baseOption : baseOption, true)
  }

  const resize = () => chart?.resize()

  onMounted(async () => {
    await nextTick()
    setOption()
    window.addEventListener('resize', resize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', resize)
    chart?.dispose()
    chart = null
  })

  return { setOption, resize }
}
