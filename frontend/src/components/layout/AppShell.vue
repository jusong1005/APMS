<script setup>
import { computed, ref } from 'vue'
import Header from './Header.vue'
import Sidebar from './Sidebar.vue'
import { navigationItems } from './navigation.js'
import DashboardPage from '../pages/DashboardPage.vue'
import CollectionTasksPage from '../pages/CollectionTasksPage.vue'
import PriceMultiAnalysisPage from '../pages/PriceMultiAnalysisPage.vue'
import TrendPredictionPage from '../pages/TrendPredictionPage.vue'
import AlertsCenterPage from '../pages/AlertsCenterPage.vue'
import UserPermissionCenterPage from '../pages/UserPermissionCenterPage.vue'
import SettingsCenterPage from '../pages/SettingsCenterPage.vue'
import ProfileSettingsPage from '../pages/ProfileSettingsPage.vue'
import Badge from '../ui/Badge.vue'
import Button from '../ui/Button.vue'

const activeKey = ref('dashboard')
const collapsed = ref(false)

const pages = {
  dashboard: {
    title: '全国农产品价格监控大盘',
    description: '汇总采集、清洗、入库、价格波动和预警状态，支撑全国市场价格监测。',
    component: DashboardPage
  },
  collection: {
    title: '采集任务管理',
    description: '统一编排批发市场、农贸市场和电商平台的数据采集任务。',
    component: CollectionTasksPage
  },
  analysis: {
    title: '价格数据分析',
    description: '按地区、品类、市场和时间维度分析价格走势、分布与波动。',
    component: PriceMultiAnalysisPage
  },
  prediction: {
    title: '趋势预测',
    description: '融合历史价格、气象因子和节令特征，输出短期趋势预测。',
    component: TrendPredictionPage
  },
  alerts: {
    title: '价格预警中心',
    description: '管理涨跌幅、缺失率、采集失败和异常价格等预警规则。',
    component: AlertsCenterPage
  },
  users: {
    title: '用户权限管理',
    description: '统一维护平台用户、角色、所属机构和关键操作权限。',
    component: UserPermissionCenterPage
  },
  settings: {
    title: '系统配置',
    description: '维护数据源、质量规则、机构权限、调度频率和接口配置。',
    component: SettingsCenterPage
  },
  profile: {
    title: '个人设置',
    description: '欢迎回来，管理员张建国。管理个人资料、安全策略、监控偏好和消息通知。',
    breadcrumb: ['农产品价格监控', '个人设置'],
    component: ProfileSettingsPage
  }
}

const activePage = computed(() => pages[activeKey.value])
const activeNav = computed(() => navigationItems.find((item) => item.key === activeKey.value) || { breadcrumb: activePage.value.breadcrumb })
</script>

<template>
  <div class="min-h-screen bg-[#f8fafc] text-slate-950">
    <Sidebar
      :active-key="activeKey"
      :collapsed="collapsed"
      @navigate="activeKey = $event"
      @collapse-change="collapsed = $event"
    />
    <div :class="['min-h-screen transition-all duration-300', collapsed ? 'pl-[76px]' : 'pl-[248px]']">
      <Header :breadcrumbs="activeNav.breadcrumb" @navigate="activeKey = $event" />
      <main class="thin-scrollbar h-[calc(100vh-64px)] overflow-y-auto bg-[#f8fafc] px-6 py-6">
        <section :key="activeKey" class="page-transition mx-auto max-w-[1480px] space-y-6">
          <div class="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
            <div class="space-y-2">
              <div class="flex flex-wrap items-center gap-2">
                <Badge variant="outline">Enterprise Shell</Badge>
                <Badge>实时监控</Badge>
              </div>
              <div>
                <h1 class="text-2xl font-semibold tracking-normal text-slate-950">{{ activePage.title }}</h1>
                <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{{ activePage.description }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <Button variant="secondary">导出快照</Button>
              <Button>刷新数据</Button>
            </div>
          </div>

          <component :is="activePage.component" />
        </section>
      </main>
    </div>
  </div>
</template>