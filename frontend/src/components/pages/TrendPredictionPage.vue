<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, MarkLineComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { AlertTriangle, BrainCircuit, CloudSun, Route, Sparkles, TrendingUp } from 'lucide-vue-next'
import Badge from '../ui/Badge.vue'

echarts.use([LineChart, BarChart, GridComponent, MarkLineComponent, TooltipComponent, CanvasRenderer])

const models = [
  { key: 'timeSeries', label: '时间序列模型', summary: '捕捉历史价格周期与短期波动，适合连续交易日趋势外推。', threshold: 3.18, forecastBase: [2.88, 2.9, 2.93, 2.96, 2.99, 3.01, 3.04, 3.06, 3.08, 3.1, 3.12, 3.14, 3.15, 3.17, 3.19, 3.2, 3.22, 3.23, 3.24, 3.25, 3.27, 3.28, 3.29, 3.3, 3.32, 3.33, 3.34, 3.35, 3.36, 3.38], weights: [32, 21, 16, 13, 10, 8] },
  { key: 'randomForest', label: '随机森林模型', summary: '融合多源特征判断非线性影响，适合解释关键因子贡献。', threshold: 3.24, forecastBase: [2.88, 2.91, 2.94, 2.95, 2.97, 3.0, 3.02, 3.03, 3.05, 3.08, 3.1, 3.11, 3.12, 3.14, 3.16, 3.17, 3.18, 3.19, 3.21, 3.22, 3.23, 3.24, 3.25, 3.26, 3.27, 3.28, 3.29, 3.3, 3.31, 3.32], weights: [24, 28, 18, 15, 9, 6] },
  { key: 'deepLearning', label: '深度学习模型', summary: '识别多变量长期关联，适合高维气象与市场信号联合预测。', threshold: 3.3, forecastBase: [2.88, 2.9, 2.94, 2.98, 3.01, 3.05, 3.08, 3.11, 3.14, 3.18, 3.2, 3.23, 3.26, 3.28, 3.31, 3.33, 3.36, 3.38, 3.41, 3.43, 3.45, 3.48, 3.5, 3.52, 3.55, 3.57, 3.59, 3.61, 3.64, 3.66], weights: [19, 24, 21, 17, 11, 8] }
]

const factorLabels = ['季节因素', '气象灾害', '运输成本', '市场供需', '节假日需求', '采集质量']
const factorIcons = [CloudSun, AlertTriangle, Route, TrendingUp, Sparkles, BrainCircuit]
const historyPrices = [2.54, 2.56, 2.58, 2.57, 2.6, 2.62, 2.64, 2.67, 2.66, 2.69, 2.71, 2.73, 2.72, 2.75, 2.77, 2.78, 2.8, 2.79, 2.82, 2.83, 2.85, 2.84, 2.86, 2.87]

const activeModelKey = ref('timeSeries')
const predictionChartRef = ref(null)
const factorChartRef = ref(null)
let predictionChart
let factorChart
let resizeObserver

const activeModel = computed(() => models.find((model) => model.key === activeModelKey.value))
const chartData = computed(() => buildPredictionData(activeModel.value))
const factorData = computed(() => buildFactorData(activeModel.value.weights))
const forecastMax = computed(() => Math.max(...activeModel.value.forecastBase))
const isWarning = computed(() => forecastMax.value > activeModel.value.threshold)
const peakDay = computed(() => activeModel.value.forecastBase.findIndex((price) => price === forecastMax.value) + 1)
const predictionOption = computed(() => buildPredictionOption(chartData.value, activeModel.value.threshold))
const factorOption = computed(() => buildFactorOption(factorData.value))

function initCharts() {
  if (!predictionChartRef.value || !factorChartRef.value) return
  predictionChart = echarts.init(predictionChartRef.value)
  factorChart = echarts.init(factorChartRef.value)
  updateCharts()
  const resize = () => {
    predictionChart?.resize()
    factorChart?.resize()
  }
  window.addEventListener('resize', resize)
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(predictionChartRef.value)
  resizeObserver.observe(factorChartRef.value)
  predictionChart.__resizeHandler = resize
}

function updateCharts() {
  predictionChart?.setOption(predictionOption.value, true)
  factorChart?.setOption(factorOption.value, true)
}

watch([predictionOption, factorOption], () => nextTick(updateCharts))

