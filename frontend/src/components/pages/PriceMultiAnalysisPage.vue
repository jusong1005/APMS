<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { AlertTriangle, Lightbulb, MapPin, TrendingUp } from 'lucide-vue-next'
import Badge from '../ui/Badge.vue'
import { cityCoverageStats, defaultAreaPaths, marketTree } from '../../data/chinaMarkets'

echarts.use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const timeRanges = [
  { value: '7d', label: '近 7 天', days: 7 },
  { value: '30d', label: '近 30 天', days: 30 },
  { value: '90d', label: '近 90 天', days: 90 },
  { value: '180d', label: '近半年', days: 180 }
]

const categories = [
  { value: 'vegetable', label: '蔬菜', product: '大白菜', base: [2.2, 2.3, 2.35, 2.42, 2.48, 2.53, 2.61, 2.68] },
  { value: 'fruit', label: '水果', product: '苹果', base: [6.8, 6.72, 6.76, 6.84, 6.95, 7.08, 7.12, 7.2] },
  { value: 'livestock', label: '畜禽', product: '鸡蛋', base: [9.8, 9.92, 10.04, 10.16, 10.21, 10.28, 10.36, 10.44] }
]

const cascaderProps = { multiple: true, emitPath: true, checkStrictly: false }
const palette = ['#166534', '#bd7b18', '#0f766e', '#b91c1c', '#2563eb', '#7c3aed', '#0e7490', '#be123c', '#4d7c0f', '#c2410c']

const timeRange = ref('30d')
const category = ref('vegetable')
const selectedAreaPaths = ref(clonePaths(defaultAreaPaths))
const chartRef = ref(null)
let chartInstance
let resizeObserver

const marketLeafList = flattenMarkets(marketTree)
const marketMap = new Map(marketLeafList.map((item) => [item.value, item]))

const product = computed(() => categories.find((item) => item.value === category.value).product)
const activeCategory = computed(() => categories.find((item) => item.value === category.value))
const selectedMarkets = computed(() => selectedAreaPaths.value.map((path) => marketMap.get(path.at(-1))).filter(Boolean))
const activeMarkets = computed(() => selectedMarkets.value.length ? selectedMarkets.value : [marketLeafList[0]])
const visibleSelectedMarkets = computed(() => selectedMarkets.value.slice(0, 4))
const hiddenSelectedCount = computed(() => Math.max(0, selectedMarkets.value.length - visibleSelectedMarkets.value.length))

const series = computed(() => {
  const scale = timeRanges.find((item) => item.value === timeRange.value).days / 30
  return activeMarkets.value.map((market, index) => ({
    key: market.value,
    name: market.displayName,
    shortName: market.shortName,
    color: palette[index % palette.length],
    values: activeCategory.value.base.map((value, pointIndex) => roundPrice(value + market.offset + (scale - 1) * 0.03 * pointIndex))
  }))
})

const stats = computed(() => {
  const latestValues = series.value.map((item) => item.values.at(-1))
  const previousValues = series.value.map((item) => item.values.at(-2))
  const currentAvg = average(latestValues)
  const previousAvg = average(previousValues)
  return {
    highest: Math.max(...latestValues),
    lowest: Math.min(...latestValues),
    average: currentAvg,
    change: previousAvg ? ((currentAvg - previousAvg) / previousAvg) * 100 : 0,
    leader: series.value.reduce((top, item) => {
      const latest = item.values.at(-1)
      return latest > top.value ? { region: item.shortName, value: latest } : top
    }, { region: '', value: -Infinity })
  }
})

const avgOffset = computed(() => ((stats.value.average - stats.value.lowest) / (stats.value.highest - stats.value.lowest || 1)) * 100)
const changeLabel = computed(() => `${stats.value.change >= 0 ? '上涨' : '下降'}${Math.abs(stats.value.change).toFixed(1)}%`)
const chartOption = computed(() => buildChartOption(series.value))
const briefings = computed(() => [
  { icon: TrendingUp, title: '本周价格简报', text: `${product.value} 较上周环比${changeLabel.value}，均价为 ${stats.value.average.toFixed(2)} 元/公斤。`, toneClass: 'bg-forest-50 text-forest-700 border-forest-100' },
  { icon: MapPin, title: '区域分化', text: `${stats.value.leader.region} 当前价格最高，覆盖具体市场 ${activeMarkets.value.length} 个。`, toneClass: 'bg-amber-50 text-amber-700 border-amber-100' },
  { icon: AlertTriangle, title: '波动提示', text: stats.value.change > 4 ? '涨幅超过常规观察线，建议进入价格预警中心跟踪。' : '价格处于正常波动区间，可保持常规监控。', toneClass: stats.value.change > 4 ? 'bg-red-50 text-red-700 border-red-100' : 'bg-forest-50 text-forest-700 border-forest-100' },
  { icon: Lightbulb, title: '运营建议', text: '建议结合采集任务成功率和气象影响数据判断短期供应压力。', toneClass: 'bg-slate-100 text-slate-600 border-slate-200' }
])

