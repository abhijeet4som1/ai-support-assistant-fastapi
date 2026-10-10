import * as React from 'react';

import { cn } from '@/lib/cn';

export function Table({ className, ...props }: React.HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="w-full overflow-x-auto">
      <table className={cn('w-full caption-bottom text-sm', className)} {...props} />
    </div>
  );
}
export function TableHeader(props: React.HTMLAttributes<HTMLTableSectionElement>) {
  return <thead className="bg-muted/60 [&_tr]:border-b" {...props} />;
}
export function TableBody(props: React.HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className="[&_tr:last-child]:border-0" {...props} />;
}
export function TableRow({ className, ...props }: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr className={cn('hover:bg-muted/40 border-b transition-colors', className)} {...props} />
  );
}
export function TableHead({ className, ...props }: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      scope="col"
      className={cn(
        'text-muted-foreground h-10 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide',
        className,
      )}
      {...props}
    />
  );
}
export function TableCell({ className, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className={cn('px-4 py-3 align-middle', className)} {...props} />;
}
