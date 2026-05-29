import { ChevronLeft, ChevronRight, Leaf } from 'lucide-react'
import { Button } from '../ui/button.jsx'
import { cn } from '../../lib/utils.js'
import { navigationItems } from './navigation.js'

export function Sidebar({ activeKey, collapsed, onCollapseChange, onNavigate }) {
  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-30 flex flex-col border-r border-white/10 bg-forest-950 text-white shadow-xl transition-all duration-300',
        collapsed ? 'w-[76px]' : 'w-[248px]'
      )}
    >
      <div className="flex h-16 items-center gap-3 border-b border-white/10 px-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-white/15 bg-white/10">
          <Leaf className="h-5 w-5 text-emerald-200" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-normal">农产品价格平台</p>
            <p className="truncate text-xs text-emerald-100/70">Agri Price Monitor</p>
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigationItems.map((item) => {
          const Icon = item.icon
          const active = item.key === activeKey
          return (
            <Button
              key={item.key}
              variant="sidebar"
              data-active={active}
              title={collapsed ? item.label : undefined}
              className={cn(
                'h-11 w-full justify-start rounded-lg px-3 text-sm',
                collapsed && 'justify-center px-0',
                active && 'shadow-sm'
              )}
              onClick={() => onNavigate(item.key)}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Button>
          )
        })}
      </nav>

      <div className="border-t border-white/10 p-3">
        <Button
          variant="sidebar"
          size={collapsed ? 'icon' : 'default'}
          className={cn('w-full rounded-lg', collapsed ? 'justify-center' : 'justify-between')}
          onClick={() => onCollapseChange(!collapsed)}
        >
          {!collapsed && <span>收起侧边栏</span>}
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>
    </aside>
  )
}