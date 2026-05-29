import { useEffect, useMemo, useRef, useState } from 'react'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, MarkLineComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { AlertTriangle, BrainCircuit, CloudSun, Route, Sparkles, TrendingUp } from 'lucide-react'
import { Badge } from '../ui/badge.jsx'
import { cn } from '../../lib/utils.js'

echarts.use([LineChart, BarChart, GridComponent, LegendComponent, MarkLineComponent, TooltipComponent, CanvasRenderer])

const models = [
  {
    key: 'timeSeries',
    label: '时间序列模型',
    summary: '捕捉历史价格周期与短期波动，适合连续交易日趋势外推。',
    threshold: 3.18,
    forecastBase: [2.88, 2.9, 2.93, 2.96, 2.99, 3.01, 3.04, 3.06, 3.08, 3.1, 3.12, 3.14, 3.15, 3.17, 3.19, 3.2, 3.22, 3.23, 3.24, 3.25, 3.27, 3.28, 3.29, 3.3, 3.32, 3.33, 3.34, 3.35, 3.36, 3.38],
    weights: [32, 21, 16, 13, 10, 8]
  },
  {
    key: 'randomForest',
    label: '随机森林模型',
    summary: '融合多源特征判断非线性影响，适合解释关键因子贡献。',
    threshold: 3.24,
    forecastBase: [2.88, 2.91, 2.94, 2.95, 2.97, 3.0, 3.02, 3.03, 3.05, 3.08, 3.1, 3.11, 3.12, 3.14, 3.16, 3.17, 3.18, 3.19, 3.21, 3.22, 3.23, 3.24, 3.25, 3.26, 3.27, 3.28, 3.29, 3.3, 3.31, 3.32],
    weights: [24, 28, 18, 15, 9, 6]
  },
  {
    key: 'deepLearning',
    label: '深度学习模型',
    summary: '识别多变量长期关联，适合高维气象与市场信号联合预测。',
    threshold: 3.3,
    forecastBase: [2.88, 2.9, 2.94, 2.98, 3.01, 3.05, 3.08, 3.11, 3.14, 3.18, 3.2, 3.23, 3.26, 3.28, 3.31, 3.33, 3.36, 3.38, 3.41, 3.43, 3.45, 3.48, 3.5, 3.52, 3.55, 3.57, 3.59, 3.61, 3.64, 3.66],
    weights: [19, 24, 21, 17, 11, 8]
  }
]

const factorLabels = ['季节因素', '气象灾害', '运输成本', '市场供需', '节假日需求', '采集质量']
const factorIcons = [CloudSun, AlertTriangle, Route, TrendingUp, Sparkles, BrainCircuit]
const historyPrices = [2.54, 2.56, 2.58, 2.57, 2.6, 2.62, 2.64, 2.67, 2.66, 2.69, 2.71, 2.73, 2.72, 2.75, 2.77, 2.78, 2.8, 2.79, 2.82, 2.83, 2.85, 2.84, 2.86, 2.87]

