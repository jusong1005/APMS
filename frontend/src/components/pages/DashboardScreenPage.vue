<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { Activity, AlertTriangle, Database, Radio, RefreshCw, ShieldCheck, Sprout, TrendingUp, Wifi, Zap } from 'lucide-vue-next'
import Button from '../ui/Button.vue'
import { dashboardApi } from '../../lib/api'

const metricIcons = [Database, Radio, Sprout, AlertTriangle]
const metricTones = [
  { icon: 'text-emerald-200', ring: 'border-emerald-400/30 bg-emerald-400/10' },
  { icon: 'text-cyan-200', ring: 'border-cyan-300/30 bg-cyan-300/10' },
  { icon: 'text-harvest-400', ring: 'border-harvest-400/30 bg-harvest-400/10' },
  { icon: 'text-red-200', ring: 'border-red-300/30 bg-red-300/10' }
]

const overview = ref({
  cards: [
    { label: '今日采集记录', value: 0, change: '+实时', trend: 'up' },
    { label: '覆盖市场主体', value: 0, change: '+MongoDB', trend: 'up' },
    { label: '重点农产品', value: 0, change: '+MongoDB', trend: 'up' },
    { label: '异常波动预警', value: 0, change: 'Redis/Mongo', trend: 'down' }
  ]
})
const realtime = ref({})
const trendRows = ref([])
const alerts = ref([])
const loading = ref(false)
const error = ref('')
const updatedAt = ref(new Date())
const trendChartRef = ref(null)

let trendChart
let refreshTimer

const numberFormat = new Intl.NumberFormat('zh-CN')
const timeFormat = new Intl.DateTimeFormat('zh-CN', {
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false
})

const metricCards = computed(() => {
  const cards = Array.isArray(overview.value.cards) ? overview.value.cards : []
  return cards.slice(0, 4).map((card, index) => ({
    ...card,
    valueText: formatNumber(card.value),
    icon: metricIcons[index] || TrendingUp,
    tone: metricTones[index] || metricTones[0]
  }))
})

const normalizedPrices = computed(() => {
  const raw = realtime.value.latestPrices
  const list = Array.isArray(raw) ? raw : Array.isArray(raw?.items) ? raw.items : []
  return list.slice(0, 6).map((item, index) => ({
    name: item.product_name || item.productName || item.product || `品类 ${index + 1}`,
    category: item.product_category || item.category || '重点监测',
    value: Number(item.mean_price || item.average_price || item.averagePrice || item.price || 0),
    recordCount: Number(item.record_count || item.recordCount || item.count || 0),
    regionCount: Number(item.region_count || item.regionCount || 0)
  }))
})

const normalizedAlerts = computed(() => {
  return alerts.value.slice(0, 8).map((alert, index) => {
    const rate = Number(alert.change_rate ?? alert.changeRate ?? alert.rate ?? 0)
    const level = alert.level || (Math.abs(rate) >= 12 ? 'high' : Math.abs(rate) >= 8 ? 'medium' : 'low')
    return {
      id: alert.id || `${alert.product_name || alert.product || index}-${index}`,
      product: alert.product_name || alert.productName || alert.product || '农产品',
      region: alert.region || '全国',
      rate,
      level,
      status: alert.status || 'open',
      detectedAt: alert.detected_at || alert.detectedAt || alert.time || ''
    }
  })
})

const alertSummary = computed(() => ({
  high: normalizedAlerts.value.filter((alert) => alert.level === 'high').length,
  medium: normalizedAlerts.value.filter((alert) => alert.level === 'medium').length,
  low: normalizedAlerts.value.filter((alert) => alert.level !== 'high' && alert.level !== 'medium').length
}))

const batchTiles = computed(() => {
  const batch = realtime.value.lastBatch || {}
  const metrics = realtime.value.metrics || {}
  return [
    { label: '实时批次数', value: formatNumber(batch.batch_count ?? batch.batchCount ?? metrics.batch_count ?? 0), icon: Zap },
    { label: '平均价格', value: formatPrice(batch.realtime_average_price ?? batch.realtimeAveragePrice ?? metrics.average_price), icon: Activity },
    { label: '缓存状态', value: Object.keys(metrics).length ? '在线' : '演示', icon: Wifi },
    { label: '链路状态', value: error.value ? '关注' : '正常', icon: ShieldCheck }
  ]
})

const regionHotspots = computed(() => {
  const source = normalizedAlerts.value.length ? normalizedAlerts.value : [
    { region: '山东', product: '番茄', rate: 18.6, level: 'medium' },
    { region: '河南', product: '苹果', rate: -12.2, level: 'high' },
    { region: '四川', product: '玉米', rate: 4.1, level: 'low' },
    { region: '北京', product: '猪肉', rate: 6.8, level: 'low' }
  ]
  return source.slice(0, 5)
})

