/** Assertion-free helpers for narrowing `unknown` values from JSON or the DOM. */
export const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

export const isStringArray = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every((v) => typeof v === 'string');

/** Type guard factory for string-literal unions declared as `as const` tuples. */
export const oneOf =
  <const T extends readonly string[]>(values: T) =>
  (value: unknown): value is T[number] =>
    typeof value === 'string' && values.some((v) => v === value);