export function TrendPredictionPage() {
  const [activeModelKey, setActiveModelKey] = useState('timeSeries')
  const activeModel = models.find((model) => model.key === activeModelKey)

  const chartData = useMemo(() => buildPredictionData(activeModel), [activeModel])
  const factorData = useMemo(() => buildFactorData(activeModel.weights), [activeModel])
  const forecastMax = Math.max(...activeModel.forecastBase)
  const isWarning = forecastMax > activeModel.threshold
  const peakDay = activeModel.forecastBase.findIndex((price) => price === forecastMax) + 1

  const predictionOption = useMemo(() => buildPredictionOption(chartData, activeModel.threshold), [chartData, activeModel.threshold])
  const factorOption = useMemo(() => buildFactorOption(factorData), [factorData])

  return (
    <div className="space-y-4">
      <section className="rounded-lg border bg-white p-4 shadow-panel">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-950">预测模型选择</h2>
            <p className="mt-1 text-sm leading-6 text-slate-500">{activeModel.summary}</p>
          </div>
          <div className="grid rounded-md border bg-slate-50 p-1 sm:grid-cols-3">
            {models.map((model) => (
              <button
                key={model.key}
                className={cn(
                  'h-9 rounded-sm px-3 text-sm font-medium transition-colors',
                  activeModelKey === model.key ? 'bg-white text-forest-800 shadow-sm' : 'text-slate-500 hover:text-slate-900'
                )}
                onClick={() => setActiveModelKey(model.key)}
              >
                {model.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section
        className={cn(
          'rounded-lg border p-4 shadow-panel',
          isWarning ? 'border-red-200 bg-red-50' : 'border-forest-100 bg-forest-50'
        )}
      >
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-3">
            <span
              className={cn(
                'flex h-11 w-11 items-center justify-center rounded-lg border bg-white',
                isWarning ? 'border-red-200 text-red-600' : 'border-forest-100 text-forest-700'
              )}
            >
              <AlertTriangle className="h-5 w-5" />
            </span>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className={cn('text-base font-semibold', isWarning ? 'text-red-900' : 'text-forest-900')}>
                  {isWarning ? '预测价格超过预警阈值' : '预测价格处于安全区间'}
                </h2>
                <Badge variant={isWarning ? 'danger' : 'default'}>{isWarning ? '高风险' : '正常'}</Badge>
              </div>
              <p className={cn('mt-1 text-sm leading-6', isWarning ? 'text-red-700' : 'text-forest-700')}>
                未来 30 天最高预测价 {forecastMax.toFixed(2)} 元/公斤，阈值 {activeModel.threshold.toFixed(2)} 元/公斤，预计第 {peakDay} 天达到峰值。
              </p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center sm:min-w-[360px]">
            <MetricPill label="历史末值" value={historyPrices.at(-1)} />
            <MetricPill label="预测峰值" value={forecastMax} danger={isWarning} />
            <MetricPill label="阈值" value={activeModel.threshold} />
          </div>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[1.6fr_0.9fr]">
        <section className="rounded-lg border bg-white p-5 shadow-panel">
          <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-semibold text-slate-950">置信区间预测图</h2>
                <Badge variant="outline">ECharts</Badge>
              </div>
              <p className="mt-1 text-sm text-slate-500">历史价格使用实线，未来 30 天预测使用虚线，浅色阴影表示波动区间。</p>
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-slate-500">
              <LegendDot color="#166534" label="历史数据" />
              <LegendDot color="#bd7b18" label="预测数据" dashed />
              <LegendDot color="rgba(34,197,94,0.28)" label="波动区间" />
            </div>
          </div>
          <EChart option={predictionOption} className="h-[430px]" ariaLabel="置信区间预测图" />
        </section>

        <section className="rounded-lg border bg-white p-5 shadow-panel">
          <div className="mb-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-base font-semibold text-slate-950">预测因子分析</h2>
              <Badge>影响因素权重</Badge>
            </div>
            <p className="mt-1 text-sm text-slate-500">横向柱状图展示不同因素对预测结果的贡献。</p>
          </div>
          <EChart option={factorOption} className="h-[318px]" ariaLabel="影响因素权重横向柱状图" />
          <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {factorData.slice(0, 4).map((factor, index) => {
              const Icon = factorIcons[index]
              return (
                <div key={factor.name} className="flex items-center justify-between rounded-lg border bg-slate-50 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg border bg-white text-forest-700">
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="text-sm font-medium text-slate-800">{factor.name}</span>
                  </div>
                  <span className="text-sm font-semibold text-slate-950">{factor.value}%</span>
                </div>
              )
            })}
          </div>
        </section>
      </div>
    </div>
  )
}

function EChart({ option, className, ariaLabel }) {
  const chartRef = useRef(null)
  const chartInstanceRef = useRef(null)

  useEffect(() => {
    if (!chartRef.current) return undefined

    const chart = echarts.init(chartRef.current)
    chartInstanceRef.current = chart

    const resize = () => chart.resize()
    window.addEventListener('resize', resize)

    let resizeObserver
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(resize)
      resizeObserver.observe(chartRef.current)
    }

    return () => {
      window.removeEventListener('resize', resize)
      resizeObserver?.disconnect()
      chart.dispose()
      chartInstanceRef.current = null
    }
  }, [])

  useEffect(() => {
    chartInstanceRef.current?.setOption(option, true)
  }, [option])

  return <div ref={chartRef} role="img" aria-label={ariaLabel} className={cn('w-full rounded-lg border bg-slate-50', className)} />
}

function MetricPill({ label, value, danger = false }) {
  return (
    <div className="rounded-lg border bg-white px-3 py-2">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={cn('mt-1 text-base font-semibold', danger ? 'text-red-700' : 'text-slate-950')}>{value.toFixed(2)}</p>
    </div>
  )
}

function LegendDot({ color, label, dashed = false }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className={cn('h-0 w-8 border-t-2', dashed && 'border-dashed')} style={{ borderColor: color }} />
      {label}
    </span>
  )
}

function buildPredictionData(model) {
  const historyLabels = Array.from({ length: historyPrices.length }, (_, index) => `历史${index + 1}`)
  const forecastLabels = Array.from({ length: 30 }, (_, index) => `未来${index + 1}`)
  const labels = [...historyLabels, ...forecastLabels]
  const forecastStart = historyPrices.length - 1
  const forecastLine = [
    ...Array(forecastStart).fill(null),
    historyPrices.at(-1),
    ...model.forecastBase
  ]
  const historyLine = [...historyPrices, ...Array(30).fill(null)]
  const bandLower = [...Array(forecastStart).fill(null), historyPrices.at(-1) - 0.08, ...model.forecastBase.map((price, index) => roundPrice(price - 0.1 - index * 0.006))]
  const bandWidth = [...Array(forecastStart).fill(null), 0.16, ...model.forecastBase.map((_, index) => roundPrice(0.22 + index * 0.012))]

  return { labels, historyLine, forecastLine, bandLower, bandWidth }
}

function buildPredictionOption(data, threshold) {
  return {
    color: ['#166534', '#bd7b18', '#22c55e'],
    grid: { left: 46, right: 28, top: 36, bottom: 44 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line' },
      valueFormatter: (value) => (typeof value === 'number' ? `${value.toFixed(2)} 元/公斤` : value)
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.labels,
      axisLabel: { color: '#64748b', interval: 5 },
      axisLine: { lineStyle: { color: '#cbd5e1' } }
    },
    yAxis: {
      type: 'value',
      name: '元/公斤',
      min: 2.4,
      max: 3.9,
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } }
    },
    series: [
      {
        name: '区间下界',
        type: 'line',
        stack: 'confidence-band',
        data: data.bandLower,
        symbol: 'none',
        lineStyle: { opacity: 0 },
        tooltip: { show: false },
        emphasis: { disabled: true }
      },
      {
        name: '波动区间',
        type: 'line',
        stack: 'confidence-band',
        data: data.bandWidth,
        symbol: 'none',
        lineStyle: { opacity: 0 },
        areaStyle: { color: 'rgba(34, 197, 94, 0.18)' },
        tooltip: { show: false },
        emphasis: { disabled: true }
      },
      {
        name: '历史数据',
        type: 'line',
        data: data.historyLine,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#166534' }
      },
      {
        name: '预测数据',
        type: 'line',
        data: data.forecastLine,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#bd7b18', type: 'dashed' },
        markLine: {
          symbol: 'none',
          label: { formatter: `预警阈值 ${threshold.toFixed(2)}`, color: '#b91c1c' },
          lineStyle: { color: '#ef4444', type: 'dashed' },
          data: [{ yAxis: threshold }]
        }
      }
    ]
  }
}

function buildFactorData(weights) {
  return factorLabels.map((name, index) => ({ name, value: weights[index] })).sort((first, second) => first.value - second.value)
}

function buildFactorOption(data) {
  return {
    grid: { left: 82, right: 28, top: 16, bottom: 24 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (value) => `${value}%`
    },
    xAxis: {
      type: 'value',
      max: 36,
      axisLabel: { color: '#64748b', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: data.map((item) => item.name),
      axisLabel: { color: '#475569' },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [
      {
        name: '权重',
        type: 'bar',
        data: data.map((item) => item.value),
        barWidth: 18,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: '#166534'
        },
        label: {
          show: true,
          position: 'right',
          color: '#0f172a',
          formatter: '{c}%'
        }
      }
    ]
  }
}

function roundPrice(value) {
  return Math.round(value * 100) / 100
}