onMounted(() => nextTick(initCharts))
onUnmounted(() => {
  if (predictionChart?.__resizeHandler) window.removeEventListener('resize', predictionChart.__resizeHandler)
  resizeObserver?.disconnect()
  predictionChart?.dispose()
  factorChart?.dispose()
})

function buildPredictionData(model) {
  const historyLabels = Array.from({ length: historyPrices.length }, (_, index) => `历史${index + 1}`)
  const forecastLabels = Array.from({ length: 30 }, (_, index) => `未来${index + 1}`)
  const forecastStart = historyPrices.length - 1
  return {
    labels: [...historyLabels, ...forecastLabels],
    historyLine: [...historyPrices, ...Array(30).fill(null)],
    forecastLine: [...Array(forecastStart).fill(null), historyPrices.at(-1), ...model.forecastBase],
    bandLower: [...Array(forecastStart).fill(null), historyPrices.at(-1) - 0.08, ...model.forecastBase.map((price, index) => roundPrice(price - 0.1 - index * 0.006))],
    bandWidth: [...Array(forecastStart).fill(null), 0.16, ...model.forecastBase.map((_, index) => roundPrice(0.22 + index * 0.012))]
  }
}

function buildPredictionOption(data, threshold) {
  return {
    color: ['#166534', '#bd7b18', '#22c55e'],
    grid: { left: 46, right: 28, top: 36, bottom: 44 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'line' }, valueFormatter: (value) => (typeof value === 'number' ? `${value.toFixed(2)} 元/公斤` : value) },
    xAxis: { type: 'category', boundaryGap: false, data: data.labels, axisLabel: { color: '#64748b', interval: 5 }, axisLine: { lineStyle: { color: '#cbd5e1' } } },
    yAxis: { type: 'value', name: '元/公斤', min: 2.4, max: 3.9, axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } } },
    series: [
      { name: '区间下界', type: 'line', stack: 'confidence-band', data: data.bandLower, symbol: 'none', lineStyle: { opacity: 0 }, tooltip: { show: false }, emphasis: { disabled: true } },
      { name: '波动区间', type: 'line', stack: 'confidence-band', data: data.bandWidth, symbol: 'none', lineStyle: { opacity: 0 }, areaStyle: { color: 'rgba(34, 197, 94, 0.18)' }, tooltip: { show: false }, emphasis: { disabled: true } },
      { name: '历史数据', type: 'line', data: data.historyLine, smooth: true, showSymbol: false, lineStyle: { width: 3, color: '#166534' } },
      { name: '预测数据', type: 'line', data: data.forecastLine, smooth: true, showSymbol: false, lineStyle: { width: 3, color: '#bd7b18', type: 'dashed' }, markLine: { symbol: 'none', label: { formatter: `预警阈值 ${threshold.toFixed(2)}`, color: '#b91c1c' }, lineStyle: { color: '#ef4444', type: 'dashed' }, data: [{ yAxis: threshold }] } }
    ]
  }
}

function buildFactorData(weights) {
  return factorLabels.map((name, index) => ({ name, value: weights[index] })).sort((first, second) => first.value - second.value)
}

function buildFactorOption(data) {
  return {
    grid: { left: 82, right: 28, top: 16, bottom: 24 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (value) => `${value}%` },
    xAxis: { type: 'value', max: 36, axisLabel: { color: '#64748b', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } } },
    yAxis: { type: 'category', data: data.map((item) => item.name), axisLabel: { color: '#475569' }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{ name: '权重', type: 'bar', data: data.map((item) => item.value), barWidth: 18, itemStyle: { borderRadius: [0, 6, 6, 0], color: '#166534' }, label: { show: true, position: 'right', color: '#0f172a', formatter: '{c}%' } }]
  }
}

function roundPrice(value) {
  return Math.round(value * 100) / 100
}
</script>

