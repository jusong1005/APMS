<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, MarkLineComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { ElMessage } from 'element-plus'
import { AlertTriangle, BrainCircuit, CloudSun, Route, Sparkles, TrendingUp } from 'lucide-vue-next'
import AiAdviceLines from '../ai/AiAdviceLines.vue'
import Badge from '../ui/Badge.vue'
import Button from '../ui/Button.vue'
import { aiApi, predictionApi } from '../../lib/api'
import { adviceTextClass, formatAdviceAccuracy, normalizeAccuracy, useAdviceGenerator } from '../../composables/useAdviceGenerator'

echarts.use([LineChart, BarChart, GridComponent, LegendComponent, MarkLineComponent, TooltipComponent, CanvasRenderer])

const emptyPredictionModel = {
  key: '',
  product: '',
  marketName: '',
  region: '',
  marketLabel: '暂无市场',
  segmentKey: '',
  trainingRecords: 0,
  modelName: '暂无预测模型',
  summary: '暂无可展示的预测数据。',
  threshold: 0,
  forecastBase: [],
  forecastLabels: [],
  historyPrices: [],
  historyLabels: [],
  backtestForecast: [],
  lowerBound: [],
  upperBound: [],
  weights: [],
  metrics: {},
  confidence: 0,
  riskLevel: 'unknown',
  routingReason: '等待预测结果同步'
}

const models = ref([])

const factorLabels = ['季节因素', '气象灾害', '运输成本', '市场供需', '节假日需求', '采集质量']
const factorIcons = [CloudSun, AlertTriangle, Route, TrendingUp, Sparkles, BrainCircuit]
const factorIconMap = { 季节因素: CloudSun, 气象灾害: AlertTriangle, 运输成本: Route, 市场供需: TrendingUp, 节假日需求: Sparkles, 采集质量: BrainCircuit }
const historyPrices = []

const selectedProduct = ref('')
const selectedSegmentKey = ref('')
const predictionChartRef = ref(null)
const factorChartRef = ref(null)
const aiLoading = ref(false)
const aiInterpretation = ref(null)
const selectedFactorName = ref('')
const {
  advice: decisionAdvice,
  loading: decisionAdviceLoading,
  textLines: decisionAdviceLines,
  loadAdvice: loadDecisionAdvice
} = useAdviceGenerator('prediction')
let predictionChart
let factorChart
let resizeObserver

