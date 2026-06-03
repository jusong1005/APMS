<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, BarChart3, CheckCircle2, Clock3, Database, RefreshCw, ServerCog, ShieldCheck, Sprout, TrendingUp, Wifi, Zap } from 'lucide-vue-next'
import Badge from '../ui/Badge.vue'
import Button from '../ui/Button.vue'
import { dashboardApi } from '../../lib/api'
import { useScreenChart } from '../dashboard-screen/useScreenChart'

const metricIcons = [Database, ServerCog, Sprout, AlertTriangle]
const trendChartRef = ref(null)
const categoryChartRef = ref(null)
const loading = ref(false)
const lastUpdatedAt = ref(new Date())

const metrics = ref([
  { label: '累计入库记录', value: '126,840', change: '演示数据', trend: 'up', icon: Database },
  { label: '覆盖市场主体', value: '1,528', change: '+36', trend: 'up', icon: ServerCog },
  { label: '重点农产品', value: '512', change: '+18', trend: 'up', icon: Sprout },
  { label: '异常波动预警', value: '24', change: '-8.1%', trend: 'down', icon: AlertTriangle }
])
const realtime = ref({})
const trendRows = ref([])
const alertRows = ref([
  { name: '山东 番茄', detail: '涨幅 18.6%', level: 'medium', status: 'open' },
  { name: '四川 玉米', detail: '涨幅 4.1%', level: 'low', status: 'open' },
  { name: '河南 苹果', detail: '跌幅 12.2%', level: 'high', status: 'acknowledged' }
])
const priceRows = ref([
  { product: '番茄', category: '蔬菜类', price: 4.28, recordCount: 620, regionCount: 31 },
  { product: '玉米', category: '粮食类', price: 2.86, recordCount: 584, regionCount: 31 },
  { product: '苹果', category: '水果类', price: 7.24, recordCount: 576, regionCount: 31 },
  { product: '大白菜', category: '蔬菜类', price: 2.18, recordCount: 548, regionCount: 31 },
  { product: '猪肉', category: '肉禽蛋类', price: 21.35, recordCount: 564, regionCount: 31 }
])

const categoryStats = computed(() => {
  const grouped = new Map()
  priceRows.value.forEach((row) => {
    grouped.set(row.category || '其他', (grouped.get(row.category || '其他') || 0) + Number(row.recordCount || 1))
  })
  return Array.from(grouped.entries()).map(([name, value]) => ({ name, value }))
})

const batchCards = computed(() => {
  const lastBatch = realtime.value.lastBatch || {}
  const redisMetrics = realtime.value.metrics || {}
  const usingMongoLatest = lastBatch.status === 'mongo_latest'
  return [
    { label: usingMongoLatest ? '最新入库品类' : '最新批次', value: formatNumber(lastBatch.batch_count ?? lastBatch.batchCount ?? redisMetrics.batch_count ?? 0), icon: Zap, status: usingMongoLatest ? '入库' : '实时' },
    { label: usingMongoLatest ? '最新入库均价' : '实时均价', value: formatPrice(lastBatch.latest_average_price ?? lastBatch.latestAveragePrice ?? lastBatch.realtime_average_price ?? lastBatch.realtimeAveragePrice ?? redisMetrics.average_price), icon: Activity, status: usingMongoLatest ? 'MongoDB' : 'Redis' },
    { label: 'Redis 缓存', value: Object.keys(redisMetrics).length ? '在线' : '演示', icon: Wifi, status: '正常' },
    { label: '入库链路', value: priceRows.value.length ? '可用' : '待同步', icon: CheckCircle2, status: 'MongoDB' }
  ]
})

const qualityItems = computed(() => [
  { label: '采集成功率', value: 98.6, color: 'bg-forest-600' },
  { label: '清洗通过率', value: 96.8, color: 'bg-emerald-500' },
  { label: '入库完整率', value: 99.1, color: 'bg-harvest-400' },
  { label: '预警闭环率', value: 91.4, color: 'bg-violet-400' }
])

