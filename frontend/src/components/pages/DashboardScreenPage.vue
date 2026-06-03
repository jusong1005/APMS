<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { LayoutDashboard } from 'lucide-vue-next'
import CategoryRings from '../dashboard-screen/CategoryRings.vue'
import ChinaMarketMap from '../dashboard-screen/ChinaMarketMap.vue'
import FruitTrendChart from '../dashboard-screen/FruitTrendChart.vue'
import GrainRankingChart from '../dashboard-screen/GrainRankingChart.vue'
import MeatTradeList from '../dashboard-screen/MeatTradeList.vue'
import MerchantScaleChart from '../dashboard-screen/MerchantScaleChart.vue'
import ProductDoughnutChart from '../dashboard-screen/ProductDoughnutChart.vue'
import RealtimeQuoteList from '../dashboard-screen/RealtimeQuoteList.vue'
import { analysisApi, dashboardApi } from '../../lib/api'

const emit = defineEmits(['exit-screen'])

const screenScale = ref(1)
const now = ref(new Date())
const loading = ref(false)

const categoryMetrics = ref([
  { label: '蔬菜', value: 150, percent: 86, color: '#10b981' },
  { label: '水果', value: 60, percent: 68, color: '#4ade80' },
  { label: '粮食', value: 50, percent: 58, color: '#f59e0b' },
  { label: '畜禽', value: 68, percent: 74, color: '#c4b5fd' }
])
const productComposition = ref([
  { name: '种植业产品', value: 150, color: '#10b981' },
  { name: '渔业产品', value: 50, color: '#d1d5db' },
  { name: '畜牧业产品', value: 20, color: '#f59e0b' }
])
const vegetableQuotes = ref([
  { name: '番茄', region: '山东寿光', price: 4.8, change: 2.6 },
  { name: '大白菜', region: '北京新发地', price: 2.1, change: -1.2 },
  { name: '黄瓜', region: '河南郑州', price: 3.7, change: 1.8 },
  { name: '土豆', region: '四川成都', price: 2.9, change: 0.7 },
  { name: '辣椒', region: '湖南长沙', price: 5.6, change: 3.4 },
  { name: '生菜', region: '上海江桥', price: 4.2, change: -0.8 }
])
const marketPoints = ref([
  { name: '北京', lng: 116.4, lat: 39.9, count: 86 },
  { name: '山东', lng: 117.0, lat: 36.7, count: 112 },
  { name: '河南', lng: 113.6, lat: 34.8, count: 92 },
  { name: '四川', lng: 104.1, lat: 30.7, count: 78 },
  { name: '广东', lng: 113.3, lat: 23.1, count: 105 },
  { name: '江苏', lng: 118.8, lat: 32.1, count: 88 },
  { name: '浙江', lng: 120.2, lat: 30.3, count: 76 },
  { name: '云南', lng: 102.7, lat: 25.0, count: 64 },
  { name: '陕西', lng: 108.9, lat: 34.3, count: 58 }
])
const fruitTrend = ref([
  { label: '08-10', price: 18, attention: 28 },
  { label: '08-12', price: 16, attention: 24 },
  { label: '08-14', price: 22, attention: 31 },
  { label: '08-16', price: 19, attention: 27 },
  { label: '08-18', price: 26, attention: 38 },
  { label: '08-20', price: 42, attention: 34 },
  { label: '08-22', price: 31, attention: 56 },
  { label: '08-24', price: 35, attention: 92 }
])
const merchantScale = ref([
  { range: '0-1万', wholesale: 520, retail: 1260 },
  { range: '1-3万', wholesale: 1880, retail: 2450 },
  { range: '3-5万', wholesale: 2955, retail: 784 },
  { range: '5-8万', wholesale: 960, retail: 420 },
  { range: '8-11万', wholesale: 420, retail: 210 },
  { range: '11万+', wholesale: 180, retail: 120 }
])
const fallbackGrainRanking = [
  { name: '玉米', value: 6.6 },
  { name: '小麦', value: 6.2 },
  { name: '大米', value: 5.8 },
  { name: '大豆', value: 5.4 },
  { name: '高粱', value: 4.9 },
  { name: '小米', value: 4.6 },
  { name: '荞麦', value: 4.2 },
  { name: '绿豆', value: 3.8 },
  { name: '红薯', value: 6.62 },
  { name: '糯米', value: 3.4 },
  { name: '红豆', value: 3.1 },
  { name: '燕麦', value: 2.8 }
]
const grainRanking = ref(fallbackGrainRanking.slice(0, 8))
const meatDeals = ref([
  { name: '牛腩', market: '成都白家', price: 28, change: 1.2 },
  { name: '猪肉', market: '北京新发地', price: 15, change: -0.6 },
  { name: '羊肉', market: '郑州万邦', price: 31, change: 0.9 },
  { name: '鸡胸肉', market: '山东寿光', price: 9.8, change: -1.4 },
  { name: '牛腱', market: '广州江南', price: 33, change: 2.1 },
  { name: '鸭腿', market: '杭州勾庄', price: 8.6, change: 0.4 }
])

