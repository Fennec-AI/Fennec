import * as React from "react"

import { cn } from "@/lib/utils"

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-7 w-full rounded-[4px] border border-input bg-ds-sunken px-2.5 py-1 font-mono text-xs text-ds-fg file:border-0 file:bg-transparent file:text-xs file:font-medium file:text-foreground placeholder:text-ds-tertiary focus-visible:border-ds-border-strong focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