const updatedText = computed(() => new Intl.DateTimeFormat('zh-CN', {
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false
}).format(lastUpdatedAt.value))

const formatShortDate = (value, fallback) => {
  const text = String(value || fallback || '')
  const isoDate = text.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (isoDate) return `${isoDate[2]}-${isoDate[3]}`
  const shortDate = text.match(/^(\d{2})-(\d{2})(?:T.*)?$/)
  if (shortDate) return `${shortDate[1]}-${shortDate[2]}`
  const parsed = new Date(text)
  if (!Number.isNaN(parsed.getTime())) {
    return `${String(parsed.getMonth() + 1).padStart(2, '0')}-${String(parsed.getDate()).padStart(2, '0')}`
  }
  return text
}

const buildTrendOption = () => {
  const rows = trendRows.value.length ? trendRows.value.slice(-12) : [
    { date: '05-19', average_price: 4.21, record_count: 1280 },
    { date: '05-20', average_price: 4.33, record_count: 1324 },
    { date: '05-21', average_price: 4.27, record_count: 1296 },
    { date: '05-22', average_price: 4.42, record_count: 1411 },
    { date: '05-23', average_price: 4.48, record_count: 1388 },
    { date: '05-24', average_price: 4.39, record_count: 1360 },
    { date: '05-25', average_price: 4.56, record_count: 1442 }
  ]
  return {
    color: ['#1b6f42', '#d99b2b'],
    grid: { left: 46, right: 36, top: 34, bottom: 34 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: rows.map((row, index) => formatShortDate(row.date || row.time, index + 1)),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisLabel: { color: '#64748b' }
    },
    yAxis: [
      { type: 'value', name: '均价', splitLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
      { type: 'value', name: '记录', splitLine: { show: false }, axisLabel: { color: '#a16207' } }
    ],
    series: [
      {
        name: '全国均价',
        type: 'line',
        smooth: true,
        symbolSize: 7,
        lineStyle: { width: 3 },
        areaStyle: { color: 'rgba(27, 111, 66, 0.12)' },
        data: rows.map((row) => Number(row.average_price ?? row.averagePrice ?? row.price ?? 0))
      },
      {
        name: '采集记录',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: 12,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        data: rows.map((row) => Number(row.record_count ?? row.recordCount ?? 0))
      }
    ]
  }
}

const buildCategoryOption = () => ({
  color: ['#1b6f42', '#238b54', '#d99b2b', '#8b5cf6', '#94a3b8'],
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, itemWidth: 10, itemHeight: 10, textStyle: { color: '#64748b' } },
  series: [
    {
      type: 'pie',
      radius: ['48%', '70%'],
      center: ['50%', '44%'],
      label: { formatter: '{b}\n{d}%', color: '#334155', fontSize: 12 },
      itemStyle: { borderColor: '#fff', borderWidth: 3 },
      data: categoryStats.value
    }
  ]
})

const { setOption: setTrendOption } = useScreenChart(trendChartRef, buildTrendOption)
const { setOption: setCategoryOption } = useScreenChart(categoryChartRef, buildCategoryOption)

watch(trendRows, () => setTrendOption(), { deep: true })
watch(categoryStats, () => setCategoryOption(), { deep: true })

const loadDashboard = async () => {
  loading.value = true
  try {
    const [overview, realtimeData, trend, alerts] = await Promise.all([
      dashboardApi.overview(),
      dashboardApi.realtime(),
      dashboardApi.trend(),
      dashboardApi.alerts()
    ])
    metrics.value = (overview.cards || []).map((card, index) => ({
      label: card.label,
      value: formatNumber(card.value),
      change: card.change,
      trend: card.trend || 'up',
      icon: metricIcons[index] || TrendingUp
    }))
    realtime.value = realtimeData || {}
    trendRows.value = Array.isArray(trend) ? trend : []
    priceRows.value = normalizePriceRows(realtimeData)
    alertRows.value = normalizeAlerts(alerts)
    lastUpdatedAt.value = new Date()
  } catch {
    lastUpdatedAt.value = new Date()
  } finally {
    loading.value = false
  }
}

