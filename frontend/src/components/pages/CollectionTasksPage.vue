<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Activity, AlertTriangle, Clock3, DatabaseZap, FileText, Pencil, Pause, Play, Plus, RefreshCw, Search, ServerOff } from 'lucide-vue-next'
import Badge from '../ui/Badge.vue'
import Button from '../ui/Button.vue'
import { taskApi } from '../../lib/api'

const statusOptions = [
  { value: 'all', label: '全部状态' },
  { value: 'running', label: '运行中' },
  { value: 'stopped', label: '已停止' },
  { value: 'error', label: '异常' }
]

const defaultTasks = [
  { id: 'xf-001', name: '北京新发地价格采集', source: '新发地批发市场', frequency: '5分钟/次', lastSync: '2026-05-30 00:28:12', successRate: 99.2, status: 'running', backlog: 128 },
  { id: 'sg-002', name: '寿光蔬菜行情采集', source: '寿光蔬菜网', frequency: '10分钟/次', lastSync: '2026-05-30 00:24:35', successRate: 97.8, status: 'running', backlog: 86 },
  { id: 'moa-003', name: '农业农村部价格指数同步', source: '农业农村部官网', frequency: '30分钟/次', lastSync: '2026-05-30 00:02:41', successRate: 96.4, status: 'running', backlog: 42 },
  { id: 'mofcom-004', name: '商务部农产品行情采集', source: '全国农产品商务信息公共服务平台', frequency: '15分钟/次', lastSync: '2026-05-29 23:58:09', successRate: 91.6, status: 'error', backlog: 624 },
  { id: 'weather-005', name: '气象辅助数据同步', source: '中国天气网', frequency: '30分钟/次', lastSync: '2026-05-30 00:15:53', successRate: 98.7, status: 'running', backlog: 73 },
  { id: 'market-006', name: '华东批发市场补采任务', source: '区域批发市场联盟', frequency: '1小时/次', lastSync: '2026-05-29 22:46:21', successRate: 88.3, status: 'stopped', backlog: 1180 },
  { id: 'fresh-007', name: '生鲜电商价格巡检', source: '主流农产品电商平台', frequency: '20分钟/次', lastSync: '2026-05-30 00:11:16', successRate: 94.9, status: 'running', backlog: 213 }
]

const tasks = ref(defaultTasks)

const statusMeta = {
  running: { label: '运行中', className: 'bg-forest-100 text-forest-800 border-transparent', icon: Play },
  stopped: { label: '已停止', className: 'bg-slate-100 text-slate-600 border-transparent', icon: Pause },
  error: { label: '异常', className: 'bg-red-100 text-red-700 border-transparent', icon: AlertTriangle }
}

const status = ref('all')
const keyword = ref('')
const refreshing = ref(false)
const refreshedAt = ref('00:30:12')
const savingTask = ref(false)
const formVisible = ref(false)
const formMode = ref('create')
const logsVisible = ref(false)
const logsLoading = ref(false)
const logRows = ref([])
const logTask = ref(null)
const taskForm = reactive({
  id: '',
  name: '',
  source: '',
  frequency: '5分钟/次',
  status: 'stopped',
  successRate: 0,
  backlog: 0,
  productsText: '番茄 大白菜 黄瓜 土豆 玉米 大米 大豆 猪肉 牛肉 鸡蛋',
  lookbackDays: 3
})

const filteredTasks = computed(() => {
  const normalizedKeyword = keyword.value.trim().toLowerCase()
  return tasks.value.filter((task) => {
    const matchStatus = status.value === 'all' || task.status === status.value
    const matchKeyword = !normalizedKeyword || `${task.name} ${task.source}`.toLowerCase().includes(normalizedKeyword)
    return matchStatus && matchKeyword
  })
})

