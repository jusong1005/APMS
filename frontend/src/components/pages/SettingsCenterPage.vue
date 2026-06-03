<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ActivitySquare,
  AlertTriangle,
  Database,
  FileClock,
  Globe2,
  RotateCcw,
  Save,
  ShieldCheck,
  SlidersHorizontal,
  Trash2,
  Zap
} from 'lucide-vue-next'
import { settingsApi } from '../../lib/api'

const activeSection = ref('global')
const dirtyFields = ref({})

const sections = [
  { key: 'global', label: '全局配置', icon: Globe2 },
  { key: 'crawler', label: '采集引擎参数', icon: SlidersHorizontal },
  { key: 'quality', label: '质量校验阈值', icon: ShieldCheck },
  { key: 'database', label: '数据库状态', icon: Database },
  { key: 'audit', label: '审计日志', icon: FileClock }
]

const globalConfig = reactive({
  siteName: 'AgriPulse 农产品价格采集监控平台',
  apiPrefix: '/api/v1/agri-price',
  maintenanceMode: false,
  refreshRate: '1min'
})

const crawlerConfig = reactive({
  retryCount: 3,
  timeoutMs: '8000',
  concurrency: 18,
  userAgents: [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AgriPulse/1.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 AgriPulse/1.0',
    'AgriPulseCrawler/1.0 (+https://agripulse.local/monitor)'
  ].join('\n')
})

const qualityConfig = reactive({
  abnormalWavePercent: 20,
  missingTolerance: 3,
  autoClean: true
})

const dangerDialog = reactive({
  visible: false,
  title: '',
  message: '',
  success: ''
})

const refreshOptions = [
  { label: '30s', value: '30s' },
  { label: '1min', value: '1min' },
  { label: '5min', value: '5min' }
]

const databaseStatus = ref([
  { name: 'MongoDB', role: '生产行情库', status: 'connected', latency: '18 ms', endpoint: 'agri_price' },
  { name: 'Redis', role: '热点缓存库', status: 'connected', latency: '3 ms', endpoint: '127.0.0.1:6379' }
])

const auditLogs = ref([
  { time: '2026-05-30 09:28:16', operator: 'admin', action: '更新异常价格波动阈值', ip: '10.24.18.32' },
  { time: '2026-05-30 09:12:04', operator: 'ops_chen', action: '开启自动清洗开关', ip: '10.24.18.77' },
  { time: '2026-05-29 22:45:51', operator: 'data_li', action: '调整采集并发限制', ip: '10.24.20.16' },
  { time: '2026-05-29 20:10:39', operator: 'admin', action: '刷新 User-Agent 池', ip: '10.24.18.32' },
  { time: '2026-05-29 18:33:20', operator: 'model_wang', action: '重置趋势预测模型', ip: '10.24.21.90' }
])

const dirtyCount = computed(() => Object.values(dirtyFields.value).filter(Boolean).length)

const markDirty = (field) => {
  dirtyFields.value = { ...dirtyFields.value, [field]: true }
}

const isDirty = (field) => Boolean(dirtyFields.value[field])

