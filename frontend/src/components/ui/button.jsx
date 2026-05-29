import * as React from 'react'
import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils.js'

const buttonVariants = cva(
  'inline-flex h-9 items-center justify-center gap-2 rounded-md px-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground shadow-sm hover:bg-forest-700',
        secondary: 'border bg-white text-slate-700 shadow-sm hover:bg-slate-50',
        ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
        sidebar: 'text-forest-100 hover:bg-white/8 hover:text-white data-[active=true]:bg-white data-[active=true]:text-forest-900',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-red-600'
      },
      size: {
        default: 'h-9 px-3',
        icon: 'h-9 w-9 px-0',
        sm: 'h-8 px-2.5 text-xs'
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'default'
    }
  }
)

const Button = React.forwardRef(({ className, variant, size, ...props }, ref) => (
  <button className={cn(buttonVariants({ variant, size }), className)} ref={ref} {...props} />
))
Button.displayName = 'Button'

export { Button, buttonVariants }