const productOptions = computed(() => {
  const counts = new Map()
  models.value.forEach((model) => {
    if (!model.product) return
    counts.set(model.product, (counts.get(model.product) || 0) + 1)
  })
  return Array.from(counts.entries())
    .map(([value, count]) => ({ value, label: value, count }))
    .sort((first, second) => first.label.localeCompare(second.label, 'zh-CN'))
})
const segmentOptions = computed(() => {
  const seen = new Set()
  return models.value
    .filter((model) => model.product === selectedProduct.value)
    .filter((model) => {
      if (seen.has(model.segmentKey)) return false
      seen.add(model.segmentKey)
      return true
    })
    .map((model) => ({ value: model.segmentKey, label: model.marketLabel, records: model.trainingRecords }))
    .sort((first, second) => second.records - first.records || first.label.localeCompare(second.label, 'zh-CN'))
})
const activeModel = computed(() => models.value.find((model) => model.product === selectedProduct.value && model.segmentKey === selectedSegmentKey.value) || models.value.find((model) => model.product === selectedProduct.value) || models.value[0] || emptyPredictionModel)
const chartData = computed(() => buildPredictionData(activeModel.value))
const factorData = computed(() => buildFactorData(activeModel.value.weights))
const forecastMax = computed(() => Math.max(...(activeModel.value.forecastBase?.length ? activeModel.value.forecastBase : [0])))
const lastHistoryPrice = computed(() => activeModel.value.historyPrices?.at(-1) ?? historyPrices.at(-1) ?? 0)
const isWarning = computed(() => forecastMax.value > activeModel.value.threshold)
const peakDay = computed(() => Math.max(1, activeModel.value.forecastBase.findIndex((price) => price === forecastMax.value) + 1))
const predictionOption = computed(() => buildPredictionOption(chartData.value, activeModel.value.threshold))
const factorOption = computed(() => buildFactorOption(factorData.value))
const modelMetricItems = computed(() => buildModelMetricItems(activeModel.value))
const displayFactors = computed(() => [...factorData.value].sort((first, second) => Number(second.value) - Number(first.value)).slice(0, 4))
const selectedFactor = computed(() => displayFactors.value.find((factor) => factor.name === selectedFactorName.value) || displayFactors.value[0])
const selectedFactorExplanation = computed(() => decisionAdvice.value?.factorExplanations?.[selectedFactor.value?.name] || '点击左侧因子后，可查看其对当前价格方向和决策动作的解释。')
const decisionConfidence = computed(() => normalizeAccuracy(activeModel.value.confidence))
const decisionAccuracy = computed(() => decisionAdvice.value?.directionalAccuracy ?? activeModel.value.metrics?.significantDirectionalAccuracy ?? activeModel.value.metrics?.directionalAccuracy ?? activeModel.value.confidence)
const isLowConfidence = computed(() => decisionConfidence.value < 70)
const decisionPanelClass = computed(() => {
  if (isLowConfidence.value) return 'border-amber-200 bg-amber-50'
  if ((decisionAdvice.value?.riskLevel || activeModel.value.riskLevel) === 'high') return 'border-red-200 bg-red-50/70'
  return 'border-forest-100 bg-forest-50/80'
})
const decisionTextClass = computed(() => adviceTextClass(decisionAdvice.value?.riskLevel || activeModel.value.riskLevel, decisionAccuracy.value))
const confidenceTextClass = computed(() => isLowConfidence.value ? 'text-amber-700' : 'text-forest-700')

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
watch(models, syncSelectedProduct)
watch(selectedProduct, syncSelectedSegment)
watch(displayFactors, (factors) => {
  if (!factors.some((factor) => factor.name === selectedFactorName.value)) {
    selectedFactorName.value = factors[0]?.name || ''
  }
}, { immediate: true })
watch([activeModel, factorData, forecastMax, peakDay, isWarning], () => {
  if (!activeModel.value.product) {
    decisionAdvice.value = null
    return
  }
  loadDecisionAdvice('prediction', {
    model: activeModel.value,
    factors: factorData.value,
    forecastMax: forecastMax.value,
    peakDay: peakDay.value,
    isWarning: isWarning.value
  })
}, { immediate: true, deep: true })

onMounted(async () => {
  await loadPredictions()
  await nextTick()
  initCharts()
})
onUnmounted(() => {
  if (predictionChart?.__resizeHandler) window.removeEventListener('resize', predictionChart.__resizeHandler)
  resizeObserver?.disconnect()
  predictionChart?.dispose()
  factorChart?.dispose()
})

function buildPredictionData(model) {
  const historySeries = model.historyPrices?.length ? model.historyPrices : historyPrices
  const forecastSeries = model.forecastBase?.length ? model.forecastBase : []
  if (!historySeries.length && !forecastSeries.length) {
    return { labels: [], forecastStartLabel: '', actualLine: [], predictedLine: [], bandLower: [], bandWidth: [] }
  }
  const historyLabels = model.historyLabels?.length ? model.historyLabels : Array.from({ length: historySeries.length }, (_, index) => `历史${index + 1}`)
  const forecastLabels = model.forecastLabels?.length ? model.forecastLabels : Array.from({ length: forecastSeries.length }, (_, index) => `未来${index + 1}`)
  const backtestLookup = new Map((model.backtestForecast || []).map((item) => [item.date, item.predictedPrice]))
  const backtestLine = historyLabels.map((label) => backtestLookup.get(label) ?? null)
  const forecastStart = Math.max(0, historySeries.length - 1)
  const firstLowerBound = model.lowerBound?.[0] ?? (historySeries.at(-1) ?? forecastSeries[0] ?? 0) - 0.08
  return {
    labels: [...historyLabels, ...forecastLabels],
    forecastStartLabel: forecastLabels[0] || historyLabels.at(-1),
    actualLine: [...historySeries, ...Array(forecastSeries.length).fill(null)],
    predictedLine: [...backtestLine, ...forecastSeries],
    bandLower: [...Array(forecastStart).fill(null), firstLowerBound, ...buildLowerBound(model, forecastSeries)],
    bandWidth: [...Array(forecastStart).fill(null), 0.16, ...buildBandWidth(model, forecastSeries)]
  }
}