const summary = computed(() => {
  const rows = tasks.value.length ? tasks.value : defaultTasks
  const runningTasks = rows.filter((task) => task.status === 'running')
  const totalBacklog = rows.reduce((sum, task) => sum + Number(task.backlog || 0), 0)
  const averageRate = rows.reduce((sum, task) => sum + Number(task.successRate || 0), 0) / rows.length
  return {
    successRate: averageRate.toFixed(1),
    backlog: totalBacklog.toLocaleString('zh-CN'),
    offline: rows.length - runningTasks.length
  }
})

const monitorCards = computed(() => [
  { icon: Activity, title: '今日采集成功率', value: `${summary.value.successRate}%`, detail: '按任务成功率加权汇总', toneClass: 'bg-forest-50 text-forest-700 border-forest-100' },
  { icon: DatabaseZap, title: '待处理数据积压量', value: summary.value.backlog, detail: '等待清洗与入库的数据记录', toneClass: 'bg-amber-50 text-amber-700 border-amber-100' },
  { icon: ServerOff, title: '离线采集点', value: summary.value.offline, detail: '已停止或异常的数据源', toneClass: 'bg-red-50 text-red-700 border-red-100' }
])

const loadTasks = async () => {
  refreshing.value = true
  try {
    const rows = await taskApi.list({ status: status.value, keyword: keyword.value })
    tasks.value = rows.map(normalizeTask)
    refreshedAt.value = new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(new Date())
  } catch (error) {
    ElMessage.error(error.message || '采集任务加载失败')
  } finally {
    refreshing.value = false
  }
}

const toggleTask = async (task) => {
  try {
    if (task.status === 'running') {
      await taskApi.stop(task.id)
      ElMessage.success('任务已暂停')
    } else {
      await taskApi.start(task.id)
      ElMessage.success('任务已启动')
    }
    await loadTasks()
  } catch (error) {
    ElMessage.error(error.message || '任务状态更新失败')
  }
}

const runTaskNow = async (task) => {
  refreshing.value = true
  try {
    await taskApi.start(task.id)
    ElMessage.success('网页采集完成，数据已写入 MongoDB')
    await loadTasks()
  } catch (error) {
    ElMessage.error(error.message || '网页采集失败')
    await loadTasks()
  } finally {
    refreshing.value = false
  }
}

const viewLogs = async (task) => {
  logTask.value = task
  logsVisible.value = true
  logsLoading.value = true
  try {
    const logs = await taskApi.logs(task.id)
    logRows.value = Array.isArray(logs) ? logs.map(normalizeLog) : []
  } catch (error) {
    ElMessage.error(error.message || '日志加载失败')
  } finally {
    logsLoading.value = false
  }
}

const openCreateForm = () => {
  formMode.value = 'create'
  Object.assign(taskForm, {
    id: '',
    name: '',
    source: '',
    frequency: '5分钟/次',
    status: 'stopped',
    successRate: 0,
    backlog: 0,
    productsText: '番茄 大白菜 黄瓜 土豆 玉米 大米 大豆 猪肉 牛肉 鸡蛋',
    lookbackDays: 3
  })
  formVisible.value = true
}

const openEditForm = (task) => {
  formMode.value = 'edit'
  Object.assign(taskForm, {
    id: task.id,
    name: task.name,
    source: task.source,
    frequency: task.frequency,
    status: task.status,
    successRate: task.successRate,
    backlog: task.backlog,
    productsText: Array.isArray(task.products) && task.products.length ? task.products.join(' ') : task.productsText,
    lookbackDays: task.lookbackDays || 3
  })
  formVisible.value = true
}