const clockText = computed(() => new Intl.DateTimeFormat('zh-CN', {
  weekday: 'short',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false
}).format(now.value))

const chartOptionHook = (option) => option

const regionCoordinates = {
  北京: [116.4, 39.9], 山东: [117.0, 36.7], 河南: [113.6, 34.8], 四川: [104.1, 30.7], 广东: [113.3, 23.1], 江苏: [118.8, 32.1], 浙江: [120.2, 30.3], 云南: [102.7, 25.0], 陕西: [108.9, 34.3], 上海: [121.5, 31.2], 湖南: [112.9, 28.2], 湖北: [114.3, 30.6]
}

let clockTimer
let refreshTimer

const updateScale = () => {
  const widthScale = window.innerWidth / 1920
  const heightScale = window.innerHeight / 1080
  screenScale.value = Math.min(widthScale, heightScale)
}

const asNumber = (value, fallback = 0) => Number.isFinite(Number(value)) ? Number(value) : fallback

const normalizePriceRows = (realtime) => {
  const latestPrices = realtime?.latestPrices
  if (Array.isArray(latestPrices)) return latestPrices
  if (Array.isArray(latestPrices?.items)) return latestPrices.items
  return []
}

const isGrainProduct = (item) => /粮|谷|米|麦|豆|玉米|小麦|大米|大豆|高粱|小米|荞麦|燕麦|糯米|绿豆|红豆|红薯|马铃薯|花生|芝麻/.test(`${item.category}${item.name}`)

const normalizeGrainName = (name) => {
  const text = String(name || '')
  const matched = ['玉米', '小麦', '大米', '大豆', '高粱', '小米', '荞麦', '燕麦', '糯米', '绿豆', '红豆', '红薯', '马铃薯', '花生', '芝麻'].find((keyword) => text.includes(keyword))
  return matched || text.replace(/(价格|均价|批发|指数|类)$/g, '') || '粮食品类'
}

const roundPercent = (value) => Math.round(Number(value || 0) * 10) / 10

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

const buildGrainRanking = (mappedRows) => {
  const merged = new Map()
  mappedRows.filter(isGrainProduct).forEach((item, index) => {
    const name = normalizeGrainName(item.name)
    const value = roundPercent(Math.abs(item.change) + 1 + index * 0.36)
    const current = merged.get(name)
    if (!current || value > current.value) merged.set(name, { name, value })
  })
  fallbackGrainRanking.forEach((item) => {
    if (!merged.has(item.name)) merged.set(item.name, item)
  })
  return Array.from(merged.values()).sort((left, right) => right.value - left.value).slice(0, 8)
}

const updateCategoryMetrics = (overviewData, productStats = []) => {
  if (Array.isArray(productStats) && productStats.length) {
    const categoryGroups = [
      { label: '蔬菜', pattern: /蔬菜|菜/, color: '#10b981' },
      { label: '水果', pattern: /水果|果/, color: '#4ade80' },
      { label: '粮食', pattern: /粮食|粮|谷|米|麦|豆|玉米|小麦|大米|大豆|高粱|小米|荞麦/, color: '#f59e0b' },
      { label: '畜禽', pattern: /畜|禽|肉|蛋|猪|牛|羊|鸡|鸭/, color: '#c4b5fd' }
    ]
    const values = categoryGroups.map((group) => productStats
      .filter((item) => group.pattern.test(`${item.product_category || ''}${item.product_name || ''}`))
      .reduce((sum, item) => sum + asNumber(item.record_count || item.recordCount, 0), 0))
    const total = values.reduce((sum, value) => sum + value, 0) || asNumber(overviewData?.collectionRecords || overviewData?.cards?.[0]?.value, 0)
    if (total > 0) {
      categoryMetrics.value = categoryGroups.map((group, index) => ({
        label: group.label,
        value: values[index],
        percent: Math.round((values[index] / total) * 100),
        color: group.color
      }))
      return
    }
  }
  const total = asNumber(overviewData?.collectionRecords || overviewData?.cards?.[0]?.value, 328)
  categoryMetrics.value = [
    { label: '蔬菜', value: Math.round(total * 0.46), percent: 86, color: '#10b981' },
    { label: '水果', value: Math.round(total * 0.22), percent: 68, color: '#4ade80' },
    { label: '粮食', value: Math.round(total * 0.16), percent: 58, color: '#f59e0b' },
    { label: '畜禽', value: Math.round(total * 0.20), percent: 74, color: '#c4b5fd' }
  ]
}