async function loadPredictions() {
  try {
    const rows = await predictionApi.list()
    if (!Array.isArray(rows) || !rows.length) return
    models.value = rows.map((row, index) => buildModelFromPrediction(row, index))
    syncSelectedProduct()
  } catch (error) {
    ElMessage.error(error.message || '预测数据加载失败')
  }
}

async function generatePredictionInterpretation() {
  if (!activeModel.value.product) {
    ElMessage.warning('暂无可解读的预测数据')
    return
  }
  aiLoading.value = true
  try {
    aiInterpretation.value = await aiApi.predictionInterpretation({
      product: activeModel.value.product,
      marketName: activeModel.value.marketName,
      region: activeModel.value.region,
      modelName: activeModel.value.modelName,
      routingReason: activeModel.value.routingReason,
      confidence: activeModel.value.confidence,
      riskLevel: activeModel.value.riskLevel,
      recentAverage: activeModel.value.recentAverage,
      next7DayAverage: activeModel.value.next7DayAverage,
      changePercent: activeModel.value.changePercent,
      threshold: activeModel.value.threshold,
      forecastMax: forecastMax.value,
      peakDay: peakDay.value,
      lastHistoryPrice: lastHistoryPrice.value,
      isWarning: isWarning.value,
      factors: factorData.value,
      metrics: modelMetricItems.value,
      historyPrices: activeModel.value.historyPrices?.slice(-12) || [],
      forecastBase: activeModel.value.forecastBase?.slice(0, 30) || []
    })
    ElMessage.success('AI 趋势解读已生成')
  } catch (error) {
    ElMessage.error(error.message || 'AI 趋势解读生成失败')
  } finally {
    aiLoading.value = false
  }
}

function riskBadgeVariant(level) {
  return ({ high: 'danger', medium: 'warning', low: 'outline' }[level] || 'warning')
}

function factorIcon(name) {
  return factorIconMap[name] || BrainCircuit
}

function syncSelectedProduct() {
  if (!productOptions.value.some((option) => option.value === selectedProduct.value)) {
    selectedProduct.value = productOptions.value[0]?.value || ''
  }
  syncSelectedSegment()
}

function syncSelectedSegment() {
  if (!segmentOptions.value.some((option) => option.value === selectedSegmentKey.value)) {
    selectedSegmentKey.value = segmentOptions.value[0]?.value || ''
  }
}