const normalizePriceRows = (realtimeData) => {
  const raw = realtimeData?.latestPrices
  const rows = Array.isArray(raw) ? raw : Array.isArray(raw?.items) ? raw.items : []
  if (!rows.length) return priceRows.value
  return rows.slice(0, 8).map((row, index) => ({
    product: row.product_name || row.productName || row.product || `农产品 ${index + 1}`,
    category: row.product_category || row.category || '重点监测',
    price: Number(row.mean_price || row.average_price || row.averagePrice || row.price || 0),
    recordCount: Number(row.record_count || row.recordCount || row.count || 0),
    regionCount: Number(row.region_count || row.regionCount || 0)
  }))
}

const normalizeAlerts = (alerts) => {
  const rows = Array.isArray(alerts) ? alerts : []
  if (!rows.length) return alertRows.value
  return rows.slice(0, 5).map((alert) => {
    const rate = Number(alert.change_rate ?? alert.changeRate ?? 0)
    const level = alert.level || (Math.abs(rate) >= 12 ? 'high' : Math.abs(rate) >= 8 ? 'medium' : 'low')
    return {
      name: `${alert.region || '全国'} ${alert.product_name || alert.product || '农产品'}`,
      detail: `${rate >= 0 ? '涨幅' : '跌幅'} ${Math.abs(rate).toFixed(1)}%`,
      level,
      status: alert.status || 'open'
    }
  })
}

const alertVariant = (level) => level === 'high' ? 'danger' : level === 'medium' ? 'warning' : 'outline'
const alertLevelText = (level) => level === 'high' ? '高' : level === 'medium' ? '中' : '低'
const formatNumber = (value) => Number(value || 0).toLocaleString('zh-CN')
const formatPrice = (value) => Number(value || 0) > 0 ? `¥${Number(value).toFixed(2)}` : '--'
const formatPercent = (value) => `${Number(value || 0).toFixed(1)}%`

onMounted(loadDashboard)
</script>

