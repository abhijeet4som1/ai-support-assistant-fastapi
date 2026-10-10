import * as React from 'react';

import { cn } from '@/lib/cn';

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, type = 'text', ...props }: InputProps) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        'bg-surface text-foreground placeholder:text-muted-foreground shadow-xs flex h-9 w-full rounded-md border px-3 py-1 text-sm transition-colors',
        'focus-visible:ring-ring focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-offset-1',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'aria-invalid:border-danger aria-invalid:ring-danger/30',
        className,
      )}
      {...props}
    />
  );
}
