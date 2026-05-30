<script setup>
import { ChevronLeft, ChevronRight, Leaf } from 'lucide-vue-next'
import Button from '../ui/Button.vue'
import { navigationItems } from './navigation.js'

defineProps({
  activeKey: { type: String, required: true },
  collapsed: { type: Boolean, required: true }
})

const emit = defineEmits(['navigate', 'collapse-change'])
</script>

<template>
  <aside
    :class="[
      'fixed inset-y-0 left-0 z-30 flex flex-col border-r border-white/10 bg-forest-950 text-white shadow-xl transition-all duration-300',
      collapsed ? 'w-[76px]' : 'w-[248px]'
    ]"
  >
    <div class="flex h-16 items-center gap-3 border-b border-white/10 px-4">
      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-white/15 bg-white/10">
        <Leaf class="h-5 w-5 text-emerald-200" />
      </div>
      <div v-if="!collapsed" class="min-w-0">
        <p class="truncate text-sm font-semibold tracking-normal">农产品价格平台</p>
        <p class="truncate text-xs text-emerald-100/70">Agri Price Monitor</p>
      </div>
    </div>

    <nav class="flex-1 space-y-1 px-3 py-4">
      <Button
        v-for="item in navigationItems"
        :key="item.key"
        variant="sidebar"
        :data-active="item.key === activeKey"
        :title="collapsed ? item.label : undefined"
        :class="[
          'h-11 w-full justify-start rounded-lg px-3 text-sm',
          collapsed && 'justify-center px-0',
          item.key === activeKey && 'shadow-sm'
        ]"
        @click="emit('navigate', item.key)"
      >
        <component :is="item.icon" class="h-4 w-4 shrink-0" />
        <span v-if="!collapsed" class="truncate">{{ item.label }}</span>
      </Button>
    </nav>

    <div class="border-t border-white/10 p-3">
      <Button
        variant="sidebar"
        :size="collapsed ? 'icon' : 'default'"
        :class="['w-full rounded-lg', collapsed ? 'justify-center' : 'justify-between']"
        @click="emit('collapse-change', !collapsed)"
      >
        <span v-if="!collapsed">收起侧边栏</span>
        <ChevronRight v-if="collapsed" class="h-4 w-4" />
        <ChevronLeft v-else class="h-4 w-4" />
      </Button>
    </div>
  </aside>
</template>