<template>
  <div class="space-y-4">
    <section class="rounded-lg border bg-white p-4 shadow-panel">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h2 class="text-base font-semibold text-slate-950">预测模型选择</h2>
          <p class="mt-1 text-sm leading-6 text-slate-500">{{ activeModel.summary }}</p>
        </div>
        <div class="grid rounded-md border bg-slate-50 p-1 sm:grid-cols-3">
          <button v-for="model in models" :key="model.key" :class="['h-9 rounded-sm px-3 text-sm font-medium transition-colors', activeModelKey === model.key ? 'bg-white text-forest-800 shadow-sm' : 'text-slate-500 hover:text-slate-900']" @click="activeModelKey = model.key">
            {{ model.label }}
          </button>
        </div>
      </div>
    </section>

    <section :class="['rounded-lg border p-4 shadow-panel', isWarning ? 'border-red-200 bg-red-50' : 'border-forest-100 bg-forest-50']">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div class="flex items-start gap-3">
          <span :class="['flex h-11 w-11 items-center justify-center rounded-lg border bg-white', isWarning ? 'border-red-200 text-red-600' : 'border-forest-100 text-forest-700']">
            <AlertTriangle class="h-5 w-5" />
          </span>
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h2 :class="['text-base font-semibold', isWarning ? 'text-red-900' : 'text-forest-900']">{{ isWarning ? '预测价格超过预警阈值' : '预测价格处于安全区间' }}</h2>
              <Badge :variant="isWarning ? 'danger' : 'default'">{{ isWarning ? '高风险' : '正常' }}</Badge>
            </div>
            <p :class="['mt-1 text-sm leading-6', isWarning ? 'text-red-700' : 'text-forest-700']">
              未来 30 天最高预测价 {{ forecastMax.toFixed(2) }} 元/公斤，阈值 {{ activeModel.threshold.toFixed(2) }} 元/公斤，预计第 {{ peakDay }} 天达到峰值。
            </p>
          </div>
        </div>
        <div class="grid grid-cols-3 gap-2 text-center sm:min-w-[360px]">
          <div v-for="item in [{ label: '历史末值', value: historyPrices.at(-1) }, { label: '预测峰值', value: forecastMax, danger: isWarning }, { label: '阈值', value: activeModel.threshold }]" :key="item.label" class="rounded-lg border bg-white px-3 py-2">
            <p class="text-xs text-slate-500">{{ item.label }}</p>
            <p :class="['mt-1 text-base font-semibold', item.danger ? 'text-red-700' : 'text-slate-950']">{{ item.value.toFixed(2) }}</p>
          </div>
        </div>
      </div>
    </section>

    <div class="grid gap-4 xl:grid-cols-[1.6fr_0.9fr]">
      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="text-base font-semibold text-slate-950">置信区间预测图</h2>
              <Badge variant="outline">ECharts</Badge>
            </div>
            <p class="mt-1 text-sm text-slate-500">历史价格使用实线，未来 30 天预测使用虚线，浅色阴影表示波动区间。</p>
          </div>
          <div class="flex flex-wrap gap-2 text-xs text-slate-500">
            <span class="inline-flex items-center gap-2"><span class="h-0 w-8 border-t-2 border-[#166534]" />历史数据</span>
            <span class="inline-flex items-center gap-2"><span class="h-0 w-8 border-t-2 border-dashed border-[#bd7b18]" />预测数据</span>
            <span class="inline-flex items-center gap-2"><span class="h-0 w-8 border-t-2 border-[rgba(34,197,94,0.28)]" />波动区间</span>
          </div>
        </div>
        <div ref="predictionChartRef" role="img" aria-label="置信区间预测图" class="h-[430px] w-full rounded-lg border bg-slate-50" />
      </section>

      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-base font-semibold text-slate-950">预测因子分析</h2>
            <Badge>影响因素权重</Badge>
          </div>
          <p class="mt-1 text-sm text-slate-500">横向柱状图展示不同因素对预测结果的贡献。</p>
        </div>
        <div ref="factorChartRef" role="img" aria-label="影响因素权重横向柱状图" class="h-[318px] w-full rounded-lg border bg-slate-50" />
        <div class="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
          <div v-for="(factor, index) in factorData.slice(0, 4)" :key="factor.name" class="flex items-center justify-between rounded-lg border bg-slate-50 px-3 py-2">
            <div class="flex items-center gap-2">
              <span class="flex h-8 w-8 items-center justify-center rounded-lg border bg-white text-forest-700"><component :is="factorIcons[index]" class="h-4 w-4" /></span>
              <span class="text-sm font-medium text-slate-800">{{ factor.name }}</span>
            </div>
            <span class="text-sm font-semibold text-slate-950">{{ factor.value }}%</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>