function buildModelFromPrediction(row, index) {
  const product = String(row.product || row.product_name || '农产品')
  const marketName = String(row.marketName || row.market_name || '全部市场')
  const region = String(row.region || '全部地区')
  const marketLabel = region && region !== '全部地区' ? `${marketName} / ${region}` : marketName
  const segmentKey = `${marketName}::${region}`
  const base = Number(row.next7DayAverage || row.next_7_day_average || 0)
  const confidence = Number(row.confidence || 0.8)
  const riskLevel = row.riskLevel || row.risk_level || 'low'
  const modelCode = row.model || 'timeSeries'
  const modelName = row.modelName || row.model_name || modelLabel(modelCode, index)
  const metrics = row.metrics && typeof row.metrics === 'object' ? row.metrics : {}
  const isAiForced = Boolean(row.is_ai_forced ?? row.isAiForced)
  const routingReason = normalizeRoutingReason(row.routing_reason || row.routingReason || '', modelName, isAiForced)
  const forecastRows = Array.isArray(row.forecast) ? row.forecast : []
  const historyRows = Array.isArray(row.history) ? row.history : []
  const forecastBase = Array.isArray(row.forecastBase) && row.forecastBase.length
    ? row.forecastBase.map(Number).filter(Number.isFinite)
    : forecastRows.map((item) => Number(item.price)).filter(Number.isFinite)
  const historySeries = historyRows.map((item) => Number(item.price)).filter(Number.isFinite)
  const backtestForecast = Array.isArray(row.backtestForecast) ? row.backtestForecast.map(normalizeBacktestRow).filter(Boolean) : []
  return {
    key: `${row.id || row._id || product}-${segmentKey}-${index}`,
    product,
    marketName,
    region,
    marketLabel,
    segmentKey,
    trainingRecords: Number(row.trainingRecords || row.training_records || 0),
    model: modelCode,
    modelName,
    metrics,
    isAiForced,
    routingReason,
    routingDiagnostics: row.routingDiagnostics || {},
    confidence,
    riskLevel,
    recentAverage: Number(row.recentAverage || row.recent_average || 0),
    next7DayAverage: base,
    changePercent: Number(row.changePercent || row.change_percent || 0),
    label: `${product} · ${marketLabel}`,
    summary: `${product}（${marketLabel}）未来 7 天均价约 ${base.toFixed(2)} 元/公斤，模型置信度 ${(confidence * 100).toFixed(0)}%。`,
    threshold: roundPrice(base * (riskLevel === 'high' ? 0.96 : riskLevel === 'medium' ? 1.04 : 1.12)),
    forecastBase,
    forecastLabels: forecastRows.map((item) => item.date || '').filter(Boolean),
    historyPrices: historySeries,
    historyLabels: historyRows.map((item) => item.date || '').filter(Boolean),
    backtestForecast,
    lowerBound: Array.isArray(row.lowerBound) ? row.lowerBound.map(Number).filter(Number.isFinite) : [],
    upperBound: Array.isArray(row.upperBound) ? row.upperBound.map(Number).filter(Number.isFinite) : [],
    weights: Array.isArray(row.weights) && row.weights.length ? row.weights : []
  }
}

function normalizeBacktestRow(row) {
  const date = row.date || row.ds
  const predictedPrice = Number(row.predictedPrice ?? row.predicted_price ?? row.price)
  const actualPrice = Number(row.actualPrice ?? row.actual_price ?? row.actual)
  const absoluteError = Number(row.absoluteError ?? row.absolute_error)
  const errorPercent = Number(row.errorPercent ?? row.error_percent)
  if (!date || !Number.isFinite(predictedPrice)) return null
  return {
    date,
    predictedPrice,
    actualPrice: Number.isFinite(actualPrice) ? actualPrice : null,
    absoluteError: Number.isFinite(absoluteError) ? absoluteError : null,
    errorPercent: Number.isFinite(errorPercent) ? errorPercent : null
  }
}

function modelLabel(model, index) {
  const labels = { timeSeries: '时间序列模型', weatherAware: '气象感知模型', combined: '组合模型', prophetXgboost: 'Prophet-XGBoost组合模型', recentMedian: '近期中位数稳健模型', recentWeighted: '近期加权均值模型', lastValue: '最近价格基线模型', dampedTrend: '阻尼趋势基线模型' }
  return labels[model] || ['时间序列模型', '随机森林模型', '深度学习模型'][index] || '预测模型'
}

function buildLowerBound(model, forecastSeries) {
  if (model.lowerBound?.length === forecastSeries.length) return model.lowerBound
  return forecastSeries.map((price, index) => roundPrice(price - 0.1 - index * 0.006))
}

function buildBandWidth(model, forecastSeries) {
  if (model.lowerBound?.length === forecastSeries.length && model.upperBound?.length === forecastSeries.length) {
    return model.upperBound.map((price, index) => roundPrice(price - model.lowerBound[index]))
  }
  return forecastSeries.map((_, index) => roundPrice(0.22 + index * 0.012))
}

