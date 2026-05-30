<script setup>
import { ArrowDownRight, ArrowUpRight, Database, ServerCog, Sprout, TrendingUp } from 'lucide-vue-next'
import Badge from '../ui/Badge.vue'

const metrics = [
  { label: '今日采集记录', value: '126,840', change: '+12.4%', trend: 'up', icon: Database },
  { label: '覆盖市场主体', value: '1,528', change: '+36', trend: 'up', icon: ServerCog },
  { label: '重点农产品', value: '512', change: '+18', trend: 'up', icon: Sprout },
  { label: '异常波动预警', value: '24', change: '-8.1%', trend: 'down', icon: TrendingUp }
]

const alertItems = [
  ['山东 番茄', '涨幅 18.6%', 'warning'],
  ['四川 玉米', '缺失率 4.1%', 'outline'],
  ['河南 苹果', '跌幅 12.2%', 'danger']
]
</script>

<template>
  <div class="space-y-6">
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div v-for="metric in metrics" :key="metric.label" class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-sm text-slate-500">{{ metric.label }}</p>
            <p class="mt-3 text-2xl font-semibold text-slate-950">{{ metric.value }}</p>
          </div>
          <div class="flex h-10 w-10 items-center justify-center rounded-lg border bg-forest-50 text-forest-700">
            <component :is="metric.icon" class="h-5 w-5" />
          </div>
        </div>
        <div class="mt-4 flex items-center gap-1 text-sm">
          <ArrowUpRight v-if="metric.trend === 'up'" class="h-4 w-4 text-forest-600" />
          <ArrowDownRight v-else class="h-4 w-4 text-red-500" />
          <span :class="metric.trend === 'up' ? 'text-forest-700' : 'text-red-600'">{{ metric.change }}</span>
          <span class="text-slate-400">较上一批次</span>
        </div>
      </div>
    </div>

    <div class="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4">
          <h2 class="text-base font-semibold text-slate-950">全国价格指数趋势</h2>
          <p class="mt-1 text-sm text-slate-500">ECharts 折线图区域，后续接入 /api/price-trends</p>
        </div>
        <div class="flex h-80 items-end gap-2 rounded-lg border bg-slate-50 p-5">
          <div v-for="(height, index) in [42, 48, 44, 58, 62, 57, 66, 73, 69, 78, 86, 82]" :key="index" class="flex flex-1 flex-col items-center justify-end gap-2">
            <div class="w-full rounded-t-sm bg-forest-600" :style="{ height: `${height}%` }" />
            <span class="text-xs text-slate-400">{{ index + 1 }}</span>
          </div>
        </div>
      </section>

      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4">
          <h2 class="text-base font-semibold text-slate-950">预警优先级</h2>
          <p class="mt-1 text-sm text-slate-500">高风险价格波动、采集失败和质量异常统一收敛</p>
        </div>
        <div class="space-y-3">
          <div v-for="[name, detail, variant] in alertItems" :key="name" class="flex items-center justify-between rounded-lg border bg-white px-4 py-3">
            <div>
              <p class="text-sm font-medium text-slate-900">{{ name }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ detail }}</p>
            </div>
            <Badge :variant="variant">{{ variant === 'danger' ? '高' : variant === 'warning' ? '中' : '低' }}</Badge>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>