import { cn } from '../../lib/utils.js'

export function Badge({ className, variant = 'default', ...props }) {
  const variants = {
    default: 'border-transparent bg-forest-100 text-forest-800',
    warning: 'border-transparent bg-amber-100 text-amber-800',
    danger: 'border-transparent bg-red-100 text-red-700',
    outline: 'border-slate-200 bg-white text-slate-600'
  }

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium',
        variants[variant],
        className
      )}
      {...props}
    />
  )
}