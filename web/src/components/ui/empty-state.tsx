import * as React from 'react';

import { cn } from '@/lib/cn';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'bg-surface flex flex-col items-center justify-center rounded-lg border border-dashed px-6 py-12 text-center',
        className,
      )}
    >
      {icon ? (
        <div className="bg-primary-soft text-primary mb-4 flex size-12 items-center justify-center rounded-full [&_svg]:size-6">
          {icon}
        </div>
      ) : null}
      <h3 className="text-foreground text-base font-semibold">{title}</h3>
      {description ? (
        <p className="text-muted-foreground mt-1 max-w-md text-sm">{description}</p>
      ) : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