function flattenMarkets(tree) {
  const leaves = []
  tree.forEach((province) => {
    province.children.forEach((city) => {
      city.children.forEach((market) => {
        leaves.push({
          ...market,
          province: province.label,
          city: city.label,
          displayName: `${province.label} / ${city.label} / ${market.label}`,
          shortName: market.label
        })
      })
    })
  })
  return leaves
}

function removeSelectedMarket(value) {
  if (selectedAreaPaths.value.length <= 1) return
  selectedAreaPaths.value = selectedAreaPaths.value.filter((path) => path.at(-1) !== value)
}

function resetAreaSelection() {
  selectedAreaPaths.value = clonePaths(defaultAreaPaths)
}

function clonePaths(paths) {
  return paths.map((path) => [...path])
}

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
  const resize = () => chartInstance?.resize()
  window.addEventListener('resize', resize)
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(chartRef.value)
  chartInstance.__resizeHandler = resize
  window.setTimeout(resize, 0)
}

function updateChart() {
  chartInstance?.setOption(chartOption.value, true)
}

watch(chartOption, () => nextTick(updateChart))
watch(selectedAreaPaths, (paths) => {
  if (!paths.length) resetAreaSelection()
})

onMounted(() => nextTick(initChart))
onUnmounted(() => {
  if (chartInstance?.__resizeHandler) window.removeEventListener('resize', chartInstance.__resizeHandler)
  resizeObserver?.disconnect()
  chartInstance?.dispose()
})

function buildChartOption(inputSeries) {
  return {
    color: inputSeries.map((item) => item.color),
    grid: { left: 52, right: 36, top: 76, bottom: 46 },
    legend: {
      type: 'scroll',
      top: 14,
      left: 18,
      right: 18,
      itemWidth: 12,
      itemHeight: 8,
      pageIconColor: '#064e3b',
      pageIconInactiveColor: '#cbd5e1',
      pageTextStyle: { color: '#64748b' },
      textStyle: { color: '#475569', fontSize: 12 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line' },
      valueFormatter: (value) => `${Number(value).toFixed(2)} 元/公斤`
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: Array.from({ length: 8 }, (_, index) => `W${index + 1}`),
      axisLabel: { color: '#64748b' },
      axisLine: { lineStyle: { color: '#cbd5e1' } }
    },
    yAxis: {
      type: 'value',
      name: '元/公斤',
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } }
    },
    series: inputSeries.map((item) => ({
      name: item.name,
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: item.values,
      lineStyle: { width: 3 },
      emphasis: { focus: 'series' }
    }))
  }
}

