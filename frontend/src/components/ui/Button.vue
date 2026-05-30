<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: { type: String, default: 'default' },
  size: { type: String, default: 'default' },
  class: { type: String, default: '' }
})

const variantClasses = {
  default: 'bg-primary text-primary-foreground shadow-sm hover:bg-forest-700',
  secondary: 'border bg-white text-slate-700 shadow-sm hover:bg-slate-50',
  ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
  sidebar: 'text-forest-100 hover:bg-white/8 hover:text-white data-[active=true]:bg-white data-[active=true]:text-forest-900',
  destructive: 'bg-destructive text-destructive-foreground hover:bg-red-600'
}

const sizeClasses = {
  default: 'h-9 px-3',
  icon: 'h-9 w-9 px-0',
  sm: 'h-8 px-2.5 text-xs'
}

const classes = computed(() => [
  'inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50',
  variantClasses[props.variant],
  sizeClasses[props.size],
  props.class
])
</script>

<template>
  <button :class="classes">
    <slot />
  </button>
</template>