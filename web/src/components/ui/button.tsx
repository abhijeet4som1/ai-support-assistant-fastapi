import { type VariantProps } from 'class-variance-authority';
import { Loader2 } from 'lucide-react';
import { Slot } from 'radix-ui';
import * as React from 'react';

import { cn } from '@/lib/cn';

import { buttonVariants } from './button-variants';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  /** Render as the child element (e.g. a router Link) while keeping button styles. */
  asChild?: boolean;
  loading?: boolean;
}

export function Button({
  className,
  variant,
  size,
  asChild = false,
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const classes = cn(buttonVariants({ variant, size }), className);
  if (asChild) {
    // Slot needs exactly one element child; loading state is not supported in asChild mode.
    return (
      <Slot.Root
        data-slot="button"
        className={classes}
        aria-disabled={disabled || undefined}
        {...props}
      >
        {children}
      </Slot.Root>
    );
  }
  return (
    <button
      data-slot="button"
      className={classes}
      disabled={disabled ?? loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? <Loader2 className="animate-spin" aria-hidden /> : null}
      {children}
    </button>
  );
}
