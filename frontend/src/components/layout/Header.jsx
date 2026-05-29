import { useEffect, useMemo, useState } from 'react'
import { Bell, ChevronRight, Clock3, ShieldCheck } from 'lucide-react'
import { Avatar, AvatarFallback } from '../ui/avatar.jsx'
import { Badge } from '../ui/badge.jsx'
import { Button } from '../ui/button.jsx'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '../ui/dropdown-menu.jsx'
import { Separator } from '../ui/separator.jsx'

const notifications = [
  { title: '新发地采集任务完成', detail: '本批次 12,480 条价格记录已入湖', level: 'default' },
  { title: '山东番茄价格波动', detail: '近 24 小时涨幅 18.6%，进入观察区间', level: 'warning' },
  { title: '质量规则校验通过', detail: '缺失率 0.7%，重复率 0.2%', level: 'default' }
]

export function Header({ breadcrumbs }) {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000)
    return () => window.clearInterval(timer)
  }, [])

  const marketTime = useMemo(() => {
    return new Intl.DateTimeFormat('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(now)
  }, [now])

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-white/95 px-6 shadow-sm backdrop-blur">
      <div className="flex min-w-0 items-center gap-2 text-sm text-slate-500">
        {breadcrumbs.map((crumb, index) => (
          <div key={crumb} className="flex items-center gap-2">
            <span className={index === breadcrumbs.length - 1 ? 'font-medium text-slate-900' : undefined}>{crumb}</span>
            {index < breadcrumbs.length - 1 && <ChevronRight className="h-4 w-4 text-slate-300" />}
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-lg border bg-slate-50 px-3 py-2 text-sm text-slate-600 md:flex">
          <Clock3 className="h-4 w-4 text-forest-600" />
          <span>当前市场时间</span>
          <Separator orientation="vertical" className="h-4" />
          <span className="font-medium text-slate-900">{marketTime}</span>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="secondary" size="icon" className="relative">
              <Bell className="h-4 w-4" />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-red-500" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-80">
            <DropdownMenuLabel className="flex items-center justify-between">
              <span>实时系统通知</span>
              <Badge variant="outline">3 条</Badge>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {notifications.map((item) => (
              <DropdownMenuItem key={item.title} className="items-start">
                <ShieldCheck className="mt-0.5 h-4 w-4 text-forest-600" />
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-slate-900">{item.title}</p>
                    {item.level === 'warning' && <Badge variant="warning">关注</Badge>}
                  </div>
                  <p className="text-xs leading-5 text-slate-500">{item.detail}</p>
                </div>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="flex items-center gap-3 rounded-lg border bg-white px-2.5 py-1.5 shadow-sm">
          <Avatar>
            <AvatarFallback>农</AvatarFallback>
          </Avatar>
          <div className="hidden min-w-0 pr-1 lg:block">
            <p className="truncate text-sm font-semibold text-slate-900">国家农产品监测中心</p>
            <p className="truncate text-xs text-slate-500">数据运营专员</p>
          </div>
        </div>
      </div>
    </header>
  )
}