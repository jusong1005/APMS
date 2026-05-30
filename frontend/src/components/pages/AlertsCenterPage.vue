<script setup>
import { computed, ref } from 'vue'
import { AlertTriangle, BellRing, CheckCircle2, Clock3, Eye, Flame, RadioTower, Settings2, ShieldAlert, Siren, TrendingUp } from 'lucide-vue-next'
import Badge from '../ui/Badge.vue'
import Button from '../ui/Button.vue'

const rules = [
  {
    id: 'rule-pork-rise',
    name: '猪肉价格快速上涨',
    condition: '当猪肉价格上涨超过 15% 时触发推送',
    product: '猪肉',
    threshold: '涨幅 > 15%',
    channel: '短信 + 站内通知',
    level: 'high',
    enabled: true
  },
  {
    id: 'rule-vegetable-spike',
    name: '重点蔬菜异常波动',
    condition: '当大白菜、番茄等重点品类 24 小时涨跌超过 12% 时进入处置队列',
    product: '蔬菜品类',
    threshold: '涨跌幅 > 12%',
    channel: '站内通知',
    level: 'medium',
    enabled: true
  },
  {
    id: 'rule-collection-missing',
    name: '采集数据缺失预警',
    condition: '当核心市场连续 3 个采集周期无数据回传时触发核查',
    product: '核心市场',
    threshold: '连续缺失 3 次',
    channel: '邮件 + 站内通知',
    level: 'medium',
    enabled: true
  }
]

const records = [
  {
    id: 'A-20260530-001',
    time: '09:18:42',
    title: '猪肉价格上涨超过 15%',
    detail: '北京新发地、郑州万邦和成都白家市场猪肉均价较昨日上涨 16.8%，超过高风险阈值。',
    scope: '华北、华中、西南 3 个区域，12 个市场主体',
    status: 'processing',
    level: 'high',
    owner: '价格监测一组'
  },
  {
    id: 'A-20260530-002',
    time: '08:47:15',
    title: '山东番茄价格进入观察区间',
    detail: '寿光蔬菜行情采集显示番茄批发价 24 小时上涨 12.4%，建议持续跟踪供应端变化。',
    scope: '山东省 5 个批发市场',
    status: 'read',
    level: 'medium',
    owner: '区域运营岗'
  },
  {
    id: 'A-20260529-018',
    time: '昨日 22:36:09',
    title: '华东批发市场补采任务中断',
    detail: '补采任务连续 3 个周期未回传数据，已自动生成数据源连通性核查工单。',
    scope: '华东区域批发市场联盟',
    status: 'closed',
    level: 'medium',
    owner: '采集运维岗'
  },
  {
    id: 'A-20260529-015',
    time: '昨日 18:20:51',
    title: '鸡蛋价格预测突破预警线',
    detail: '趋势预测模型显示未来 7 天鸡蛋均价可能突破 11.20 元/公斤，需提前关注库存。',
    scope: '北京、河南、四川 3 个重点区域',
    status: 'processing',
    level: 'high',
    owner: '预测分析岗'
  }
]

const statusTabs = [
  { value: 'all', label: '全部' },
  { value: 'processing', label: '处理中' },
  { value: 'read', label: '已阅' },
  { value: 'closed', label: '已关闭' }
]

const levelMeta = {
  high: { label: '高风险', className: 'border-red-200 bg-red-50 text-red-700', icon: Siren },
  medium: { label: '中风险', className: 'border-amber-200 bg-amber-50 text-amber-800', icon: AlertTriangle }
}

const statusMeta = {
  processing: { label: '处理中', className: 'border-red-200 bg-red-50 text-red-700', icon: Clock3 },
  read: { label: '已阅', className: 'border-amber-200 bg-amber-50 text-amber-800', icon: Eye },
  closed: { label: '已关闭', className: 'border-forest-100 bg-forest-50 text-forest-700', icon: CheckCircle2 }
}

const activeStatus = ref('all')

const summary = computed(() => ({
  high: records.filter((item) => item.level === 'high').length,
  processing: records.filter((item) => item.status === 'processing').length,
  closed: records.filter((item) => item.status === 'closed').length
}))

const filteredRecords = computed(() => {
  if (activeStatus.value === 'all') return records
  return records.filter((item) => item.status === activeStatus.value)
})
</script>