function average(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

function roundPrice(value) {
  return Math.round(value * 100) / 100
}
</script>

<template>
  <div class="space-y-4">
    <section class="rounded-lg border bg-white p-4 shadow-panel">
      <div class="flex flex-col gap-4 2xl:flex-row 2xl:items-start 2xl:justify-between">
        <div class="max-w-xl">
          <h2 class="text-base font-semibold text-slate-950">多维筛选器</h2>
          <div class="mt-1 flex flex-wrap items-center gap-2 text-sm leading-6 text-slate-500">
            <span>按时间跨度、产品品类和省份 / 城市 / 批发市场三级地区维度组合分析价格走势。</span>
            <Badge variant="outline">全国城市</Badge>
            <span>覆盖 {{ cityCoverageStats.provinces }} 个省级地区、{{ cityCoverageStats.cities }} 个城市。</span>
          </div>
        </div>
        <div class="grid gap-3 lg:grid-cols-[150px_250px_minmax(340px,520px)] 2xl:min-w-[940px]">
          <el-select v-model="timeRange" class="w-full" aria-label="时间跨度">
            <el-option v-for="range in timeRanges" :key="range.value" :label="range.label" :value="range.value" />
          </el-select>
          <div class="grid rounded-md border bg-slate-50 p-1 sm:grid-cols-3">
            <button v-for="item in categories" :key="item.value" :class="['h-8 rounded-sm px-3 text-sm font-medium transition-colors', category === item.value ? 'bg-white text-forest-800 shadow-sm' : 'text-slate-500 hover:text-slate-900']" @click="category = item.value">
              {{ item.label }}
            </button>
          </div>
          <el-cascader
            v-model="selectedAreaPaths"
            :options="marketTree"
            :props="cascaderProps"
            filterable
            clearable
            collapse-tags
            collapse-tags-tooltip
            :show-all-levels="true"
            class="w-full"
            placeholder="搜索并选择省份 / 城市 / 批发市场"
          />
        </div>
      </div>
      <div class="mt-4 rounded-lg border border-slate-100 bg-slate-50 px-3 py-3">
        <div class="mb-2 flex items-center justify-between gap-3">
          <span class="text-xs font-semibold text-slate-500">已选地区市场</span>
          <button class="text-xs font-medium text-[#064e3b] hover:underline" @click="resetAreaSelection">恢复默认</button>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <el-tag
            v-for="market in visibleSelectedMarkets"
            :key="market.value"
            closable
            effect="plain"
            class="selected-market-tag"
            @close="removeSelectedMarket(market.value)"
          >
            {{ market.province }} / {{ market.city }} / {{ market.label }}
          </el-tag>
          <span v-if="hiddenSelectedCount" class="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-500">+{{ hiddenSelectedCount }} 更多</span>
          <span v-if="!selectedMarkets.length" class="text-xs text-slate-400">请选择至少一个批发市场</span>
        </div>
      </div>
    </section>

    <div class="grid gap-4 xl:grid-cols-[2fr_1fr]">
      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="text-base font-semibold text-slate-950">{{ product }} 多市场价格走势</h2>
              <Badge variant="outline">ECharts</Badge>
              <Badge>滚动图例</Badge>
            </div>
            <p class="mt-1 text-sm text-slate-500">图例已启用 scroll 模式，支持多个省市市场同时对比而不遮挡图表。</p>
          </div>
          <div class="text-xs leading-5 text-slate-500">当前选中 {{ activeMarkets.length }} 个具体市场</div>
        </div>
        <div ref="chartRef" role="img" aria-label="多地区价格走势折线图" class="w-full rounded-lg border bg-slate-50" style="height: 380px" />
      </section>

      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-base font-semibold text-slate-950">价格梯度图</h2>
            <Badge>当前市场</Badge>
          </div>
          <p class="mt-1 text-sm text-slate-500">展示最高价、均价和最低价分布。</p>
        </div>
        <div class="space-y-5">
          <div class="rounded-lg border bg-slate-50 p-4">
            <div class="mb-3 flex items-center justify-between text-sm">
              <span class="text-slate-500">品种</span>
              <span class="font-medium text-slate-950">{{ product }}</span>
            </div>
            <div class="relative h-64 rounded-lg border bg-white p-5">
              <div class="absolute left-1/2 top-6 h-52 w-8 -translate-x-1/2 rounded-full bg-gradient-to-t from-forest-600 via-harvest-400 to-red-500 shadow-inner" />
              <div class="absolute left-[calc(50%+34px)] flex items-center gap-2" style="top: 9%"><span class="h-px w-9 bg-slate-300" /><span class="rounded-md border border-red-200 bg-red-50 px-2 py-1 text-xs font-medium text-red-700">最高价 {{ stats.highest.toFixed(2) }}</span></div>
              <div class="absolute left-[calc(50%+34px)] flex items-center gap-2" :style="{ top: `${100 - avgOffset}%` }"><span class="h-px w-9 bg-slate-300" /><span class="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">均价 {{ stats.average.toFixed(2) }}</span></div>
              <div class="absolute left-[calc(50%+34px)] flex items-center gap-2" style="top: 78%"><span class="h-px w-9 bg-slate-300" /><span class="rounded-md border border-forest-100 bg-forest-50 px-2 py-1 text-xs font-medium text-forest-700">最低价 {{ stats.lowest.toFixed(2) }}</span></div>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-2">
            <div v-for="item in [{ label: '最高', value: stats.highest }, { label: '均价', value: stats.average }, { label: '最低', value: stats.lowest }]" :key="item.label" class="rounded-lg border bg-white p-3 text-center">
              <p class="text-xs text-slate-500">{{ item.label }}</p>
              <p class="mt-1 text-sm font-semibold text-slate-950">{{ item.value.toFixed(2) }}</p>
            </div>
          </div>
        </div>
      </section>
    </div>

    <section class="rounded-lg border bg-white p-5 shadow-panel">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 class="text-base font-semibold text-slate-950">数据洞察区</h2>
          <p class="mt-1 text-sm text-slate-500">根据筛选结果自动生成本周价格简报。</p>
        </div>
        <Badge variant="outline">自动生成</Badge>
      </div>
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div v-for="item in briefings" :key="item.title" class="rounded-lg border bg-slate-50 p-4">
          <div class="flex items-center gap-2">
            <span :class="['flex h-8 w-8 items-center justify-center rounded-lg border', item.toneClass]"><component :is="item.icon" class="h-4 w-4" /></span>
            <h3 class="text-sm font-semibold text-slate-950">{{ item.title }}</h3>
          </div>
          <p class="mt-3 text-sm leading-6 text-slate-600">{{ item.text }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.selected-market-tag {
  max-width: 360px;
  border-color: #d1fae5;
  color: #064e3b;
}
</style>