const saveTask = async () => {
  if (!taskForm.name.trim() || !taskForm.source.trim()) {
    ElMessage.warning('请填写任务名称和数据来源')
    return
  }
  savingTask.value = true
  const body = {
    name: taskForm.name.trim(),
    source: taskForm.source.trim(),
    frequency: taskForm.frequency.trim() || '未设置',
    status: taskForm.status,
    successRate: Number(taskForm.successRate || 0),
    backlog: Number(taskForm.backlog || 0),
    products: splitProducts(taskForm.productsText),
    lookbackDays: Number(taskForm.lookbackDays || 3)
  }
  if (formMode.value === 'create' && taskForm.id.trim()) body.id = taskForm.id.trim()
  try {
    if (formMode.value === 'create') {
      await taskApi.create(body)
      ElMessage.success('采集任务已创建')
    } else {
      await taskApi.update(taskForm.id, body)
      ElMessage.success('采集任务已更新')
    }
    formVisible.value = false
    await loadTasks()
  } catch (error) {
    ElMessage.error(error.message || '任务保存失败')
  } finally {
    savingTask.value = false
  }
}

const splitProducts = (text) => Array.from(new Set(String(text || '').split(/[,，\s]+/).map((item) => item.trim()).filter(Boolean)))

const normalizeLog = (log) => ({
  id: log.id || log._id || `${log.task_id || log.taskId}-${log.created_at || log.createdAt}-${log.message}`,
  action: log.action || '-',
  level: log.level || 'INFO',
  message: log.message || '暂无运行日志',
  createdAt: log.created_at || log.createdAt || '-'
})

const normalizeTask = (task) => ({
  id: task.id || task._id,
  name: task.name || '未命名采集任务',
  source: task.source || '未配置数据源',
  frequency: task.frequency || '未设置',
  lastSync: task.lastSync || task.last_sync || task.updated_at || '-',
  successRate: Math.max(0, Math.min(100, Number(task.successRate ?? task.success_rate ?? 0) || 0)),
  status: statusMeta[task.status] ? task.status : 'stopped',
  backlog: Number(task.backlog || 0),
  products: Array.isArray(task.products) ? task.products : splitProducts(task.products),
  productsText: Array.isArray(task.products) ? task.products.join(' ') : String(task.products || '番茄 大白菜 黄瓜 土豆 玉米 大米 大豆 猪肉 牛肉 鸡蛋'),
  lookbackDays: Number(task.lookbackDays ?? task.lookback_days ?? 3)
})

onMounted(loadTasks)
</script>

