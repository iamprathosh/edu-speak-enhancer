import { cn } from "@/lib/utils"
import { cva, type VariantProps } from "class-variance-authority"

const loadingIndicatorVariants = cva(
  "animate-spin rounded-full border-t-2 border-b-2 border-edumate-500",
  {
    variants: {
      size: {
        sm: "h-4 w-4",
        md: "h-8 w-8",
        lg: "h-12 w-12",
      },
    },
    defaultVariants: {
      size: "md",
    },
  }
)

export interface LoadingIndicatorProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof loadingIndicatorVariants> {
  text?: string;
}

export function LoadingIndicator({
  className,
  size,
  text,
  ...props
}: LoadingIndicatorProps) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={cn(loadingIndicatorVariants({ size, className }))}
        {...props}
      />
      {text && (
        <p className="mt-3 text-sm text-slate-600">{text}</p>
      )}
    </div>
  )
}