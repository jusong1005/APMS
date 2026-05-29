import { useMemo, useState } from 'react'
import { ArrowDownRight, ArrowUpRight, Database, ServerCog, Sprout, TrendingUp } from 'lucide-react'
import { Header } from './Header.jsx'
import { Sidebar } from './Sidebar.jsx'
import { navigationItems } from './navigation.js'
import { CollectionTasksPage } from '../pages/CollectionTasksPage.jsx'
import { PriceMultiAnalysisPage } from '../pages/PriceMultiAnalysisPage.jsx'
import { TrendPredictionPage } from '../pages/TrendPredictionPage.jsx'
import { Badge } from '../ui/badge.jsx'
import { Button } from '../ui/button.jsx'
import { cn } from '../../lib/utils.js'

const pages = {
  dashboard: {
    title: '全国农产品价格监控大盘',
    description: '汇总采集、清洗、入库、价格波动和预警状态，支撑全国市场价格监测。',
    content: <DashboardContent />
  },
  collection: {
    title: '采集任务管理',
    description: '统一编排批发市场、农贸市场和电商平台的数据采集任务。',
    content: <CollectionTasksPage />
  },
  analysis: {
    title: '价格数据分析',
    description: '按地区、品类、市场和时间维度分析价格走势、分布与波动。',
    content: <PriceMultiAnalysisPage />
  },
  prediction: {
    title: '趋势预测',
    description: '融合历史价格、气象因子和节令特征，输出短期趋势预测。',
    content: <TrendPredictionPage />
  },
  alerts: {
    title: '价格预警中心',
    description: '管理涨跌幅、缺失率、采集失败和异常价格等预警规则。',
    content: <WorkflowContent type="alerts" />
  },
  settings: {
    title: '系统配置',
    description: '维护数据源、质量规则、机构权限、调度频率和接口配置。',
    content: <WorkflowContent type="settings" />
  }
}

export function AppShell() {
  const [activeKey, setActiveKey] = useState('dashboard')
  const [collapsed, setCollapsed] = useState(false)

  const activeNav = useMemo(() => navigationItems.find((item) => item.key === activeKey), [activeKey])
  const activePage = pages[activeKey]

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-950">
      <Sidebar
        activeKey={activeKey}
        collapsed={collapsed}
        onCollapseChange={setCollapsed}
        onNavigate={setActiveKey}
      />
      <div className={cn('min-h-screen transition-all duration-300', collapsed ? 'pl-[76px]' : 'pl-[248px]')}>
        <Header breadcrumbs={activeNav.breadcrumb} />
        <main className="thin-scrollbar h-[calc(100vh-64px)] overflow-y-auto bg-[#f8fafc] px-6 py-6">
          <section key={activeKey} className="page-transition mx-auto max-w-[1480px] space-y-6">
            <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">Enterprise Shell</Badge>
                  <Badge>实时监控</Badge>
                </div>
                <div>
                  <h1 className="text-2xl font-semibold tracking-normal text-slate-950">{activePage.title}</h1>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{activePage.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="secondary">导出快照</Button>
                <Button>刷新数据</Button>
              </div>
            </div>
            {activePage.content}
          </section>
        </main>
      </div>
    </div>
  )
}

function DashboardContent() {
  const metrics = [
    { label: '今日采集记录', value: '126,840', change: '+12.4%', trend: 'up', icon: Database },
    { label: '覆盖市场主体', value: '1,528', change: '+36', trend: 'up', icon: ServerCog },
    { label: '重点农产品', value: '512', change: '+18', trend: 'up', icon: Sprout },
    { label: '异常波动预警', value: '24', change: '-8.1%', trend: 'down', icon: TrendingUp }
  ]

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon
          const TrendIcon = metric.trend === 'up' ? ArrowUpRight : ArrowDownRight
          return (
            <div key={metric.label} className="rounded-lg border bg-white p-5 shadow-panel">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm text-slate-500">{metric.label}</p>
                  <p className="mt-3 text-2xl font-semibold text-slate-950">{metric.value}</p>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-forest-50 text-forest-700">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-1 text-sm">
                <TrendIcon className={cn('h-4 w-4', metric.trend === 'up' ? 'text-forest-600' : 'text-red-500')} />
                <span className={metric.trend === 'up' ? 'text-forest-700' : 'text-red-600'}>{metric.change}</span>
                <span className="text-slate-400">较上一批次</span>
              </div>
            </div>
          )
        })}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
        <Panel title="全国价格指数趋势" caption="ECharts 折线图区域，后续接入 /api/price-trends">
          <div className="flex h-80 items-end gap-2 rounded-lg border bg-slate-50 p-5">
            {[42, 48, 44, 58, 62, 57, 66, 73, 69, 78, 86, 82].map((height, index) => (
              <div key={index} className="flex flex-1 flex-col items-center justify-end gap-2">
                <div className="w-full rounded-t-sm bg-forest-600" style={{ height: `${height}%` }} />
                <span className="text-xs text-slate-400">{index + 1}</span>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="预警优先级" caption="高风险价格波动、采集失败和质量异常统一收敛">
          <div className="space-y-3">
            {[
              ['山东 番茄', '涨幅 18.6%', 'warning'],
              ['四川 玉米', '缺失率 4.1%', 'outline'],
              ['河南 苹果', '跌幅 12.2%', 'danger']
            ].map(([name, detail, variant]) => (
              <div key={name} className="flex items-center justify-between rounded-lg border bg-white px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-900">{name}</p>
                  <p className="mt-1 text-xs text-slate-500">{detail}</p>
                </div>
                <Badge variant={variant}>{variant === 'danger' ? '高' : variant === 'warning' ? '中' : '低'}</Badge>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  )
}

function WorkflowContent({ type }) {
  const copy = {
    collection: ['任务调度', '数据源接入', '采集日志', '失败重试'],
    analysis: ['价格走势', '地区对比', '品类分布', '质量画像'],
    prediction: ['特征工程', '模型评估', '趋势曲线', '预测解释'],
    alerts: ['规则配置', '告警队列', '处置流程', '通知策略'],
    settings: ['机构权限', '质量阈值', '接口密钥', '系统审计']
  }[type]

  return (
    <div className="grid gap-4 lg:grid-cols-4">
      {copy.map((item, index) => (
        <div key={item} className="rounded-lg border bg-white p-5 shadow-panel">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border bg-slate-50 text-forest-700">{index + 1}</div>
          <h2 className="mt-4 text-base font-semibold text-slate-950">{item}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">这里承载该模块的核心表格、筛选器、图表或配置面板，保持无刷新切换。</p>
        </div>
      ))}
    </div>
  )
}

function Panel({ title, caption, children }) {
  return (
    <section className="rounded-lg border bg-white p-5 shadow-panel">
      <div className="mb-4">
        <h2 className="text-base font-semibold text-slate-950">{title}</h2>
        <p className="mt-1 text-sm text-slate-500">{caption}</p>
      </div>
      {children}
    </section>
  )
}