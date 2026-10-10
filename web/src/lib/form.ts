import { type FieldValues, type Path, type UseFormSetError } from 'react-hook-form';

import { type UiError } from '@/api/errors';

export const fieldErrorId = (id: string) => `${id}-error`;

/** Props to spread on a form control so screen readers announce its error. */
export function fieldProps(id: string, error?: string) {
  return {
    id,
    'aria-invalid': error ? true : undefined,
    'aria-describedby': error ? fieldErrorId(id) : undefined,
  } as const;
}

/**
 * Applies server-side field errors (ValidationException.fieldList) to a react-hook-form form.
 * Returns true when at least one error matched a known field; otherwise the caller should show
 * the message at form level.
 */
export function applyServerFieldErrors<T extends FieldValues>(
  ui: UiError,
  setError: UseFormSetError<T>,
  fields: readonly Path<T>[],
): boolean {
  if (ui.kind !== 'validation') return false;
  let applied = false;
  for (const field of fields) {
    const message = ui.fields[field];
    if (message) {
      setError(field, { type: 'server', message });
      applied = true;
    }
  }
  return applied;
}
