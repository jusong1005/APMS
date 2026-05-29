import * as AvatarPrimitive from '@radix-ui/react-avatar'
import { cn } from '../../lib/utils.js'

export function Avatar({ className, ...props }) {
  return <AvatarPrimitive.Root className={cn('relative flex h-9 w-9 shrink-0 overflow-hidden rounded-md', className)} {...props} />
}

export function AvatarImage({ className, ...props }) {
  return <AvatarPrimitive.Image className={cn('aspect-square h-full w-full object-cover', className)} {...props} />
}

export function AvatarFallback({ className, ...props }) {
  return (
    <AvatarPrimitive.Fallback
      className={cn('flex h-full w-full items-center justify-center bg-forest-100 text-sm font-semibold text-forest-800', className)}
      {...props}
    />
  )
}