const updateComposition = (priceRows) => {
  if (!priceRows.length) return
  const planting = priceRows.filter((item) => /蔬菜|水果|粮食|种植/.test(item.product_category || item.category || '')).length || 1
  const fishery = priceRows.filter((item) => /渔|水产/.test(item.product_category || item.category || '')).length || Math.max(1, Math.round(priceRows.length * 0.16))
  const livestock = priceRows.filter((item) => /畜|肉|禽|蛋/.test(item.product_category || item.category || '')).length || Math.max(1, Math.round(priceRows.length * 0.22))
  productComposition.value = [
    { name: '种植业产品', value: planting * 30, color: '#10b981' },
    { name: '渔业产品', value: fishery * 10, color: '#d1d5db' },
    { name: '畜牧业产品', value: livestock * 12, color: '#f59e0b' }
  ]
}

const updateLists = (priceRows) => {
  if (!priceRows.length) return
  const mappedRows = priceRows.map((item, index) => ({
    name: item.product_name || item.productName || item.product || `农产品${index + 1}`,
    region: item.region || ['山东寿光', '北京新发地', '河南郑州', '四川成都'][index % 4],
    market: item.market_name || item.marketName || ['新发地', '寿光市场', '万邦市场', '白家市场'][index % 4],
    category: item.product_category || item.category || '',
    price: asNumber(item.mean_price || item.average_price || item.averagePrice || item.price, 2.8 + index),
    change: asNumber(item.change_rate || item.changeRate, (index % 2 === 0 ? 1 : -1) * (0.8 + index * 0.4))
  }))
  vegetableQuotes.value = mappedRows.filter((item) => /蔬菜|菜|番茄|白菜|黄瓜|土豆|辣椒|生菜/.test(`${item.category}${item.name}`)).slice(0, 8)
  if (!vegetableQuotes.value.length) vegetableQuotes.value = mappedRows.slice(0, 6)
  meatDeals.value = mappedRows.filter((item) => /畜|肉|禽|蛋|猪|牛|羊|鸡|鸭/.test(`${item.category}${item.name}`)).slice(0, 8)
  if (!meatDeals.value.length) meatDeals.value = mappedRows.slice(0, 6).map((item, index) => ({ ...item, name: ['猪肉', '牛腩', '羊肉', '鸡胸肉', '鸭腿', '牛腱'][index % 6] }))
  grainRanking.value = buildGrainRanking(mappedRows)
}

const updateTrend = (trendRows) => {
  if (!Array.isArray(trendRows) || !trendRows.length) return
  fruitTrend.value = trendRows.slice(-8).map((item, index) => ({
    label: formatShortDate(item.date || item.time, `T-${7 - index}`),
    price: asNumber(item.average_price || item.averagePrice || item.price, 0),
    attention: Math.round(asNumber(item.record_count || item.recordCount, 20) / 18) + 20 + index * 4
  }))
}

const updateMap = (alerts) => {
  if (!Array.isArray(alerts) || !alerts.length) return
  const grouped = new Map()
  alerts.forEach((alert) => {
    const region = alert.region || '山东'
    const coordinates = regionCoordinates[region]
    if (!coordinates) return
    grouped.set(region, (grouped.get(region) || 48) + Math.abs(asNumber(alert.change_rate || alert.changeRate, 6)) * 4)
  })
  if (!grouped.size) return
  marketPoints.value = Array.from(grouped.entries()).map(([name, count]) => ({ name, lng: regionCoordinates[name][0], lat: regionCoordinates[name][1], count: Math.round(count) }))
}

const loadDashboard = async () => {
  loading.value = true
  try {
    const [overviewData, realtimeData, trendData, alertData, productStats] = await Promise.all([
      dashboardApi.overview(),
      dashboardApi.realtime(),
      dashboardApi.trend(),
      dashboardApi.alerts(),
      analysisApi.productStatistics()
    ])
    const priceRows = normalizePriceRows(realtimeData)
    updateCategoryMetrics(overviewData, productStats)
    updateComposition(priceRows)
    updateLists(priceRows)
    updateTrend(trendData)
    updateMap(alertData)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  updateScale()
  loadDashboard()
  clockTimer = window.setInterval(() => {
    now.value = new Date()
  }, 1000)
  refreshTimer = window.setInterval(loadDashboard, 30000)
  window.addEventListener('resize', updateScale)
})

