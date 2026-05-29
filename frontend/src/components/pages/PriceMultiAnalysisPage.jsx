import { useMemo, useState } from 'react'
import {
  AlertTriangle,
  Lightbulb,
  MapPin,
  TrendingUp
} from 'lucide-react'
import { Badge } from '../ui/badge.jsx'
import { Button } from '../ui/button.jsx'
import { cn } from '../../lib/utils.js'

const timeRanges = [
  { value: '7d', label: '近 7 天', days: 7 },
  { value: '30d', label: '近 30 天', days: 30 },
  { value: '90d', label: '近 90 天', days: 90 },
  { value: '180d', label: '近半年', days: 180 }
]

const categories = [
  { value: 'vegetable', label: '蔬菜', product: '大白菜' },
  { value: 'fruit', label: '水果', product: '苹果' },
  { value: 'livestock', label: '畜禽', product: '鸡蛋' }
]

const regions = ['山东', '河南', '四川', '北京']

const regionColors = {
  山东: '#166534',
  河南: '#bd7b18',
  四川: '#0f766e',
  北京: '#b91c1c'
}

const baseSeries = {
  vegetable: {
    山东: [2.2, 2.3, 2.35, 2.42, 2.48, 2.53, 2.61, 2.68],
    河南: [2.05, 2.12, 2.18, 2.24, 2.31, 2.38, 2.44, 2.51],
    四川: [2.34, 2.38, 2.43, 2.49, 2.58, 2.63, 2.71, 2.76],
    北京: [2.65, 2.71, 2.78, 2.85, 2.92, 2.96, 3.02, 3.08]
  },
  fruit: {
    山东: [6.8, 6.72, 6.76, 6.84, 6.95, 7.08, 7.12, 7.2],
    河南: [6.42, 6.51, 6.55, 6.63, 6.71, 6.82, 6.9, 7.01],
    四川: [7.1, 7.04, 7.16, 7.22, 7.31, 7.45, 7.52, 7.61],
    北京: [7.48, 7.55, 7.63, 7.7, 7.82, 7.91, 8.03, 8.12]
  },
  livestock: {
    山东: [9.8, 9.92, 10.04, 10.16, 10.21, 10.28, 10.36, 10.44],
    河南: [9.55, 9.61, 9.7, 9.82, 9.9, 10.02, 10.11, 10.18],
    四川: [10.12, 10.2, 10.29, 10.37, 10.48, 10.6, 10.68, 10.75],
    北京: [10.45, 10.58, 10.64, 10.79, 10.92, 11.04, 11.16, 11.24]
  }
}