function buildPredictionOption(data, threshold) {
  const numericValues = [...data.actualLine, ...data.predictedLine, ...data.bandLower, threshold].filter((value) => typeof value === 'number' && Number.isFinite(value))
  if (!numericValues.length) {
    return {
      color: ['#166534', '#2563eb', '#bd7b18', '#22c55e'],
      grid: { left: 48, right: 30, top: 48, bottom: 46 },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value' },
      series: []
    }
  }
  const minValue = Math.min(...numericValues)
  const maxValue = Math.max(...numericValues)
  const padding = Math.max((maxValue - minValue) * 0.16, 0.2)
  return {
    color: ['#166534', '#2563eb', '#bd7b18', '#22c55e'],
    legend: { top: 6, right: 10, itemWidth: 14, itemHeight: 8, textStyle: { color: '#475569' }, data: ['实际价格', '预测价格'] },
    grid: { left: 48, right: 30, top: 48, bottom: 46 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      valueFormatter: (value) => (typeof value === 'number' ? `${value.toFixed(2)} 元/公斤` : value)
    },
    xAxis: { type: 'category', boundaryGap: false, data: data.labels, axisLabel: { color: '#64748b', interval: Math.max(1, Math.floor(data.labels.length / 10)) }, axisLine: { lineStyle: { color: '#cbd5e1' } } },
    yAxis: { type: 'value', name: '元/公斤', min: roundPrice(Math.max(0, minValue - padding)), max: roundPrice(maxValue + padding), axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } } },
    series: [
      { name: '区间下界', type: 'line', stack: 'confidence-band', data: data.bandLower, symbol: 'none', lineStyle: { opacity: 0 }, tooltip: { show: false }, emphasis: { disabled: true } },
      { name: '波动区间', type: 'line', stack: 'confidence-band', data: data.bandWidth, symbol: 'none', lineStyle: { opacity: 0 }, areaStyle: { color: 'rgba(34, 197, 94, 0.18)' }, tooltip: { show: false }, emphasis: { disabled: true } },
      { name: '实际价格', type: 'line', data: data.actualLine, smooth: true, showSymbol: false, lineStyle: { width: 3, color: '#166534' } },
      {
        name: '预测价格',
        type: 'line',
        data: data.predictedLine,
        smooth: true,
        showSymbol: false,
        connectNulls: false,
        lineStyle: { width: 3, color: '#bd7b18', type: 'dashed' },
        markLine: {
          symbol: 'none',
          label: { color: '#475569' },
          lineStyle: { color: '#94a3b8', type: 'dashed' },
          data: [
            { yAxis: threshold, label: { formatter: `预警阈值 ${threshold.toFixed(2)}`, color: '#b91c1c' }, lineStyle: { color: '#ef4444', type: 'dashed' } },
            { xAxis: data.forecastStartLabel, label: { formatter: '未来预测' } }
          ]
        }
      }
    ]
  }
}

function buildFactorData(weights) {
  if (Array.isArray(weights) && weights.every((item) => item && typeof item === 'object')) {
    return weights
      .map((item) => ({ name: item.factor || item.name, value: Number(item.percent ?? Number(item.weight) * 100) }))
      .filter((item) => item.name && Number.isFinite(item.value))
      .sort((first, second) => first.value - second.value)
  }
  return factorLabels
    .map((name, index) => ({ name, value: Number(weights[index]) }))
    .filter((item) => Number.isFinite(item.value))
    .sort((first, second) => first.value - second.value)
}

function buildFactorOption(data) {
  const maxValue = Math.max(36, ...data.map((item) => item.value))
  return {
    grid: { left: 82, right: 28, top: 16, bottom: 24 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (value) => `${value}%` },
    xAxis: { type: 'value', max: Math.ceil(maxValue / 5) * 5, axisLabel: { color: '#64748b', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } } },
    yAxis: { type: 'category', data: data.map((item) => item.name), axisLabel: { color: '#475569' }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{ name: '权重', type: 'bar', data: data.map((item) => item.value), barWidth: 18, itemStyle: { borderRadius: [0, 6, 6, 0], color: '#166534' }, label: { show: true, position: 'right', color: '#0f172a', formatter: '{c}%' } }]
  }
}

