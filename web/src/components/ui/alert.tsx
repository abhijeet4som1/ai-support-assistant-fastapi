import { cva, type VariantProps } from 'class-variance-authority';
import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react';
import * as React from 'react';

import { cn } from '@/lib/cn';

const alertVariants = cva(
  'relative flex w-full gap-3 rounded-lg border px-4 py-3 text-sm [&_svg]:mt-0.5 [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        info: 'bg-primary-soft text-primary-soft-foreground border-primary/20',
        success: 'bg-success-soft text-success-soft-foreground border-success/30',
        warning: 'bg-warning-soft text-warning-soft-foreground border-warning/40',
        danger: 'bg-danger-soft text-danger-soft-foreground border-danger/30',
      },
    },
    defaultVariants: { variant: 'info' },
  },
);

const icons = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: XCircle,
} as const;

export interface AlertProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'>, VariantProps<typeof alertVariants> {
  title?: React.ReactNode;
}

export function Alert({ className, variant = 'info', title, children, ...props }: AlertProps) {
  const Icon = icons[variant ?? 'info'];
  return (
    <div
      role={variant === 'danger' || variant === 'warning' ? 'alert' : 'status'}
      data-slot="alert"
      className={cn(alertVariants({ variant }), className)}
      {...props}
    >
      <Icon aria-hidden />
      <div className="min-w-0 flex-1 space-y-1">
        {title ? <p className="font-medium">{title}</p> : null}
        {children ? <div className="[&_p]:leading-relaxed">{children}</div> : null}
      </div>
    </div>
  );
}
