import { memo, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  Clock3,
  DatabaseZap,
  FileText,
  Pencil,
  Pause,
  Play,
  Plus,
  Search,
  ServerOff
} from 'lucide-react'
import { Badge } from '../ui/badge.jsx'
import { Button } from '../ui/button.jsx'
import { cn } from '../../lib/utils.js'

const statusOptions = [
  { value: 'all', label: '全部状态' },
  { value: 'running', label: '运行中' },
  { value: 'stopped', label: '已停止' },
  { value: 'error', label: '异常' }
]

const tasks = [
  {
    id: 'xf-001',
    name: '北京新发地价格采集',
    source: '新发地批发市场',
    frequency: '5分钟/次',
    lastSync: '2026-05-30 00:28:12',
    successRate: 99.2,
    status: 'running',
    backlog: 128
  },
  {
    id: 'sg-002',
    name: '寿光蔬菜行情采集',
    source: '寿光蔬菜网',
    frequency: '10分钟/次',
    lastSync: '2026-05-30 00:24:35',
    successRate: 97.8,
    status: 'running',
    backlog: 86
  },
  {
    id: 'moa-003',
    name: '农业农村部价格指数同步',
    source: '农业农村部官网',
    frequency: '30分钟/次',
    lastSync: '2026-05-30 00:02:41',
    successRate: 96.4,
    status: 'running',
    backlog: 42
  },
  {
    id: 'mofcom-004',
    name: '商务部农产品行情采集',
    source: '全国农产品商务信息公共服务平台',
    frequency: '15分钟/次',
    lastSync: '2026-05-29 23:58:09',
    successRate: 91.6,
    status: 'error',
    backlog: 624
  },
  {
    id: 'weather-005',
    name: '气象辅助数据同步',
    source: '中国天气网',
    frequency: '30分钟/次',
    lastSync: '2026-05-30 00:15:53',
    successRate: 98.7,
    status: 'running',
    backlog: 73
  },
  {
    id: 'market-006',
    name: '华东批发市场补采任务',
    source: '区域批发市场联盟',
    frequency: '1小时/次',
    lastSync: '2026-05-29 22:46:21',
    successRate: 88.3,
    status: 'stopped',
    backlog: 1180
  },
  {
    id: 'fresh-007',
    name: '生鲜电商价格巡检',
    source: '主流农产品电商平台',
    frequency: '20分钟/次',
    lastSync: '2026-05-30 00:11:16',
    successRate: 94.9,
    status: 'running',
    backlog: 213
  }
]

const statusMeta = {
  running: { label: '运行中', className: 'bg-forest-100 text-forest-800 border-transparent', icon: Play },
  stopped: { label: '已停止', className: 'bg-slate-100 text-slate-600 border-transparent', icon: Pause },
  error: { label: '异常', className: 'bg-red-100 text-red-700 border-transparent', icon: AlertTriangle }
}

const TaskRow = memo(function TaskRow({ task }) {
  const meta = statusMeta[task.status]
  const StatusIcon = meta.icon

  return (
    <tr className="border-b bg-white transition-colors hover:bg-slate-50">
      <td className="w-[20%] px-4 py-4">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-slate-950">{task.name}</p>
          <p className="mt-1 truncate text-xs text-slate-400">任务编号：{task.id}</p>
        </div>
      </td>
      <td className="w-[22%] px-4 py-4">
        <p className="truncate text-sm text-slate-700">{task.source}</p>
      </td>
      <td className="w-[12%] px-4 py-4 text-sm text-slate-600">{task.frequency}</td>
      <td className="w-[18%] px-4 py-4 text-sm text-slate-600">{task.lastSync}</td>
      <td className="w-[14%] px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="h-2 w-20 overflow-hidden rounded-full bg-slate-100">
            <div className={cn('h-full rounded-full', task.successRate >= 95 ? 'bg-forest-600' : 'bg-harvest-500')} style={{ width: `${task.successRate}%` }} />
          </div>
          <span className="text-sm font-medium text-slate-800">{task.successRate}%</span>
        </div>
      </td>
      <td className="w-[10%] px-4 py-4">
        <span className={cn('inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium', meta.className)}>
          <StatusIcon className="h-3.5 w-3.5" />
          {meta.label}
        </span>
      </td>
      <td className="w-[16%] px-4 py-4">
        <div className="flex items-center justify-end gap-1.5">
          <Button variant="ghost" size="sm" title="编辑任务">
            <Pencil className="h-4 w-4" />
            编辑
          </Button>
          <Button variant="ghost" size="sm" title="暂停任务">
            <Pause className="h-4 w-4" />
            暂停
          </Button>
          <Button variant="ghost" size="sm" title="查看日志">
            <FileText className="h-4 w-4" />
            日志
          </Button>
        </div>
      </td>
    </tr>
  )
})