const scrollToSection = (key) => {
  activeSection.value = key
  document.getElementById(`settings-${key}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const saveAll = async () => {
  const hadDirtyFields = dirtyCount.value > 0
  try {
    await settingsApi.save({
      siteName: globalConfig.siteName,
      apiPrefix: globalConfig.apiPrefix,
      maintenanceMode: globalConfig.maintenanceMode,
      refreshRate: globalConfig.refreshRate,
      retryCount: crawlerConfig.retryCount,
      timeoutMs: crawlerConfig.timeoutMs,
      concurrency: crawlerConfig.concurrency,
      userAgents: crawlerConfig.userAgents,
      alertThresholdPercent: qualityConfig.abnormalWavePercent,
      missingTolerance: qualityConfig.missingTolerance,
      autoClean: qualityConfig.autoClean
    })
    dirtyFields.value = {}
    ElMessage.success(hadDirtyFields ? '所有配置已保存' : '当前配置已同步')
    await loadSettings()
  } catch (error) {
    ElMessage.error(error.message || '配置保存失败')
  }
}

const openDangerAction = (type) => {
  const actionMap = {
    clearLogs: {
      title: '清空采集日志',
      message: '该操作会清空采集引擎历史日志，保留审计记录。',
      success: '采集日志已清空'
    },
    resetModel: {
      title: '重置模型',
      message: '该操作会重置趋势预测模型参数，下一轮训练前预测结果将回退到基准模型。',
      success: '模型已进入重置队列'
    }
  }
  const currentAction = actionMap[type]
  Object.assign(dangerDialog, { ...currentAction, visible: true })
}

const executeDangerAction = () => {
  dangerDialog.visible = false
  ElMessage.success(dangerDialog.success)
}

const loadSettings = async () => {
  try {
    const [settings, dbStatus, logs] = await Promise.all([
      settingsApi.get(),
      settingsApi.dbStatus(),
      settingsApi.auditLogs()
    ])
    applySettings(settings)
    databaseStatus.value = normalizeDatabaseStatus(dbStatus)
    auditLogs.value = (Array.isArray(logs) ? logs : []).slice(0, 20).map(normalizeAuditLog)
  } catch (error) {
    ElMessage.error(error.message || '系统配置加载失败')
  }
}

const applySettings = (settings = {}) => {
  globalConfig.siteName = settings.siteName || globalConfig.siteName
  globalConfig.apiPrefix = settings.apiPrefix || globalConfig.apiPrefix
  globalConfig.maintenanceMode = Boolean(settings.maintenanceMode ?? globalConfig.maintenanceMode)
  globalConfig.refreshRate = settings.refreshRate || globalConfig.refreshRate
  crawlerConfig.retryCount = Number(settings.retryCount ?? crawlerConfig.retryCount)
  crawlerConfig.timeoutMs = String(settings.timeoutMs ?? crawlerConfig.timeoutMs)
  crawlerConfig.concurrency = Number(settings.concurrency ?? crawlerConfig.concurrency)
  crawlerConfig.userAgents = settings.userAgents || crawlerConfig.userAgents
  qualityConfig.abnormalWavePercent = Number(settings.alertThresholdPercent ?? qualityConfig.abnormalWavePercent)
  qualityConfig.missingTolerance = Number(settings.missingTolerance ?? qualityConfig.missingTolerance)
  qualityConfig.autoClean = Boolean(settings.autoClean ?? qualityConfig.autoClean)
}

const normalizeDatabaseStatus = (status = {}) => ([
  {
    name: 'MongoDB',
    role: '生产行情库',
    status: status.mongodb?.status === 'up' ? 'connected' : 'error',
    latency: status.mongodb?.status === 'up' ? '已连通' : '异常',
    endpoint: 'agri_price'
  },
  {
    name: 'Redis',
    role: '热点缓存库',
    status: status.redis?.status === 'up' ? 'connected' : 'error',
    latency: status.redis?.detail || status.redis?.message || '-',
    endpoint: '127.0.0.1:6379'
  }
])

const normalizeAuditLog = (log) => ({
  time: String(log.created_at || log.createdAt || log.time || '').replace('T', ' ').slice(0, 19),
  operator: log.operator || log.user_id || 'system',
  action: log.action || log.detail || '-',
  ip: log.ip || '-'
})

onMounted(loadSettings)
</script>

<template>
  <div class="settings-center relative pb-24">
    <div class="grid gap-5 xl:grid-cols-[260px_minmax(0,1fr)]">
      <aside class="xl:sticky xl:top-3 xl:self-start">
        <el-card shadow="never" class="settings-nav-card overflow-hidden">
          <div class="border-b border-forest-900/10 bg-[#064e3b] px-4 py-4 text-white">
            <div class="flex items-center gap-3">
              <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-white/12 ring-1 ring-white/20">
                <Zap class="h-5 w-5" />
              </span>
              <div>
                <p class="text-sm font-semibold">AgriPulse</p>
                <p class="mt-0.5 text-xs text-emerald-100">系统设置中心</p>
              </div>
            </div>
          </div>

          <el-menu :default-active="activeSection" class="settings-sub-menu" @select="scrollToSection">
            <el-menu-item v-for="item in sections" :key="item.key" :index="item.key">
              <component :is="item.icon" class="mr-2 h-4 w-4" />
              <span>{{ item.label }}</span>
            </el-menu-item>
          </el-menu>

          <div class="border-t bg-slate-50 px-4 py-4">
            <div class="flex items-center justify-between text-xs text-slate-500">
              <span>未保存项</span>
              <span class="rounded-md bg-amber-100 px-2 py-1 font-semibold text-amber-700">{{ dirtyCount }}</span>
            </div>
          </div>
        </el-card>
      </aside>

      <div class="space-y-5">
        <el-card id="settings-global" shadow="never" class="settings-card">
          <template #header>
            <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div class="flex items-center gap-3">
                <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-forest-50 text-[#064e3b]">
                  <Globe2 class="h-5 w-5" />
                </span>
                <div>
                  <h2 class="text-base font-semibold text-slate-950">全局配置</h2>
                  <p class="mt-1 text-sm text-slate-500">平台标识、接口前缀与刷新策略</p>
                </div>
              </div>
              <el-tag type="success" effect="plain">运行中</el-tag>
            </div>
          </template>

          <el-form label-position="top" class="settings-form grid gap-4 lg:grid-cols-2">
            <el-form-item label="站点名称">
              <div class="setting-control">
                <el-input v-model="globalConfig.siteName" @input="markDirty('siteName')" />
                <span v-if="isDirty('siteName')" class="unsaved-marker">未保存</span>
              </div>
            </el-form-item>
            <el-form-item label="API 全局前缀">
              <div class="setting-control">
                <el-input v-model="globalConfig.apiPrefix" @input="markDirty('apiPrefix')" />
                <span v-if="isDirty('apiPrefix')" class="unsaved-marker">未保存</span>
              </div>
            </el-form-item>
            <el-form-item label="系统维护模式">
              <div class="setting-control justify-between rounded-lg border bg-slate-50 px-4 py-3">
                <div>
                  <p class="text-sm font-medium text-slate-800">维护窗口</p>
                  <p class="mt-1 text-xs text-slate-500">开启后前台只保留只读监控能力</p>
                </div>
                <div class="flex items-center gap-2">
                  <el-switch v-model="globalConfig.maintenanceMode" @change="markDirty('maintenanceMode')" />
                  <span v-if="isDirty('maintenanceMode')" class="unsaved-marker">未保存</span>
                </div>
              </div>
            </el-form-item>
            <el-form-item label="默认刷新频率">
              <div class="setting-control">
                <el-select v-model="globalConfig.refreshRate" class="w-full" @change="markDirty('refreshRate')">
                  <el-option v-for="option in refreshOptions" :key="option.value" :label="option.label" :value="option.value" />
                </el-select>
                <span v-if="isDirty('refreshRate')" class="unsaved-marker">未保存</span>
              </div>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card id="settings-crawler" shadow="never" class="settings-card">
          <template #header>
            <div class="flex items-center gap-3">
              <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 text-[#064e3b]">
                <SlidersHorizontal class="h-5 w-5" />
              </span>
              <div>
                <h2 class="text-base font-semibold text-slate-950">采集引擎参数</h2>
                <p class="mt-1 text-sm text-slate-500">重试策略、请求时限、并发与 User-Agent 池</p>
              </div>
            </div>
          </template>

          <div class="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
            <el-form label-position="top" class="settings-form space-y-4">
              <el-form-item label="全局重试次数">
                <div class="setting-control">
                  <el-input-number v-model="crawlerConfig.retryCount" :min="0" :max="10" controls-position="right" @change="markDirty('retryCount')" />
                  <span v-if="isDirty('retryCount')" class="unsaved-marker">未保存</span>
                </div>
              </el-form-item>
              <el-form-item label="请求超时时间">
                <div class="setting-control">
                  <el-input v-model="crawlerConfig.timeoutMs" @input="markDirty('timeoutMs')">
                    <template #append>ms</template>
                  </el-input>
                  <span v-if="isDirty('timeoutMs')" class="unsaved-marker">未保存</span>
                </div>
              </el-form-item>
              <el-form-item label="并发限制配置">
                <div class="setting-control items-start">
                  <div class="w-full rounded-lg border bg-slate-50 px-4 py-3">
                    <div class="mb-2 flex items-center justify-between text-sm">
                      <span class="text-slate-600">并发通道</span>
                      <span class="font-semibold text-[#064e3b]">{{ crawlerConfig.concurrency }}</span>
                    </div>
                    <el-slider v-model="crawlerConfig.concurrency" :min="1" :max="64" :step="1" @change="markDirty('concurrency')" />
                  </div>
                  <span v-if="isDirty('concurrency')" class="unsaved-marker">未保存</span>
                </div>
              </el-form-item>
            </el-form>

            <el-form label-position="top" class="settings-form">
              <el-form-item label="User-Agent 池配置">
                <div class="setting-control items-start">
                  <el-input
                    v-model="crawlerConfig.userAgents"
                    type="textarea"
                    :rows="9"
                    resize="none"
                    @input="markDirty('userAgents')"
                  />
                  <span v-if="isDirty('userAgents')" class="unsaved-marker">未保存</span>
                </div>
              </el-form-item>
            </el-form>
          </div>
        </el-card>

        <el-card id="settings-quality" shadow="never" class="settings-card quality-card">
          <template #header>
            <div class="flex items-center gap-3">
              <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50 text-amber-700">
                <ShieldCheck class="h-5 w-5" />
              </span>
              <div>
                <h2 class="text-base font-semibold text-slate-950">质量校验阈值</h2>
                <p class="mt-1 text-sm text-slate-500">异常价格波动、缺失容忍与自动清洗隔离</p>
              </div>
            </div>
          </template>

          <div class="grid gap-4 lg:grid-cols-3">
            <div class="rounded-lg border bg-white p-4">
              <div class="mb-3 flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-slate-900">异常价格波动百分比</p>
                  <p class="mt-1 text-xs text-slate-500">超过阈值自动标记为异常</p>
                </div>
                <AlertTriangle class="h-5 w-5 text-amber-600" />
              </div>
              <div class="setting-control">
                <el-input-number v-model="qualityConfig.abnormalWavePercent" :min="1" :max="100" controls-position="right" @change="markDirty('abnormalWavePercent')" />
                <span class="text-sm font-semibold text-slate-500">%</span>
                <span v-if="isDirty('abnormalWavePercent')" class="unsaved-marker">未保存</span>
              </div>
            </div>

            <div class="rounded-lg border bg-white p-4">
              <div class="mb-3 flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-slate-900">缺失值容忍度</p>
                  <p class="mt-1 text-xs text-slate-500">超过比例进入质量复核</p>
                </div>
                <ActivitySquare class="h-5 w-5 text-[#064e3b]" />
              </div>
              <div class="setting-control">
                <el-input-number v-model="qualityConfig.missingTolerance" :min="0" :max="30" controls-position="right" @change="markDirty('missingTolerance')" />
                <span class="text-sm font-semibold text-slate-500">%</span>
                <span v-if="isDirty('missingTolerance')" class="unsaved-marker">未保存</span>
              </div>
            </div>

            <div class="rounded-lg border bg-[#064e3b] p-4 text-white">
              <div class="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold">自动清洗开关</p>
                  <p class="mt-1 text-xs text-emerald-100">不达标数据进入隔离区</p>
                </div>
                <el-switch v-model="qualityConfig.autoClean" @change="markDirty('autoClean')" />
              </div>
              <div class="flex items-center justify-between rounded-lg bg-white/10 px-3 py-2 text-xs text-emerald-50">
                <span>{{ qualityConfig.autoClean ? '隔离区已启用' : '仅标记不拦截' }}</span>
                <span v-if="isDirty('autoClean')" class="unsaved-marker">未保存</span>
              </div>
            </div>
          </div>
        </el-card>

        <div class="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
          <el-card id="settings-database" shadow="never" class="settings-card">
            <template #header>
              <div class="flex items-center gap-3">
                <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-forest-50 text-[#064e3b]">
                  <Database class="h-5 w-5" />
                </span>
                <div>
                  <h2 class="text-base font-semibold text-slate-950">数据库状态</h2>
                  <p class="mt-1 text-sm text-slate-500">MongoDB 与 Redis 连接态势</p>
                </div>
              </div>
            </template>

            <div class="space-y-3">
              <div v-for="database in databaseStatus" :key="database.name" class="rounded-lg border bg-slate-50 p-4">
                <div class="flex items-start justify-between gap-3">
                  <div class="flex items-center gap-3">
                    <span :class="['status-lamp', database.status === 'connected' ? 'status-lamp-ok' : 'status-lamp-danger']" />
                    <div>
                      <p class="text-sm font-semibold text-slate-950">{{ database.name }}</p>
                      <p class="mt-1 text-xs text-slate-500">{{ database.role }}</p>
                    </div>
                  </div>
                  <el-tag :type="database.status === 'connected' ? 'success' : 'danger'" effect="plain">
                    {{ database.status === 'connected' ? '连接正常' : '连接异常' }}
                  </el-tag>
                </div>
                <div class="mt-4 grid gap-2 text-xs text-slate-500 sm:grid-cols-2">
                  <div class="rounded-md border bg-white px-3 py-2">
                    <span class="block text-slate-400">实例</span>
                    <span class="mt-1 block font-medium text-slate-700">{{ database.endpoint }}</span>
                  </div>
                  <div class="rounded-md border bg-white px-3 py-2">
                    <span class="block text-slate-400">延迟</span>
                    <span class="mt-1 block font-medium text-slate-700">{{ database.latency }}</span>
                  </div>
                </div>
              </div>

              <div class="flex flex-col gap-2 border-t pt-4 sm:flex-row">
                <el-button type="danger" plain class="danger-action" @click="openDangerAction('clearLogs')">
                  <Trash2 class="mr-1 h-4 w-4" />清空采集日志
                </el-button>
                <el-button type="danger" plain class="danger-action" @click="openDangerAction('resetModel')">
                  <RotateCcw class="mr-1 h-4 w-4" />重置模型
                </el-button>
              </div>
            </div>
          </el-card>

          <el-card id="settings-audit" shadow="never" class="settings-card">
            <template #header>
              <div class="flex items-center gap-3">
                <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                  <FileClock class="h-5 w-5" />
                </span>
                <div>
                  <h2 class="text-base font-semibold text-slate-950">审计日志</h2>
                  <p class="mt-1 text-sm text-slate-500">最近 5 条管理员操作记录</p>
                </div>
              </div>
            </template>

            <el-table :data="auditLogs" size="small" class="audit-table" height="316">
              <el-table-column prop="time" label="时间" min-width="156" />
              <el-table-column prop="operator" label="操作人" min-width="94" />
              <el-table-column prop="action" label="动作" min-width="160" show-overflow-tooltip />
              <el-table-column prop="ip" label="IP" min-width="116" />
            </el-table>
          </el-card>
        </div>
      </div>
    </div>

    <div class="fixed bottom-6 right-6 z-30">
      <el-button type="primary" size="large" class="save-all-button" @click="saveAll">
        <Save class="mr-2 h-4 w-4" />保存所有配置
        <span v-if="dirtyCount" class="ml-2 rounded-full bg-white/20 px-2 py-0.5 text-xs">{{ dirtyCount }}</span>
      </el-button>
    </div>

    <div v-if="dangerDialog.visible" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4" role="dialog" aria-modal="true" :aria-label="dangerDialog.title">
      <div class="w-full max-w-[420px] rounded-lg border border-red-100 bg-white p-5 shadow-2xl">
        <div class="flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-red-50 text-red-600">
            <AlertTriangle class="h-5 w-5" />
          </span>
          <div>
            <h3 class="text-base font-semibold text-slate-950">{{ dangerDialog.title }}</h3>
            <p class="mt-2 text-sm leading-6 text-slate-600">{{ dangerDialog.message }}</p>
          </div>
        </div>
        <div class="mt-5 flex justify-end gap-2">
          <el-button @click="dangerDialog.visible = false">取消</el-button>
          <el-button type="danger" @click="executeDangerAction">确认执行</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-center {
  --el-color-primary: #064e3b;
  --el-color-primary-light-3: #13805f;
  --el-color-primary-light-5: #36a47f;
  --el-color-primary-light-7: #a7f3d0;
  --el-color-primary-light-8: #d1fae5;
  --el-color-primary-light-9: #ecfdf5;
  --el-color-primary-dark-2: #043829;
}

.settings-nav-card,
.settings-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06), 0 8px 24px rgba(15, 23, 42, 0.04);
}

.settings-nav-card :deep(.el-card__body),
.settings-card :deep(.el-card__body) {
  padding: 0;
}

.settings-card :deep(.el-card__header) {
  padding: 18px 20px;
  border-bottom-color: #e2e8f0;
  background: linear-gradient(90deg, #ffffff 0%, #f8fafc 100%);
}

.settings-card :deep(.el-card__body) {
  padding: 20px;
}

.settings-sub-menu {
  border-right: 0;
  padding: 10px;
}

.settings-sub-menu :deep(.el-menu-item) {
  height: 42px;
  border-radius: 8px;
  color: #475569;
}

.settings-sub-menu :deep(.el-menu-item.is-active) {
  background: #ecfdf5;
  color: #064e3b;
  font-weight: 700;
}

.settings-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.settings-form :deep(.el-form-item__label) {
  color: #334155;
  font-weight: 700;
}

.setting-control {
  display: flex;
  min-width: 0;
  width: 100%;
  align-items: center;
  gap: 10px;
}

.setting-control :deep(.el-input),
.setting-control :deep(.el-select),
.setting-control :deep(.el-input-number),
.setting-control :deep(.el-textarea) {
  flex: 1;
  min-width: 0;
}

.unsaved-marker {
  display: inline-flex;
  min-width: 52px;
  height: 24px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: 1px solid #fcd34d;
  background: #fffbeb;
  color: #b45309;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
}

.quality-card :deep(.el-card__body) {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.status-lamp {
  position: relative;
  width: 12px;
  height: 12px;
  flex: 0 0 auto;
  border-radius: 999px;
}

.status-lamp::after {
  position: absolute;
  inset: -6px;
  border-radius: inherit;
  content: '';
  animation: lampPulse 1.8s ease-out infinite;
}

.status-lamp-ok {
  background: #10b981;
}

.status-lamp-ok::after {
  border: 1px solid rgba(16, 185, 129, 0.35);
}

.status-lamp-danger {
  background: #ef4444;
}

.status-lamp-danger::after {
  border: 1px solid rgba(239, 68, 68, 0.35);
}

.danger-action {
  margin-left: 0;
}

.audit-table :deep(.el-table__header th) {
  color: #475569;
  background: #f8fafc;
}

.save-all-button {
  min-width: 168px;
  height: 44px;
  border: 0;
  background: #064e3b;
  box-shadow: 0 14px 34px rgba(6, 78, 59, 0.32);
}

.save-all-button:hover,
.save-all-button:focus {
  background: #043829;
}

@keyframes lampPulse {
  0% {
    transform: scale(0.75);
    opacity: 0.82;
  }
  100% {
    transform: scale(1.85);
    opacity: 0;
  }
}

@media (max-width: 640px) {
  .setting-control {
    align-items: stretch;
    flex-direction: column;
  }

  .save-all-button {
    min-width: 148px;
  }
}
</style>