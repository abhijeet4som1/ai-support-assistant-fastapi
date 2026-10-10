import * as React from 'react';

import { cn } from '@/lib/cn';
import { fieldErrorId } from '@/lib/form';

import { Label } from './label';

export interface FormFieldProps {
  /** id of the control inside; used for label association and error ids. */
  htmlFor: string;
  label: React.ReactNode;
  error?: string;
  hint?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}

/**
 * Label + control + hint + error with correct aria wiring. Pass
 * `aria-describedby={fieldErrorId(id)}` and `aria-invalid` to the control (see `fieldProps`).
 */
export function FormField({ htmlFor, label, error, hint, className, children }: FormFieldProps) {
  return (
    <div className={cn('space-y-1.5', className)} data-slot="form-field">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {hint && !error ? <p className="text-muted-foreground text-xs">{hint}</p> : null}
      {error ? (
        <p id={fieldErrorId(htmlFor)} role="alert" className="text-danger text-sm">
          {error}
        </p>
      ) : null}
    </div>
  );
}
