<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Bell, ChevronDown, ChevronRight, Clock3, LogOut, Settings, ShieldCheck, UserRound } from 'lucide-vue-next'
import Badge from '../ui/Badge.vue'
import Button from '../ui/Button.vue'

const props = defineProps({
  breadcrumbs: { type: Array, required: true },
  user: { type: Object, default: null }
})

const emit = defineEmits(['navigate', 'logout'])

const notifications = [
  { title: '新发地采集任务完成', detail: '本批次 12,480 条价格记录已入湖', level: 'default' },
  { title: '山东番茄价格波动', detail: '近 24 小时涨幅 18.6%，进入观察区间', level: 'warning' },
  { title: '质量规则校验通过', detail: '缺失率 0.7%，重复率 0.2%', level: 'default' }
]

const now = ref(new Date())
const noticeOpen = ref(false)
const userMenuOpen = ref(false)
const noticeMenu = ref(null)
const userMenu = ref(null)
let timer

const displayName = computed(() => props.user?.name || props.user?.account || '平台用户')
const organization = computed(() => props.user?.organization || '农产品价格监测中心')
const roleName = computed(() => ({ admin: '管理员', analyst: '数据分析员', user: '普通用户' }[props.user?.role] || '平台用户'))
const avatarText = computed(() => displayName.value.slice(0, 1))

const marketTime = computed(() => new Intl.DateTimeFormat('zh-CN', {
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false
}).format(now.value))

const handleUserCommand = (command) => {
  userMenuOpen.value = false
  if (command === 'profile') emit('navigate', 'profile')
  if (command === 'logout') emit('logout')
}

const closeFloatingMenus = (event) => {
  const target = event.target
  if (noticeOpen.value && noticeMenu.value && !noticeMenu.value.contains(target)) {
    noticeOpen.value = false
  }
  if (userMenuOpen.value && userMenu.value && !userMenu.value.contains(target)) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  timer = window.setInterval(() => {
    now.value = new Date()
  }, 1000)
  window.addEventListener('pointerdown', closeFloatingMenus)
})

onUnmounted(() => {
  window.clearInterval(timer)
  window.removeEventListener('pointerdown', closeFloatingMenus)
})
</script>

<template>
  <header class="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-white/95 px-6 shadow-sm backdrop-blur">
    <div class="flex min-w-0 items-center gap-2 text-sm text-slate-500">
      <div v-for="(crumb, index) in breadcrumbs" :key="crumb" class="flex items-center gap-2">
        <span :class="index === breadcrumbs.length - 1 ? 'font-medium text-slate-900' : ''">{{ crumb }}</span>
        <ChevronRight v-if="index < breadcrumbs.length - 1" class="h-4 w-4 text-slate-300" />
      </div>
    </div>

    <div class="flex items-center gap-3">
      <div class="hidden items-center gap-2 rounded-lg border bg-slate-50 px-3 py-2 text-sm text-slate-600 md:flex">
        <Clock3 class="h-4 w-4 text-forest-600" />
        <span>当前市场时间</span>
        <span class="h-4 w-px bg-slate-200" />
        <span class="font-medium text-slate-900">{{ marketTime }}</span>
      </div>

      <div ref="noticeMenu" class="relative">
        <Button variant="secondary" size="icon" class="relative" @click="noticeOpen = !noticeOpen">
          <Bell class="h-4 w-4" />
          <span class="absolute right-2 top-2 h-2 w-2 rounded-full bg-red-500" />
        </Button>
        <div v-if="noticeOpen" class="absolute right-0 top-11 z-50 w-80 rounded-lg border bg-white p-1 shadow-xl">
          <div class="flex items-center justify-between px-3 py-2 text-sm font-semibold text-slate-900">
            <span>实时系统通知</span>
            <Badge variant="outline">3 条</Badge>
          </div>
          <div class="my-1 h-px bg-slate-100" />
          <button
            v-for="item in notifications"
            :key="item.title"
            class="flex w-full items-start gap-3 rounded-md px-3 py-2 text-left transition-colors hover:bg-slate-50"
          >
            <ShieldCheck class="mt-0.5 h-4 w-4 text-forest-600" />
            <span class="space-y-1">
              <span class="flex items-center gap-2">
                <span class="font-medium text-slate-900">{{ item.title }}</span>
                <Badge v-if="item.level === 'warning'" variant="warning">关注</Badge>
              </span>
              <span class="block text-xs leading-5 text-slate-500">{{ item.detail }}</span>
            </span>
          </button>
        </div>
      </div>

      <div ref="userMenu" class="relative">
        <button class="flex items-center gap-3 rounded-lg border bg-white px-2.5 py-1.5 shadow-sm transition-colors hover:bg-slate-50" @click="userMenuOpen = !userMenuOpen">
          <div class="flex h-9 w-9 items-center justify-center rounded-full bg-forest-100 text-sm font-semibold text-forest-800">{{ avatarText }}</div>
          <div class="hidden min-w-0 pr-1 text-left lg:block">
            <p class="truncate text-sm font-semibold text-slate-900">{{ organization }}</p>
            <p class="truncate text-xs text-slate-500">{{ displayName }} · {{ roleName }}</p>
          </div>
          <ChevronDown class="hidden h-4 w-4 text-slate-400 lg:block" />
        </button>
        <div v-if="userMenuOpen" class="absolute right-0 top-12 z-50 w-56 rounded-lg border bg-white p-1 shadow-xl">
          <button class="flex w-full items-center rounded-md px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-emerald-50 hover:text-[#064e3b]" @click="handleUserCommand('profile')">
            <UserRound class="mr-2 h-4 w-4" />个人设置
          </button>
          <button class="flex w-full cursor-not-allowed items-center rounded-md px-3 py-2 text-sm text-slate-400" disabled>
            <Settings class="mr-2 h-4 w-4" />偏好同步
          </button>
          <div class="my-1 h-px bg-slate-100" />
          <button class="flex w-full items-center rounded-md px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-red-50 hover:text-red-600" @click="handleUserCommand('logout')">
            <LogOut class="mr-2 h-4 w-4" />退出登录
          </button>
        </div>
      </div>
    </div>
  </header>
</template>