<template>
  <div class="space-y-6">
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div v-for="metric in metrics" :key="metric.label" class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-sm text-slate-500">{{ metric.label }}</p>
            <p class="mt-3 truncate text-2xl font-semibold text-slate-950">{{ metric.value }}</p>
          </div>
          <div class="flex h-10 w-10 items-center justify-center rounded-lg border bg-forest-50 text-forest-700">
            <component :is="metric.icon" class="h-5 w-5" />
          </div>
        </div>
        <div class="mt-4 flex items-center gap-1 text-sm">
          <ArrowUpRight v-if="metric.trend === 'up'" class="h-4 w-4 text-forest-600" />
          <ArrowDownRight v-else class="h-4 w-4 text-red-500" />
          <span :class="metric.trend === 'up' ? 'text-forest-700' : 'text-red-600'">{{ metric.change }}</span>
          <span class="text-slate-400">数据来源</span>
        </div>
      </div>
    </div>

    <section class="rounded-lg border bg-white p-5 shadow-panel">
      <div class="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        <div>
          <h2 class="text-base font-semibold text-slate-950">实时与入库链路</h2>
          <p class="mt-1 text-sm text-slate-500">Redis 实时缓存、MongoDB 最新入库、采集批次和价格均值状态</p>
        </div>
        <div class="flex items-center gap-2 text-sm text-slate-500">
          <Clock3 class="h-4 w-4 text-forest-600" />
          <span>{{ updatedText }}</span>
          <Button variant="secondary" size="sm" :disabled="loading" @click="loadDashboard">
            <RefreshCw :class="['h-4 w-4', loading && 'animate-spin']" />刷新
          </Button>
        </div>
      </div>
      <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div v-for="card in batchCards" :key="card.label" class="rounded-lg border bg-slate-50 p-4">
          <div class="flex items-center justify-between gap-3">
            <component :is="card.icon" class="h-5 w-5 text-forest-700" />
            <Badge variant="outline">{{ card.status }}</Badge>
          </div>
          <p class="mt-4 text-sm text-slate-500">{{ card.label }}</p>
          <p class="mt-1 text-xl font-semibold text-slate-950">{{ card.value }}</p>
        </div>
      </div>
    </section>

    <div class="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold text-slate-950">全国价格指数趋势</h2>
            <p class="mt-1 text-sm text-slate-500">均价走势与采集记录联动展示</p>
          </div>
          <BarChart3 class="h-5 w-5 text-forest-700" />
        </div>
        <div ref="trendChartRef" class="h-80 w-full rounded-lg border bg-slate-50" />
      </section>

      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold text-slate-950">产品类型构成</h2>
            <p class="mt-1 text-sm text-slate-500">按最新可用价格记录聚合</p>
          </div>
          <Sprout class="h-5 w-5 text-forest-700" />
        </div>
        <div ref="categoryChartRef" class="h-80 w-full rounded-lg border bg-slate-50" />
      </section>
    </div>

    <div class="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold text-slate-950">重点农产品最新价格</h2>
            <p class="mt-1 text-sm text-slate-500">优先来自 Redis 实时价格，无缓存时来自 MongoDB 最新入库数据</p>
          </div>
          <Database class="h-5 w-5 text-forest-700" />
        </div>
        <div class="overflow-hidden rounded-lg border">
          <div class="grid grid-cols-[1.1fr_0.9fr_0.8fr_0.8fr_0.8fr] bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-500">
            <span>品类</span><span>类型</span><span>均价</span><span>记录数</span><span>覆盖区域</span>
          </div>
          <div class="divide-y">
            <div v-for="(row, index) in priceRows" :key="`${row.product}-${row.category}-${index}`" class="grid grid-cols-[1.1fr_0.9fr_0.8fr_0.8fr_0.8fr] px-4 py-3 text-sm">
              <span class="font-medium text-slate-900">{{ row.product }}</span>
              <span class="text-slate-500">{{ row.category }}</span>
              <span class="font-semibold text-forest-700">{{ formatPrice(row.price) }}</span>
              <span class="text-slate-600">{{ formatNumber(row.recordCount) }}</span>
              <span class="text-slate-600">{{ row.regionCount || '--' }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold text-slate-950">预警摘要</h2>
            <p class="mt-1 text-sm text-slate-500">高风险价格波动和质量异常</p>
          </div>
          <ShieldCheck class="h-5 w-5 text-forest-700" />
        </div>
        <div class="space-y-3">
          <div v-for="alert in alertRows" :key="`${alert.name}-${alert.detail}`" class="flex items-center justify-between rounded-lg border bg-white px-4 py-3">
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-slate-900">{{ alert.name }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ alert.detail }} · {{ alert.status }}</p>
            </div>
            <Badge :variant="alertVariant(alert.level)">{{ alertLevelText(alert.level) }}</Badge>
          </div>
        </div>
      </section>
    </div>

    <section class="rounded-lg border bg-white p-5 shadow-panel">
      <div class="mb-4">
        <h2 class="text-base font-semibold text-slate-950">采集质量管控</h2>
        <p class="mt-1 text-sm text-slate-500">采集、清洗、入库和预警闭环关键质量指标</p>
      </div>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div v-for="item in qualityItems" :key="item.label" class="rounded-lg border bg-slate-50 p-4">
          <div class="flex items-center justify-between text-sm">
            <span class="font-medium text-slate-700">{{ item.label }}</span>
            <span class="font-semibold text-slate-950">{{ formatPercent(item.value) }}</span>
          </div>
          <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
            <div :class="['h-full rounded-full', item.color]" :style="{ width: `${item.value}%` }" />
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