<template>
  <div class="space-y-4">
    <section class="overflow-hidden rounded-lg border border-red-200 bg-white shadow-panel">
      <div class="border-b border-red-100 bg-gradient-to-r from-red-50 via-amber-50 to-white p-5">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex items-start gap-3">
            <span class="flex h-12 w-12 items-center justify-center rounded-lg border border-red-200 bg-white text-red-600 shadow-sm">
              <ShieldAlert class="h-6 w-6" />
            </span>
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <h2 class="text-base font-semibold text-red-950">实时价格风险态势</h2>
                <Badge variant="danger">紧急监控</Badge>
              </div>
              <p class="mt-1 text-sm leading-6 text-red-700">高风险预警优先推送到责任岗，处理中记录会持续保留在时间轴顶部。</p>
            </div>
          </div>
          <div class="grid gap-2 sm:grid-cols-3 lg:min-w-[420px]">
            <div class="rounded-lg border border-red-200 bg-white px-4 py-3">
              <p class="text-xs text-red-500">高风险预警</p>
              <p class="mt-1 text-xl font-semibold text-red-700">{{ summary.high }}</p>
            </div>
            <div class="rounded-lg border border-amber-200 bg-white px-4 py-3">
              <p class="text-xs text-amber-600">处理中</p>
              <p class="mt-1 text-xl font-semibold text-amber-700">{{ summary.processing }}</p>
            </div>
            <div class="rounded-lg border border-forest-100 bg-white px-4 py-3">
              <p class="text-xs text-forest-600">已关闭</p>
              <p class="mt-1 text-xl font-semibold text-forest-700">{{ summary.closed }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="grid gap-4 xl:grid-cols-[0.95fr_1.35fr]">
      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4 flex items-start justify-between gap-3">
          <div>
            <div class="flex items-center gap-2">
              <Settings2 class="h-5 w-5 text-amber-600" />
              <h2 class="text-base font-semibold text-slate-950">预警规则设置</h2>
            </div>
            <p class="mt-1 text-sm text-slate-500">配置价格阈值、触发条件和通知渠道。</p>
          </div>
          <Button variant="secondary"><BellRing class="h-4 w-4" />新增规则</Button>
        </div>

        <div class="space-y-3">
          <article v-for="rule in rules" :key="rule.id" class="rounded-lg border bg-slate-50 p-4 transition-colors hover:bg-white">
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <h3 class="text-sm font-semibold text-slate-950">{{ rule.name }}</h3>
                  <span :class="['rounded-md border px-2 py-0.5 text-xs font-medium', levelMeta[rule.level].className]">{{ levelMeta[rule.level].label }}</span>
                </div>
                <p class="mt-2 text-sm leading-6 text-slate-600">{{ rule.condition }}</p>
              </div>
              <label class="relative inline-flex cursor-pointer items-center">
                <input type="checkbox" class="peer sr-only" :checked="rule.enabled" />
                <span class="h-5 w-9 rounded-full bg-slate-200 after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-all peer-checked:bg-red-500 peer-checked:after:translate-x-4" />
              </label>
            </div>
            <div class="mt-4 grid gap-2 text-xs text-slate-500 sm:grid-cols-3">
              <div class="rounded-md border bg-white px-3 py-2"><span class="block text-slate-400">监控对象</span><span class="mt-1 block font-medium text-slate-700">{{ rule.product }}</span></div>
              <div class="rounded-md border bg-white px-3 py-2"><span class="block text-slate-400">触发阈值</span><span class="mt-1 block font-medium text-red-700">{{ rule.threshold }}</span></div>
              <div class="rounded-md border bg-white px-3 py-2"><span class="block text-slate-400">通知渠道</span><span class="mt-1 block font-medium text-slate-700">{{ rule.channel }}</span></div>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="mb-4 flex flex-col justify-between gap-3 lg:flex-row lg:items-center">
          <div>
            <div class="flex items-center gap-2">
              <RadioTower class="h-5 w-5 text-red-600" />
              <h2 class="text-base font-semibold text-slate-950">历史预警记录</h2>
            </div>
            <p class="mt-1 text-sm text-slate-500">按时间倒序展示触发详情、受影响范围和当前状态。</p>
          </div>
          <div class="flex rounded-md border bg-slate-50 p-1">
            <button
              v-for="tab in statusTabs"
              :key="tab.value"
              :class="['h-8 rounded-sm px-3 text-sm font-medium transition-colors', activeStatus === tab.value ? 'bg-white text-red-700 shadow-sm' : 'text-slate-500 hover:text-slate-900']"
              @click="activeStatus = tab.value"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>

        <div class="relative space-y-4 before:absolute before:left-5 before:top-2 before:h-[calc(100%-16px)] before:w-px before:bg-gradient-to-b before:from-red-300 before:via-amber-200 before:to-slate-200">
          <article v-for="record in filteredRecords" :key="record.id" class="relative pl-14">
            <span :class="['absolute left-0 top-1 flex h-10 w-10 items-center justify-center rounded-full border-4 border-white shadow-sm', record.level === 'high' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700']">
              <component :is="levelMeta[record.level].icon" class="h-5 w-5" />
            </span>
            <div :class="['rounded-lg border p-4', record.level === 'high' ? 'border-red-200 bg-red-50/70' : 'border-amber-200 bg-amber-50/70']">
              <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div class="flex flex-wrap items-center gap-2">
                    <h3 class="text-sm font-semibold text-slate-950">{{ record.title }}</h3>
                    <span :class="['inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium', statusMeta[record.status].className]">
                      <component :is="statusMeta[record.status].icon" class="h-3.5 w-3.5" />
                      {{ statusMeta[record.status].label }}
                    </span>
                  </div>
                  <p class="mt-2 text-sm leading-6 text-slate-700">{{ record.detail }}</p>
                </div>
                <div class="shrink-0 rounded-md border bg-white px-3 py-2 text-right text-xs text-slate-500">
                  <div>{{ record.time }}</div>
                  <div class="mt-1 font-medium text-slate-700">{{ record.id }}</div>
                </div>
              </div>
              <div class="mt-4 grid gap-2 sm:grid-cols-2">
                <div class="rounded-md border bg-white px-3 py-2">
                  <div class="flex items-center gap-2 text-xs text-slate-400"><Flame class="h-3.5 w-3.5 text-red-500" />受影响范围</div>
                  <p class="mt-1 text-sm font-medium text-slate-700">{{ record.scope }}</p>
                </div>
                <div class="rounded-md border bg-white px-3 py-2">
                  <div class="flex items-center gap-2 text-xs text-slate-400"><TrendingUp class="h-3.5 w-3.5 text-amber-600" />责任处理岗</div>
                  <p class="mt-1 text-sm font-medium text-slate-700">{{ record.owner }}</p>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>