export function PriceMultiAnalysisPage() {
  const [timeRange, setTimeRange] = useState('30d')
  const [category, setCategory] = useState('vegetable')
  const [selectedRegions, setSelectedRegions] = useState(['山东', '河南', '四川'])

  const product = categories.find((item) => item.value === category).product
  const series = useMemo(() => {
    const scale = timeRanges.find((item) => item.value === timeRange).days / 30
    return selectedRegions.map((region) => {
      const values = baseSeries[category][region].map((value, index) => roundPrice(value + (scale - 1) * 0.03 * index))
      return { region, values, color: regionColors[region] }
    })
  }, [category, selectedRegions, timeRange])

  const stats = useMemo(() => {
    const latestValues = series.map((item) => item.values[item.values.length - 1])
    const previousValues = series.map((item) => item.values[item.values.length - 2])
    const currentAvg = average(latestValues)
    const previousAvg = average(previousValues)
    const change = ((currentAvg - previousAvg) / previousAvg) * 100
    return {
      highest: Math.max(...latestValues),
      lowest: Math.min(...latestValues),
      average: currentAvg,
      change,
      leader: series.reduce((top, item) => {
        const latest = item.values[item.values.length - 1]
        return latest > top.value ? { region: item.region, value: latest } : top
      }, { region: '', value: -Infinity })
    }
  }, [series])

  const toggleRegion = (region) => {
    setSelectedRegions((current) => {
      if (current.includes(region)) {
        return current.length === 1 ? current : current.filter((item) => item !== region)
      }
      return [...current, region]
    })
  }

  return (
    <div className="space-y-4">
      <section className="rounded-lg border bg-white p-4 shadow-panel">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-950">多维筛选器</h2>
            <p className="mt-1 text-sm text-slate-500">按时间跨度、产品品类和地区维度组合分析农产品价格走势。</p>
          </div>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <select
              value={timeRange}
              onChange={(event) => setTimeRange(event.target.value)}
              className="h-9 rounded-md border bg-white px-3 text-sm text-slate-700 shadow-sm outline-none transition-colors focus:border-forest-500 focus:ring-2 focus:ring-forest-100"
              aria-label="时间跨度"
            >
              {timeRanges.map((range) => (
                <option key={range.value} value={range.value}>{range.label}</option>
              ))}
            </select>

            <div className="flex rounded-md border bg-slate-50 p-1">
              {categories.map((item) => (
                <button
                  key={item.value}
                  className={cn(
                    'h-8 rounded-sm px-3 text-sm font-medium transition-colors',
                    category === item.value ? 'bg-white text-forest-800 shadow-sm' : 'text-slate-500 hover:text-slate-900'
                  )}
                  onClick={() => setCategory(item.value)}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap gap-2">
              {regions.map((region) => (
                <Button
                  key={region}
                  variant={selectedRegions.includes(region) ? 'default' : 'secondary'}
                  size="sm"
                  onClick={() => toggleRegion(region)}
                >
                  <MapPin className="h-3.5 w-3.5" />
                  {region}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <section className="rounded-lg border bg-white p-5 shadow-panel">
          <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-semibold text-slate-950">{product} 多地区价格走势</h2>
                <Badge variant="outline">多轴折线</Badge>
              </div>
              <p className="mt-1 text-sm text-slate-500">左轴为价格，右轴为价格波动指数，对比不同地区同一品种走势。</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {series.map((item) => (
                <span key={item.region} className="inline-flex items-center gap-2 text-xs text-slate-500">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  {item.region}
                </span>
              ))}
            </div>
          </div>
          <MultiAxisLineChart series={series} />
        </section>

        <section className="rounded-lg border bg-white p-5 shadow-panel">
          <div className="mb-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-base font-semibold text-slate-950">价格梯度图</h2>
              <Badge>当前市场</Badge>
            </div>
            <p className="mt-1 text-sm text-slate-500">展示最高价、均价和最低价分布。</p>
          </div>
          <PriceGradient stats={stats} product={product} />
        </section>
      </div>

      <InsightBriefing product={product} stats={stats} regions={selectedRegions} />
    </div>
  )
}

function MultiAxisLineChart({ series }) {
  const width = 860
  const height = 360
  const padding = { top: 28, right: 64, bottom: 46, left: 58 }
  const allValues = series.flatMap((item) => item.values)
  const minValue = Math.min(...allValues) - 0.15
  const maxValue = Math.max(...allValues) + 0.15
  const steps = series[0]?.values.length || 0
  const points = Array.from({ length: steps }, (_, index) => index)

  const x = (index) => padding.left + (index / (steps - 1)) * (width - padding.left - padding.right)
  const y = (value) => padding.top + ((maxValue - value) / (maxValue - minValue)) * (height - padding.top - padding.bottom)
  const pathFor = (values) => values.map((value, index) => `${index === 0 ? 'M' : 'L'} ${x(index)} ${y(value)}`).join(' ')
  const gridValues = [maxValue, (maxValue + minValue) / 2, minValue]

  return (
    <div className="h-[360px] overflow-hidden rounded-lg border bg-slate-50">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="多地区价格走势折线图" className="h-full w-full">
        <rect width={width} height={height} fill="#f8fafc" />
        {gridValues.map((value) => (
          <g key={value}>
            <line x1={padding.left} x2={width - padding.right} y1={y(value)} y2={y(value)} stroke="#e2e8f0" strokeDasharray="4 6" />
            <text x={padding.left - 12} y={y(value) + 4} textAnchor="end" fontSize="12" fill="#64748b">{value.toFixed(2)}</text>
            <text x={width - padding.right + 12} y={y(value) + 4} fontSize="12" fill="#64748b">{priceIndex(value, minValue, maxValue)}</text>
          </g>
        ))}
        <line x1={padding.left} x2={padding.left} y1={padding.top} y2={height - padding.bottom} stroke="#cbd5e1" />
        <line x1={width - padding.right} x2={width - padding.right} y1={padding.top} y2={height - padding.bottom} stroke="#cbd5e1" />
        <line x1={padding.left} x2={width - padding.right} y1={height - padding.bottom} y2={height - padding.bottom} stroke="#cbd5e1" />

        {series.map((item) => (
          <g key={item.region}>
            <path d={pathFor(item.values)} fill="none" stroke={item.color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            {item.values.map((value, index) => (
              <circle key={`${item.region}-${index}`} cx={x(index)} cy={y(value)} r="4" fill="#fff" stroke={item.color} strokeWidth="2" />
            ))}
          </g>
        ))}

        {points.map((index) => (
          <text key={index} x={x(index)} y={height - 18} textAnchor="middle" fontSize="12" fill="#64748b">W{index + 1}</text>
        ))}
        <text x={padding.left} y="18" fontSize="12" fill="#475569">价格（元/公斤）</text>
        <text x={width - padding.right} y="18" textAnchor="end" fontSize="12" fill="#475569">波动指数</text>
      </svg>
    </div>
  )
}

function PriceGradient({ stats, product }) {
  const range = stats.highest - stats.lowest || 1
  const avgOffset = ((stats.average - stats.lowest) / range) * 100

  return (
    <div className="space-y-5">
      <div className="rounded-lg border bg-slate-50 p-4">
        <div className="mb-3 flex items-center justify-between text-sm">
          <span className="text-slate-500">品种</span>
          <span className="font-medium text-slate-950">{product}</span>
        </div>
        <div className="relative h-64 rounded-lg border bg-white p-5">
          <div className="absolute left-1/2 top-6 h-52 w-8 -translate-x-1/2 rounded-full bg-gradient-to-t from-forest-600 via-harvest-400 to-red-500 shadow-inner" />
          <GradientMark label="最高价" value={stats.highest} top="9%" tone="red" />
          <GradientMark label="均价" value={stats.average} top={`${100 - avgOffset}%`} tone="amber" />
          <GradientMark label="最低价" value={stats.lowest} top="78%" tone="green" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <MiniStat label="最高" value={stats.highest} />
        <MiniStat label="均价" value={stats.average} />
        <MiniStat label="最低" value={stats.lowest} />
      </div>
    </div>
  )
}

function GradientMark({ label, value, top, tone }) {
  const toneClass = {
    red: 'border-red-200 bg-red-50 text-red-700',
    amber: 'border-amber-200 bg-amber-50 text-amber-800',
    green: 'border-forest-100 bg-forest-50 text-forest-700'
  }[tone]

  return (
    <div className="absolute left-[calc(50%+34px)] flex items-center gap-2" style={{ top }}>
      <span className="h-px w-9 bg-slate-300" />
      <span className={cn('rounded-md border px-2 py-1 text-xs font-medium', toneClass)}>
        {label} {value.toFixed(2)}
      </span>
    </div>
  )
}

function MiniStat({ label, value }) {
  return (
    <div className="rounded-lg border bg-white p-3 text-center">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-950">{value.toFixed(2)}</p>
    </div>
  )
}

function InsightBriefing({ product, stats, regions }) {
  const changeLabel = `${stats.change >= 0 ? '上涨' : '下降'}${Math.abs(stats.change).toFixed(1)}%`
  const briefings = [
    { icon: TrendingUp, title: '本周价格简报', text: `${product} 较上周环比${changeLabel}，均价为 ${stats.average.toFixed(2)} 元/公斤。`, tone: 'green' },
    { icon: MapPin, title: '区域分化', text: `${stats.leader.region} 当前价格最高，覆盖对比地区 ${regions.length} 个。`, tone: 'amber' },
    { icon: AlertTriangle, title: '波动提示', text: stats.change > 4 ? '涨幅超过常规观察线，建议进入价格预警中心跟踪。' : '价格处于正常波动区间，可保持常规监控。', tone: stats.change > 4 ? 'red' : 'green' },
    { icon: Lightbulb, title: '运营建议', text: '建议结合采集任务成功率和气象影响数据判断短期供应压力。', tone: 'slate' }
  ]

  return (
    <section className="rounded-lg border bg-white p-5 shadow-panel">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-950">数据洞察区</h2>
          <p className="mt-1 text-sm text-slate-500">根据筛选结果自动生成本周价格简报。</p>
        </div>
        <Badge variant="outline">自动生成</Badge>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {briefings.map((item) => {
          const Icon = item.icon
          return (
            <div key={item.title} className="rounded-lg border bg-slate-50 p-4">
              <div className="flex items-center gap-2">
                <InsightIcon tone={item.tone} icon={Icon} />
                <h3 className="text-sm font-semibold text-slate-950">{item.title}</h3>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-600">{item.text}</p>
            </div>
          )
        })}
      </div>
    </section>
  )
}

function InsightIcon({ icon: Icon, tone }) {
  const toneClass = {
    green: 'bg-forest-50 text-forest-700 border-forest-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
    red: 'bg-red-50 text-red-700 border-red-100',
    slate: 'bg-slate-100 text-slate-600 border-slate-200'
  }[tone]
  return (
    <span className={cn('flex h-8 w-8 items-center justify-center rounded-lg border', toneClass)}>
      <Icon className="h-4 w-4" />
    </span>
  )
}

function average(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

function roundPrice(value) {
  return Math.round(value * 100) / 100
}

function priceIndex(value, min, max) {
  const index = 80 + ((value - min) / (max - min)) * 40
  return Math.round(index)
}