<template>
  <div class="space-y-4">
    <div class="grid gap-4 md:grid-cols-3">
      <div v-for="card in monitorCards" :key="card.title" class="rounded-lg border bg-white p-5 shadow-panel">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm text-slate-500">{{ card.title }}</p>
            <p class="mt-3 text-2xl font-semibold text-slate-950">{{ card.value }}</p>
          </div>
          <div :class="['flex h-10 w-10 items-center justify-center rounded-lg border', card.toneClass]">
            <component :is="card.icon" class="h-5 w-5" />
          </div>
        </div>
        <p class="mt-4 text-sm text-slate-500">{{ card.detail }}</p>
      </div>
    </div>

    <section class="rounded-lg border bg-white shadow-panel">
      <div class="flex flex-col gap-3 border-b p-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h2 class="text-base font-semibold text-slate-950">采集任务列表</h2>
          <p class="mt-1 text-sm text-slate-500">统一管理市场、平台和气象来源的采集调度。</p>
        </div>
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
          <Button @click="openCreateForm"><Plus class="h-4 w-4" />新增采集任务</Button>
          <select v-model="status" class="h-9 rounded-md border bg-white px-3 text-sm text-slate-700 shadow-sm outline-none transition-colors focus:border-forest-500 focus:ring-2 focus:ring-forest-100" aria-label="状态筛选">
            <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
          <div class="relative min-w-[280px]">
            <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input v-model="keyword" placeholder="搜索来源：新发地批发市场、寿光蔬菜网" class="h-9 w-full rounded-md border bg-white pl-9 pr-3 text-sm text-slate-700 shadow-sm outline-none transition-colors placeholder:text-slate-400 focus:border-forest-500 focus:ring-2 focus:ring-forest-100" />
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between gap-3 border-b bg-slate-50 px-4 py-3">
        <div class="flex flex-wrap items-center gap-2">
          <Badge variant="outline">高性能表格</Badge>
          <Badge variant="outline">固定表头</Badge>
          <Badge variant="outline">Vue 响应式筛选</Badge>
        </div>
        <div class="flex items-center gap-2 text-xs text-slate-500">
          <Clock3 class="h-3.5 w-3.5" />
          <span>最近刷新：{{ refreshing ? '同步中' : refreshedAt }}</span>
        </div>
      </div>

      <div class="max-h-[520px] overflow-auto">
        <table class="w-full table-fixed border-collapse text-left">
          <thead class="sticky top-0 z-10 bg-slate-50 text-xs font-medium uppercase text-slate-500 shadow-[inset_0_-1px_0_hsl(var(--border))]">
            <tr>
              <th class="w-[18%] px-4 py-3">任务名称</th>
              <th class="w-[20%] px-4 py-3">数据来源</th>
              <th class="w-[12%] px-4 py-3">采集频率</th>
              <th class="w-[18%] px-4 py-3">最后同步时间</th>
              <th class="w-[14%] px-4 py-3">当前采集成功率</th>
              <th class="w-[10%] px-4 py-3">状态</th>
              <th class="w-[20%] px-4 py-3 text-right">操作栏</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in filteredTasks" :key="task.id" class="border-b bg-white transition-colors hover:bg-slate-50">
              <td class="w-[18%] px-4 py-4">
                <p class="truncate text-sm font-medium text-slate-950">{{ task.name }}</p>
                <p class="mt-1 truncate text-xs text-slate-400">任务编号：{{ task.id }}</p>
              </td>
              <td class="w-[20%] px-4 py-4"><p class="truncate text-sm text-slate-700">{{ task.source }}</p></td>
              <td class="w-[12%] px-4 py-4 text-sm text-slate-600">{{ task.frequency }}</td>
              <td class="w-[18%] px-4 py-4 text-sm text-slate-600">{{ task.lastSync }}</td>
              <td class="w-[14%] px-4 py-4">
                <div class="flex items-center gap-3">
                  <div class="h-2 w-20 overflow-hidden rounded-full bg-slate-100">
                    <div :class="['h-full rounded-full', task.successRate >= 95 ? 'bg-forest-600' : 'bg-harvest-500']" :style="{ width: `${task.successRate}%` }" />
                  </div>
                  <span class="text-sm font-medium text-slate-800">{{ task.successRate }}%</span>
                </div>
              </td>
              <td class="w-[10%] px-4 py-4">
                <span :class="['inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium', statusMeta[task.status].className]">
                  <component :is="statusMeta[task.status].icon" class="h-3.5 w-3.5" />
                  {{ statusMeta[task.status].label }}
                </span>
              </td>
              <td class="w-[20%] px-4 py-4">
                <div class="flex items-center justify-end gap-1.5">
                  <Button variant="ghost" size="sm" title="编辑任务" @click="openEditForm(task)"><Pencil class="h-4 w-4" />编辑</Button>
                  <Button variant="ghost" size="sm" title="立即采集一次" :disabled="refreshing" @click="runTaskNow(task)"><RefreshCw :class="['h-4 w-4', refreshing && 'animate-spin']" />采集</Button>
                  <Button variant="ghost" size="sm" :title="task.status === 'running' ? '暂停任务' : '启动任务'" @click="toggleTask(task)">
                    <Pause v-if="task.status === 'running'" class="h-4 w-4" />
                    <Play v-else class="h-4 w-4" />
                    {{ task.status === 'running' ? '暂停' : '启动' }}
                  </Button>
                  <Button variant="ghost" size="sm" title="查看日志" @click="viewLogs(task)"><FileText class="h-4 w-4" />日志</Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="filteredTasks.length === 0" class="flex h-40 items-center justify-center text-sm text-slate-500">没有匹配的采集任务</div>
      </div>
    </section>

    <el-dialog v-model="formVisible" :title="formMode === 'create' ? '新增采集任务' : '编辑采集任务'" width="620px" destroy-on-close>
      <div class="grid gap-4">
        <label class="grid gap-1 text-sm font-medium text-slate-700">
          任务编号
          <el-input v-model="taskForm.id" :disabled="formMode === 'edit'" placeholder="留空则由后端自动生成" />
        </label>
        <label class="grid gap-1 text-sm font-medium text-slate-700">
          任务名称
          <el-input v-model="taskForm.name" placeholder="例如：北京新发地价格采集" />
        </label>
        <label class="grid gap-1 text-sm font-medium text-slate-700">
          数据来源
          <el-input v-model="taskForm.source" placeholder="例如：新发地批发市场" />
        </label>
        <div class="grid gap-4 sm:grid-cols-2">
          <label class="grid gap-1 text-sm font-medium text-slate-700">
            采集频率
            <el-input v-model="taskForm.frequency" placeholder="例如：5分钟/次" />
          </label>
          <label class="grid gap-1 text-sm font-medium text-slate-700">
            状态
            <el-select v-model="taskForm.status">
              <el-option v-for="option in statusOptions.filter((item) => item.value !== 'all')" :key="option.value" :label="option.label" :value="option.value" />
            </el-select>
          </label>
        </div>
        <div class="grid gap-4 sm:grid-cols-3">
          <label class="grid gap-1 text-sm font-medium text-slate-700">
            成功率
            <el-input-number v-model="taskForm.successRate" :min="0" :max="100" :precision="1" class="w-full" />
          </label>
          <label class="grid gap-1 text-sm font-medium text-slate-700">
            积压量
            <el-input-number v-model="taskForm.backlog" :min="0" class="w-full" />
          </label>
          <label class="grid gap-1 text-sm font-medium text-slate-700">
            回看天数
            <el-input-number v-model="taskForm.lookbackDays" :min="1" :max="30" class="w-full" />
          </label>
        </div>
        <label class="grid gap-1 text-sm font-medium text-slate-700">
          采集品类
          <el-input v-model="taskForm.productsText" type="textarea" :rows="3" placeholder="用空格或逗号分隔，例如：番茄 大白菜 黄瓜 玉米 猪肉" />
        </label>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <Button variant="secondary" @click="formVisible = false">取消</Button>
          <Button :disabled="savingTask" @click="saveTask">{{ savingTask ? '保存中' : '保存' }}</Button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="logsVisible" :title="`${logTask?.name || '采集任务'}运行日志`" width="760px" destroy-on-close>
      <div v-if="logsLoading" class="flex h-32 items-center justify-center text-sm text-slate-500">日志加载中...</div>
      <div v-else-if="logRows.length" class="max-h-[420px] overflow-auto rounded-lg border">
        <div v-for="log in logRows" :key="log.id" class="grid grid-cols-[120px_80px_minmax(0,1fr)] gap-3 border-b px-4 py-3 text-sm last:border-b-0">
          <span class="text-slate-500">{{ log.createdAt }}</span>
          <Badge :variant="log.level === 'ERROR' ? 'danger' : 'outline'">{{ log.level }}</Badge>
          <div class="min-w-0">
            <p class="font-medium text-slate-900">{{ log.action }}</p>
            <p class="mt-1 whitespace-pre-wrap break-words text-slate-600">{{ log.message }}</p>
          </div>
        </div>
      </div>
      <div v-else class="flex h-32 items-center justify-center text-sm text-slate-500">暂无运行日志</div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <Button variant="secondary" @click="logsVisible = false">关闭</Button>
          <Button v-if="logTask" :disabled="logsLoading" @click="viewLogs(logTask)">刷新日志</Button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>