const updatedText = computed(() => timeFormat.format(updatedAt.value))

const loadScreen = async () => {
  loading.value = true
  error.value = ''
  try {
    const [overviewData, realtimeData, trendData, alertData] = await Promise.all([
      dashboardApi.overview(),
      dashboardApi.realtime(),
      dashboardApi.trend(),
      dashboardApi.alerts()
    ])
    overview.value = overviewData || overview.value
    realtime.value = realtimeData || {}
    trendRows.value = Array.isArray(trendData) ? trendData : []
    alerts.value = Array.isArray(alertData) ? alertData : []
    updatedAt.value = new Date()
  } catch (exception) {
    error.value = exception.message || '数据刷新失败'
  } finally {
    loading.value = false
    await nextTick()
    renderTrendChart()
  }
}

const ensureChart = () => {
  if (!trendChartRef.value) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)
}

const renderTrendChart = () => {
  ensureChart()
  if (!trendChart) return
  const rows = trendRows.value.length ? trendRows.value : [
    { date: '2026-05-19', average_price: 4.21, record_count: 1280 },
    { date: '2026-05-20', average_price: 4.33, record_count: 1324 },
    { date: '2026-05-21', average_price: 4.27, record_count: 1296 },
    { date: '2026-05-22', average_price: 4.42, record_count: 1411 },
    { date: '2026-05-23', average_price: 4.48, record_count: 1388 },
    { date: '2026-05-24', average_price: 4.39, record_count: 1360 },
    { date: '2026-05-25', average_price: 4.56, record_count: 1442 }
  ]
  const labels = rows.map((row, index) => String(row.date || row.time || index + 1).replace(/^\d{4}-/, ''))
  const prices = rows.map((row) => Number(row.average_price ?? row.averagePrice ?? row.price ?? 0))
  const counts = rows.map((row) => Number(row.record_count ?? row.recordCount ?? 0))

  trendChart.setOption({
    backgroundColor: 'transparent',
    color: ['#34d399', '#d99b2b'],
    grid: { left: 42, right: 42, top: 36, bottom: 36 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(7, 31, 22, 0.96)',
      borderColor: 'rgba(52, 211, 153, 0.28)',
      textStyle: { color: '#ecfdf5' }
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels,
      axisLine: { lineStyle: { color: 'rgba(167, 243, 208, 0.24)' } },
      axisTick: { show: false },
      axisLabel: { color: '#a7f3d0', fontSize: 11 }
    },
    yAxis: [
      {
        type: 'value',
        name: '均价',
        nameTextStyle: { color: '#a7f3d0' },
        splitLine: { lineStyle: { color: 'rgba(167, 243, 208, 0.12)' } },
        axisLabel: { color: '#a7f3d0' }
      },
      {
        type: 'value',
        name: '记录',
        nameTextStyle: { color: '#f5d08a' },
        splitLine: { show: false },
        axisLabel: { color: '#f5d08a' }
      }
    ],
    series: [
      {
        name: '全国均价',
        type: 'line',
        smooth: true,
        symbolSize: 7,
        lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(52, 211, 153, 0.32)' },
            { offset: 1, color: 'rgba(52, 211, 153, 0.02)' }
          ])
        },
        data: prices
      },
      {
        name: '采集记录',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: 10,
        itemStyle: { borderRadius: [4, 4, 0, 0], color: 'rgba(217, 155, 43, 0.72)' },
        data: counts
      }
    ]
  })
}

const formatNumber = (value) => numberFormat.format(Number(value || 0))
const formatPrice = (value) => {
  const numberValue = Number(value || 0)
  return numberValue > 0 ? `¥${numberValue.toFixed(2)}` : '--'
}
const alertTone = (level) => level === 'high' ? 'text-red-200 bg-red-400/15 border-red-300/30' : level === 'medium' ? 'text-harvest-400 bg-harvest-400/15 border-harvest-400/30' : 'text-emerald-100 bg-emerald-400/10 border-emerald-300/20'
const alertLabel = (level) => level === 'high' ? '高' : level === 'medium' ? '中' : '低'

watch(trendRows, renderTrendChart, { deep: true })

onMounted(async () => {
  await loadScreen()
  refreshTimer = window.setInterval(loadScreen, 30000)
  window.addEventListener('resize', renderTrendChart)
})

onUnmounted(() => {
  window.clearInterval(refreshTimer)
  window.removeEventListener('resize', renderTrendChart)
  if (trendChart) {
    trendChart.dispose()
    trendChart = null
  }
})
</script>