export function CollectionTasksPage() {
  const [status, setStatus] = useState('all')
  const [keyword, setKeyword] = useState('')

  const filteredTasks = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase()
    return tasks.filter((task) => {
      const matchStatus = status === 'all' || task.status === status
      const matchKeyword = !normalizedKeyword || `${task.name} ${task.source}`.toLowerCase().includes(normalizedKeyword)
      return matchStatus && matchKeyword
    })
  }, [keyword, status])

  const summary = useMemo(() => {
    const runningTasks = tasks.filter((task) => task.status === 'running')
    const totalBacklog = tasks.reduce((sum, task) => sum + task.backlog, 0)
    const averageRate = tasks.reduce((sum, task) => sum + task.successRate, 0) / tasks.length
    return {
      successRate: averageRate.toFixed(1),
      backlog: totalBacklog.toLocaleString('zh-CN'),
      offline: tasks.length - runningTasks.length
    }
  }, [])

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <MonitorCard
          icon={Activity}
          title="今日采集成功率"
          value={`${summary.successRate}%`}
          detail="按任务成功率加权汇总"
          tone="green"
        />
        <MonitorCard
          icon={DatabaseZap}
          title="待处理数据积压量"
          value={summary.backlog}
          detail="等待清洗与入库的数据记录"
          tone="amber"
        />
        <MonitorCard
          icon={ServerOff}
          title="离线采集点"
          value={summary.offline}
          detail="已停止或异常的数据源"
          tone="red"
        />
      </div>

      <section className="rounded-lg border bg-white shadow-panel">
        <div className="flex flex-col gap-3 border-b p-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-950">采集任务列表</h2>
            <p className="mt-1 text-sm text-slate-500">统一管理市场、平台和气象来源的采集调度。</p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Button>
              <Plus className="h-4 w-4" />
              新增采集任务
            </Button>
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="h-9 rounded-md border bg-white px-3 text-sm text-slate-700 shadow-sm outline-none transition-colors focus:border-forest-500 focus:ring-2 focus:ring-forest-100"
              aria-label="状态筛选"
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            <div className="relative min-w-[280px]">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="搜索来源：新发地批发市场、寿光蔬菜网"
                className="h-9 w-full rounded-md border bg-white pl-9 pr-3 text-sm text-slate-700 shadow-sm outline-none transition-colors placeholder:text-slate-400 focus:border-forest-500 focus:ring-2 focus:ring-forest-100"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 border-b bg-slate-50 px-4 py-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">高性能表格</Badge>
            <Badge variant="outline">固定表头</Badge>
            <Badge variant="outline">Memo 行渲染</Badge>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Clock3 className="h-3.5 w-3.5" />
            <span>最近刷新：00:30:12</span>
          </div>
        </div>

        <div className="max-h-[520px] overflow-auto">
          <table className="w-full table-fixed border-collapse text-left">
            <thead className="sticky top-0 z-10 bg-slate-50 text-xs font-medium uppercase text-slate-500 shadow-[inset_0_-1px_0_hsl(var(--border))]">
              <tr>
                <th className="w-[20%] px-4 py-3">任务名称</th>
                <th className="w-[22%] px-4 py-3">数据来源</th>
                <th className="w-[12%] px-4 py-3">采集频率</th>
                <th className="w-[18%] px-4 py-3">最后同步时间</th>
                <th className="w-[14%] px-4 py-3">当前采集成功率</th>
                <th className="w-[10%] px-4 py-3">状态</th>
                <th className="w-[16%] px-4 py-3 text-right">操作栏</th>
              </tr>
            </thead>
            <tbody>
              {filteredTasks.map((task) => <TaskRow key={task.id} task={task} />)}
            </tbody>
          </table>
          {filteredTasks.length === 0 && (
            <div className="flex h-40 items-center justify-center text-sm text-slate-500">没有匹配的采集任务</div>
          )}
        </div>
      </section>
    </div>
  )
}

function MonitorCard({ icon: Icon, title, value, detail, tone }) {
  const toneClass = {
    green: 'bg-forest-50 text-forest-700 border-forest-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
    red: 'bg-red-50 text-red-700 border-red-100'
  }[tone]

  return (
    <div className="rounded-lg border bg-white p-5 shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">{title}</p>
          <p className="mt-3 text-2xl font-semibold text-slate-950">{value}</p>
        </div>
        <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg border', toneClass)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <p className="mt-4 text-sm text-slate-500">{detail}</p>
    </div>
  )
}