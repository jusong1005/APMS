import {
  ActivitySquare,
  BellRing,
  BrainCircuit,
  ClipboardList,
  LineChart,
  Monitor,
  Settings,
  UsersRound
} from 'lucide-vue-next'

export const navigationItems = [
  {
    key: 'screen',
    label: '监控大屏',
    icon: Monitor,
    breadcrumb: ['农产品价格监控', '监控大屏']
  },
  {
    key: 'dashboard',
    label: '监控大盘',
    icon: ActivitySquare,
    breadcrumb: ['农产品价格监控', '监控大盘']
  },
  {
    key: 'collection',
    label: '采集任务管理',
    icon: ClipboardList,
    breadcrumb: ['农产品价格监控', '采集任务管理']
  },
  {
    key: 'analysis',
    label: '价格数据分析',
    icon: LineChart,
    breadcrumb: ['农产品价格监控', '价格数据分析']
  },
  {
    key: 'prediction',
    label: '趋势预测',
    icon: BrainCircuit,
    breadcrumb: ['农产品价格监控', '趋势预测']
  },
  {
    key: 'alerts',
    label: '价格预警中心',
    icon: BellRing,
    breadcrumb: ['农产品价格监控', '价格预警中心']
  },
  {
    key: 'users',
    label: '用户权限管理',
    icon: UsersRound,
    breadcrumb: ['农产品价格监控', '用户权限管理']
  },
  {
    key: 'settings',
    label: '系统配置',
    icon: Settings,
    breadcrumb: ['农产品价格监控', '系统配置']
  }
]