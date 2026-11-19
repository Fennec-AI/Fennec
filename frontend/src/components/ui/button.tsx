import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  // Claudin `.create-btn`: sunken, 1px border, small semibold label; hover raises to panel-hover + border-strong.
  "inline-flex items-center justify-center gap-[5px] whitespace-nowrap rounded-[4px] text-[11px] font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ds-border-strong disabled:cursor-not-allowed disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-3.5 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "border border-border bg-ds-sunken text-ds-fg-muted hover:border-ds-border-strong hover:bg-ds-panel-hover hover:text-ds-fg aria-pressed:border-ds-border-strong aria-pressed:bg-ds-panel-hover aria-pressed:text-ds-fg",
        destructive:
          "border border-ds-danger/40 bg-ds-sunken text-ds-danger hover:border-ds-danger/70 hover:bg-ds-panel-hover",
        outline:
          "border border-border bg-transparent text-ds-fg-muted hover:border-ds-border-strong hover:bg-ds-panel-hover hover:text-ds-fg",
        secondary:
          "border border-border bg-ds-elevated text-ds-fg-muted hover:border-ds-border-strong hover:bg-ds-panel-hover hover:text-ds-fg",
        ghost: "text-ds-fg-muted hover:bg-ds-accent-soft hover:text-ds-fg",
        link: "text-ds-fg underline-offset-4 hover:underline",
      },
      size: {
        default: "h-7 px-2.5",
        sm: "h-control px-2 text-[10px]",
        lg: "h-8 px-4 text-xs",
        icon: "h-7 w-7",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