<template>
  <div class="min-h-[calc(100vh-64px)] bg-[#071f16] text-emerald-50">
    <div class="border-b border-emerald-300/10 bg-[#0a2a1d] px-6 py-4">
      <div class="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2 text-xs text-emerald-100/70">
            <span class="rounded-md border border-emerald-300/20 bg-emerald-300/10 px-2 py-1">实时监测</span>
            <span class="rounded-md border border-harvest-400/25 bg-harvest-400/10 px-2 py-1 text-harvest-400">全国联动</span>
            <span class="rounded-md border border-cyan-300/20 bg-cyan-300/10 px-2 py-1 text-cyan-100">Redis / MongoDB</span>
          </div>
          <h2 class="mt-3 text-2xl font-semibold tracking-normal text-white">全国农产品价格监控大屏</h2>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-emerald-100/65">采集链路、价格指数、实时缓存和异常预警集中展示。</p>
        </div>
        <div class="flex items-center gap-3">
          <div class="rounded-lg border border-emerald-300/15 bg-white/5 px-3 py-2 text-right">
            <p class="text-xs text-emerald-100/55">更新时间</p>
            <p class="mt-1 text-sm font-semibold text-emerald-50">{{ updatedText }}</p>
          </div>
          <Button
            variant="secondary"
            size="icon"
            class="border-emerald-300/20 bg-emerald-300/10 text-emerald-50 hover:bg-emerald-300/20"
            title="刷新数据"
            :disabled="loading"
            @click="loadScreen"
          >
            <RefreshCw :class="['h-4 w-4', loading && 'animate-spin']" />
          </Button>
        </div>
      </div>
    </div>

    <div class="grid gap-4 p-5 xl:grid-cols-[1.05fr_1.75fr_1.05fr]">
      <section class="space-y-4">
        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
          <article v-for="metric in metricCards" :key="metric.label" class="rounded-lg border border-emerald-300/12 bg-white/[0.055] p-4">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="text-xs text-emerald-100/60">{{ metric.label }}</p>
                <p class="mt-2 truncate text-2xl font-semibold text-white">{{ metric.valueText }}</p>
              </div>
              <div :class="['flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border', metric.tone.ring]">
                <component :is="metric.icon" :class="['h-5 w-5', metric.tone.icon]" />
              </div>
            </div>
            <div class="mt-3 flex items-center gap-2 text-xs">
              <TrendingUp :class="['h-4 w-4', metric.trend === 'down' ? 'text-red-200' : 'text-emerald-200']" />
              <span :class="metric.trend === 'down' ? 'text-red-200' : 'text-emerald-200'">{{ metric.change }}</span>
              <span class="text-emerald-100/45">较上一批次</span>
            </div>
          </article>
        </div>

        <article class="rounded-lg border border-emerald-300/12 bg-white/[0.055] p-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-white">实时链路</h3>
            <span :class="['rounded-md border px-2 py-1 text-xs', error ? 'border-red-300/30 bg-red-400/15 text-red-200' : 'border-emerald-300/20 bg-emerald-300/10 text-emerald-100']">{{ error ? '需关注' : '运行中' }}</span>
          </div>
          <div class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            <div v-for="tile in batchTiles" :key="tile.label" class="rounded-lg border border-white/10 bg-[#0d3523]/75 p-3">
              <component :is="tile.icon" class="h-4 w-4 text-harvest-400" />
              <p class="mt-3 text-xs text-emerald-100/55">{{ tile.label }}</p>
              <p class="mt-1 text-lg font-semibold text-white">{{ tile.value }}</p>
            </div>
          </div>
        </article>
      </section>

      <section class="space-y-4">
        <article class="rounded-lg border border-emerald-300/12 bg-white/[0.055] p-4">
          <div class="flex flex-col justify-between gap-2 md:flex-row md:items-center">
            <div>
              <h3 class="text-sm font-semibold text-white">全国价格指数趋势</h3>
              <p class="mt-1 text-xs text-emerald-100/50">均价走势与采集记录同屏对照</p>
            </div>
            <div class="flex gap-2 text-xs text-emerald-100/60">
              <span class="rounded-md bg-emerald-300/10 px-2 py-1 text-emerald-100">均价</span>
              <span class="rounded-md bg-harvest-400/10 px-2 py-1 text-harvest-400">记录</span>
            </div>
          </div>
          <div ref="trendChartRef" class="mt-3 h-[360px] w-full" />
        </article>

        <article class="rounded-lg border border-emerald-300/12 bg-white/[0.055] p-4">
          <div class="flex items-center justify-between gap-3">
            <h3 class="text-sm font-semibold text-white">重点品类实时价格</h3>
            <span class="text-xs text-emerald-100/50">{{ normalizedPrices.length }} 项</span>
          </div>
          <div class="mt-4 grid gap-3 md:grid-cols-2 2xl:grid-cols-3">
            <div v-for="price in normalizedPrices" :key="price.name" class="rounded-lg border border-white/10 bg-[#0d3523]/70 p-3">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-white">{{ price.name }}</p>
                  <p class="mt-1 truncate text-xs text-emerald-100/50">{{ price.category }}</p>
                </div>
                <p class="shrink-0 text-lg font-semibold text-harvest-400">{{ formatPrice(price.value) }}</p>
              </div>
              <div class="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
                <div class="h-full rounded-full bg-emerald-300" :style="{ width: `${Math.min(100, Math.max(14, price.recordCount / 8))}%` }" />
              </div>
              <div class="mt-2 flex justify-between text-xs text-emerald-100/45">
                <span>{{ formatNumber(price.recordCount) }} 条</span>
                <span>{{ price.regionCount || '--' }} 区域</span>
              </div>
            </div>
          </div>
        </article>
      </section>

      <section class="space-y-4">
        <article class="rounded-lg border border-emerald-300/12 bg-white/[0.055] p-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-white">预警态势</h3>
            <AlertTriangle class="h-4 w-4 text-harvest-400" />
          </div>
          <div class="mt-4 grid grid-cols-3 gap-2">
            <div class="rounded-lg border border-red-300/20 bg-red-400/10 p-3 text-center">
              <p class="text-xs text-red-100/70">高</p>
              <p class="mt-1 text-2xl font-semibold text-red-100">{{ alertSummary.high }}</p>
            </div>
            <div class="rounded-lg border border-harvest-400/25 bg-harvest-400/10 p-3 text-center">
              <p class="text-xs text-harvest-400/80">中</p>
              <p class="mt-1 text-2xl font-semibold text-harvest-400">{{ alertSummary.medium }}</p>
            </div>
            <div class="rounded-lg border border-emerald-300/20 bg-emerald-300/10 p-3 text-center">
              <p class="text-xs text-emerald-100/70">低</p>
              <p class="mt-1 text-2xl font-semibold text-emerald-100">{{ alertSummary.low }}</p>
            </div>
          </div>
        </article>

        <article class="rounded-lg border border-emerald-300/12 bg-white/[0.055] p-4">
          <div class="flex items-center justify-between gap-3">
            <h3 class="text-sm font-semibold text-white">重点省份热区</h3>
            <Radio class="h-4 w-4 text-cyan-100" />
          </div>
          <div class="mt-4 space-y-2">
            <div v-for="item in regionHotspots" :key="`${item.region}-${item.product}`" class="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-[#0d3523]/70 px-3 py-2">
              <div class="min-w-0">
                <p class="truncate text-sm font-semibold text-white">{{ item.region }}</p>
                <p class="mt-1 truncate text-xs text-emerald-100/48">{{ item.product }}</p>
              </div>
              <span :class="['shrink-0 rounded-md border px-2 py-1 text-xs', alertTone(item.level)]">{{ Math.abs(item.rate).toFixed(1) }}%</span>
            </div>
          </div>
        </article>

        <article class="rounded-lg border border-emerald-300/12 bg-white/[0.055] p-4">
          <div class="flex items-center justify-between gap-3">
            <h3 class="text-sm font-semibold text-white">实时预警列表</h3>
            <span class="text-xs text-emerald-100/50">{{ normalizedAlerts.length }} 条</span>
          </div>
          <div class="mt-4 space-y-2">
            <div v-for="alert in normalizedAlerts" :key="alert.id" class="rounded-lg border border-white/10 bg-[#0d3523]/70 px-3 py-2">
              <div class="flex items-center justify-between gap-3">
                <p class="min-w-0 truncate text-sm font-semibold text-white">{{ alert.region }} {{ alert.product }}</p>
                <span :class="['shrink-0 rounded-md border px-2 py-1 text-xs', alertTone(alert.level)]">{{ alertLabel(alert.level) }}</span>
              </div>
              <div class="mt-2 flex items-center justify-between gap-3 text-xs text-emerald-100/48">
                <span>{{ alert.rate >= 0 ? '涨幅' : '跌幅' }} {{ Math.abs(alert.rate).toFixed(1) }}%</span>
                <span class="truncate">{{ alert.status }}</span>
              </div>
            </div>
          </div>
        </article>
      </section>
    </div>
  </div>
</template>