onUnmounted(() => {
  window.clearInterval(clockTimer)
  window.clearInterval(refreshTimer)
  window.removeEventListener('resize', updateScale)
})
</script>

<template>
  <div class="agri-screen-root">
    <div class="agri-screen-stage" :style="{ transform: `translate(-50%, -50%) scale(${screenScale})` }">
      <header class="agri-screen-header">
        <button class="screen-workbench-button" title="返回工作台" @click="emit('exit-screen')">
          <LayoutDashboard class="h-5 w-5" />
          <span>工作台</span>
        </button>
        <div class="header-line header-line--left" />
        <h1>AgriPulse 农产品价格采集监控大盘</h1>
        <div class="header-line header-line--right" />
        <time>{{ clockText }}</time>
      </header>

      <main class="agri-screen-grid">
        <aside class="screen-column screen-column--left">
          <CategoryRings :data="categoryMetrics" :option-hook="chartOptionHook" />
          <ProductDoughnutChart :data="productComposition" :option-hook="chartOptionHook" />
          <RealtimeQuoteList :data="vegetableQuotes" />
        </aside>

        <section class="screen-column screen-column--middle">
          <ChinaMarketMap :data="marketPoints" :option-hook="chartOptionHook" />
          <FruitTrendChart :data="fruitTrend" :option-hook="chartOptionHook" />
        </section>

        <aside class="screen-column screen-column--right">
          <MerchantScaleChart :data="merchantScale" :option-hook="chartOptionHook" />
          <GrainRankingChart :data="grainRanking" :option-hook="chartOptionHook" />
          <MeatTradeList :data="meatDeals" />
        </aside>
      </main>
    </div>
  </div>
</template>

<style scoped>
.agri-screen-root {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0, rgba(16, 185, 129, 0) 38%),
    radial-gradient(circle at 50% 38%, rgba(74, 222, 128, 0.1), transparent 42%),
    linear-gradient(180deg, #042f24 0%, #011a13 100%);
}

.agri-screen-root::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0.18;
  background-image:
    linear-gradient(rgba(74, 222, 128, 0.18) 1px, transparent 1px),
    linear-gradient(90deg, rgba(74, 222, 128, 0.14) 1px, transparent 1px);
  background-size: 48px 48px;
}

.agri-screen-root::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(180deg, transparent 0, rgba(255, 255, 255, 0.035) 50%, transparent 100%);
  background-size: 100% 6px;
  mix-blend-mode: screen;
}

.agri-screen-stage {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 1920px;
  height: 1080px;
  transform-origin: center center;
  color: #ecfdf5;
}

.agri-screen-header {
  position: relative;
  display: grid;
  grid-template-columns: 360px 1fr auto 1fr 360px;
  align-items: center;
  height: 92px;
  padding: 18px 28px 12px;
}

.screen-workbench-button {
  display: inline-flex;
  width: max-content;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(74, 222, 128, 0.28);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(236, 253, 245, 0.82);
  padding: 9px 14px;
  font-weight: 700;
  cursor: pointer;
  clip-path: polygon(0 8px, 8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%);
}

.screen-workbench-button:hover {
  border-color: rgba(74, 222, 128, 0.62);
  color: #ecfdf5;
}

.agri-screen-header h1 {
  margin: 0;
  color: #ecfdf5;
  font-size: 38px;
  font-weight: 900;
  letter-spacing: 0;
  text-align: center;
  text-shadow: 0 0 22px rgba(74, 222, 128, 0.42);
}

.agri-screen-header time {
  justify-self: end;
  color: rgba(236, 253, 245, 0.82);
  font-size: 18px;
  font-variant-numeric: tabular-nums;
}

.header-line {
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(74, 222, 128, 0.9));
  box-shadow: 0 0 18px rgba(74, 222, 128, 0.42);
}

.header-line--right {
  background: linear-gradient(90deg, rgba(74, 222, 128, 0.9), transparent);
}

.agri-screen-grid {
  display: grid;
  grid-template-columns: 540px 780px 540px;
  gap: 20px;
  height: 968px;
  padding: 0 22px 22px;
}

.screen-column {
  display: grid;
  min-height: 0;
  gap: 20px;
}

.screen-column--left {
  grid-template-rows: 232px 302px minmax(0, 1fr);
}

.screen-column--middle {
  grid-template-rows: 616px minmax(0, 1fr);
}

.screen-column--right {
  grid-template-rows: 286px 326px minmax(0, 1fr);
}
</style>