function buildModelMetricItems(model) {
  const metrics = model.metrics || {}
  return [
    { label: '当前模型', value: model.modelName || '预测模型', detail: model.isAiForced ? 'AI 强制采用' : '综合评分选择', emphasis: model.isAiForced },
    { label: '综合评分', value: formatDecimal(metrics.ensembleScore, 4), detail: `路由：${model.routingReason || '已选择最优模型'}` },
    { label: '显著方向准确率', value: formatRatio(metrics.significantDirectionalAccuracy ?? metrics.directionalAccuracy), detail: `${Number(metrics.directionalSampleCount || 0)} 个有效波动样本` },
    { label: '置信度', value: formatRatio(model.confidence), detail: `${riskLabel(model.riskLevel)} · 未来 7 天 ${formatSignedPercent(model.changePercent)}` }
  ]
}

function normalizeRoutingReason(reason, modelName, isAiForced) {
  if (isAiForced) return 'AI 综合评分超过最近值基线 10%，已采用该模型'
  if (reason?.startsWith('selected ')) return `综合评分选择 ${modelName}`
  return reason || `综合评分选择 ${modelName}`
}

function formatPrice(value) {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue.toFixed(2) : '--'
}

function formatDecimal(value, digits = 2) {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue.toFixed(digits) : '--'
}

function formatRatio(value) {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return '--'
  const percentValue = Math.abs(numericValue) <= 1 ? numericValue * 100 : numericValue
  return `${percentValue.toFixed(2)}%`
}

function formatSignedPercent(value) {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return '--'
  return `${numericValue > 0 ? '+' : ''}${numericValue.toFixed(2)}%`
}

function riskLabel(value) {
  const labels = { high: '高风险', medium: '中风险', low: '低风险', unknown: '未知风险' }
  return labels[value] || labels.unknown
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
          <h2 class="text-base font-semibold text-slate-950">价格预测</h2>
          <p class="mt-1 text-sm leading-6 text-slate-500">{{ activeModel.summary }}</p>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 xl:min-w-[520px]">
          <label class="space-y-1">
            <span class="text-xs font-medium text-slate-500">产品</span>
            <select v-model="selectedProduct" class="h-10 w-full rounded-md border bg-white px-3 text-sm font-medium text-slate-800 outline-none transition-colors focus:border-forest-500 focus:ring-2 focus:ring-forest-100">
              <option v-for="option in productOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </label>
          <label class="space-y-1">
            <span class="text-xs font-medium text-slate-500">市场/地区</span>
            <select v-model="selectedSegmentKey" class="h-10 w-full rounded-md border bg-white px-3 text-sm font-medium text-slate-800 outline-none transition-colors focus:border-forest-500 focus:ring-2 focus:ring-forest-100">
              <option v-for="option in segmentOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </label>
        </div>
        <Button variant="secondary" :disabled="aiLoading" class="xl:self-end" @click="generatePredictionInterpretation">
          <Sparkles :class="['h-4 w-4', aiLoading && 'animate-pulse']" />AI 解读
        </Button>
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
          <div v-for="item in [{ label: '历史末值', value: lastHistoryPrice }, { label: '预测峰值', value: forecastMax, danger: isWarning }, { label: '阈值', value: activeModel.threshold }]" :key="item.label" class="rounded-lg border bg-white px-3 py-2">
            <p class="text-xs text-slate-500">{{ item.label }}</p>
            <p :class="['mt-1 text-base font-semibold', item.danger ? 'text-red-700' : 'text-slate-950']">{{ item.value.toFixed(2) }}</p>
          </div>
        </div>
      </div>
    </section>

    <section v-if="aiInterpretation" class="rounded-lg border border-emerald-100 bg-emerald-50 p-5 shadow-panel">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <Sparkles class="h-5 w-5 text-[#064e3b]" />
            <h2 class="text-base font-semibold text-[#064e3b]">{{ aiInterpretation.title || '趋势预测 AI 解读' }}</h2>
          </div>
          <p class="mt-2 text-sm leading-6 text-slate-700">{{ aiInterpretation.summary }}</p>
          <p class="mt-2 text-sm leading-6 text-slate-600">{{ aiInterpretation.analysis }}</p>
        </div>
        <p class="rounded-lg border border-emerald-100 bg-white px-3 py-2 text-xs leading-5 text-slate-500 lg:max-w-[320px]">{{ aiInterpretation.dataCaveat }}</p>
      </div>
      <div class="mt-4 grid gap-3 md:grid-cols-2">
        <div class="rounded-lg bg-white p-4 text-sm leading-6 text-slate-600 shadow-sm">
          <p class="font-semibold text-slate-950">建议</p>
          <p v-for="item in aiInterpretation.suggestions || []" :key="item" class="mt-1">{{ item }}</p>
        </div>
        <div class="rounded-lg bg-white p-4 text-sm leading-6 text-slate-600 shadow-sm">
          <p class="font-semibold text-slate-950">下一步动作</p>
          <p v-for="item in aiInterpretation.actions || []" :key="item" class="mt-1">{{ item }}</p>
        </div>
      </div>
    </section>

    <section class="rounded-lg border bg-white p-4 shadow-panel">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <h2 class="text-base font-semibold text-slate-950">模型决策</h2>
            <Badge variant="outline">{{ activeModel.modelName }}</Badge>
          </div>
          <p class="mt-1 max-w-3xl text-sm leading-6 text-slate-500">{{ activeModel.routingReason }}</p>
        </div>
        <div class="grid gap-2 sm:grid-cols-2 lg:min-w-[520px] xl:grid-cols-4">
          <div v-for="item in modelMetricItems" :key="item.label" :class="['rounded-lg border px-3 py-2', item.emphasis ? 'border-forest-200 bg-forest-50' : 'bg-slate-50']">
            <p class="text-xs text-slate-500">{{ item.label }}</p>
            <p :class="['mt-1 truncate text-sm font-semibold', item.emphasis ? 'text-forest-800' : 'text-slate-950']" :title="item.value">{{ item.value }}</p>
            <p class="mt-1 line-clamp-2 text-xs leading-5 text-slate-500" :title="item.detail">{{ item.detail }}</p>
          </div>
        </div>
      </div>
    </section>

    <div class="grid gap-4 xl:grid-cols-[1.6fr_0.9fr]">
      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="text-base font-semibold text-slate-950">{{ activeModel.label }}</h2>
              
            </div>
            <p class="mt-1 text-sm text-slate-500">历史区间展示实际价格和预测价格，未来 30 天预测沿同一条虚线延伸。</p>
          </div>
          <div class="flex flex-wrap gap-2 text-xs text-slate-500">
            <span class="inline-flex items-center gap-2"><span class="h-0 w-8 border-t-2 border-[#166534]" />实际价格</span>
            <span class="inline-flex items-center gap-2"><span class="h-0 w-8 border-t-2 border-dashed border-[#bd7b18]" />预测价格</span>
            <span class="inline-flex items-center gap-2"><span class="h-0 w-8 border-t-2 border-[rgba(34,197,94,0.28)]" />波动区间</span>
          </div>
        </div>
        <div ref="predictionChartRef" role="img" aria-label="置信区间预测图" class="h-[430px] w-full rounded-lg border bg-slate-50" />

        <div :class="['mt-4 rounded-lg border p-4', decisionPanelClass]">
          <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <Sparkles class="h-5 w-5 text-forest-700" />
                <h3 class="text-base font-semibold text-slate-950">因子驱动与决策面板</h3>
                <Badge :variant="riskBadgeVariant(decisionAdvice?.riskLevel || activeModel.riskLevel)">{{ riskLabel(decisionAdvice?.riskLevel || activeModel.riskLevel) }}</Badge>
              </div>
              <p :class="['mt-2 text-sm leading-6', decisionTextClass]">{{ decisionAdvice?.coreConclusion || '正在汇总预测结论...' }}</p>
            </div>
            <div class="grid shrink-0 gap-2 sm:grid-cols-2 lg:min-w-[300px]">
              <div class="rounded-lg border bg-white px-3 py-2">
                <p class="text-xs text-slate-500">模型置信度</p>
                <p :class="['mt-1 text-base font-semibold', confidenceTextClass]">{{ formatAdviceAccuracy(activeModel.confidence) }}</p>
              </div>
              <div class="rounded-lg border bg-white px-3 py-2">
                <p class="text-xs text-slate-500">方向准确率</p>
                <p :class="['mt-1 text-base font-semibold', decisionTextClass]">{{ formatAdviceAccuracy(decisionAccuracy) }}</p>
              </div>
            </div>
          </div>

          <el-descriptions class="mt-4 overflow-hidden rounded-lg" :column="2" border size="small">
            <el-descriptions-item label="核心结论">
              <span :class="decisionTextClass">{{ decisionAdvice?.coreConclusion || '等待模型输出' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="主要因子">
              <span :class="decisionTextClass">{{ selectedFactor?.name || '市场供需' }} · {{ Number(selectedFactor?.value || 0).toFixed(0) }}%</span>
            </el-descriptions-item>
            <el-descriptions-item label="预警阈值">
              <span :class="isWarning ? 'text-red-700' : 'text-forest-700'">{{ activeModel.threshold.toFixed(2) }} 元/公斤</span>
            </el-descriptions-item>
            <el-descriptions-item label="生成状态">
              <span :class="decisionAdviceLoading ? 'text-amber-700' : 'text-forest-700'">{{ decisionAdviceLoading ? '分析中' : '已生成' }}</span>
            </el-descriptions-item>
          </el-descriptions>

          <el-alert
            v-if="isLowConfidence"
            class="mt-3"
            title="置信度低于 70%，建议结合 LastValue 进行稳健决策。"
            type="warning"
            :closable="false"
            show-icon
          />

          <div class="mt-4 grid gap-3 lg:grid-cols-[1fr_1.1fr]">
            <div class="rounded-lg border bg-white p-3">
              <p class="text-xs font-medium text-slate-500">选中因子解释</p>
              <div class="mt-2 flex items-center gap-2">
                <span class="flex h-8 w-8 items-center justify-center rounded-lg border bg-forest-50 text-forest-700"><component :is="factorIcon(selectedFactor?.name)" class="h-4 w-4" /></span>
                <span class="text-sm font-semibold text-slate-950">{{ selectedFactor?.name || '预测因子' }}</span>
              </div>
              <p :class="['mt-2 text-sm leading-6', decisionTextClass]">{{ selectedFactorExplanation }}</p>
            </div>
            <div class="rounded-lg border bg-white p-3">
              <p class="text-xs font-medium text-slate-500">AI 行情短评</p>
              <AiAdviceLines v-if="decisionAdviceLines.length" class="mt-2" :lines="decisionAdviceLines" :text-class="decisionTextClass" compact />
              <p v-else class="mt-2 text-sm leading-6 text-slate-500">正在根据当前预测结果生成行情短评...</p>
            </div>
          </div>
        </div>
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
          <button
            v-for="factor in displayFactors"
            :key="factor.name"
            :class="['flex items-center justify-between rounded-lg border px-3 py-2 text-left transition-colors', selectedFactorName === factor.name ? 'border-forest-200 bg-forest-50' : 'bg-slate-50 hover:bg-white']"
            type="button"
            @click="selectedFactorName = factor.name"
          >
            <div class="flex items-center gap-2">
              <span class="flex h-8 w-8 items-center justify-center rounded-lg border bg-white text-forest-700"><component :is="factorIcon(factor.name)" class="h-4 w-4" /></span>
              <span class="text-sm font-medium text-slate-800">{{ factor.name }}</span>
            </div>
            <span class="text-sm font-semibold text-slate-950">{{ factor.value }}%</span>
          </button>
        </div>
      </section>
    </div>
  </div>
</template>