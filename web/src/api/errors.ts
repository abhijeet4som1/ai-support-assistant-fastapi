/**
 * Maps errors thrown by the api client (and the network) to a small UI-oriented union.
 * Every place that shows an error goes through this so behaviour is consistent:
 * field errors on forms, redirect on 401, inline retry for AI failures, error page otherwise.
 */
import { z } from 'zod';

import { isRecord, isStringArray } from '@/lib/guards';

import { ApiError } from './api-error';

export type UiError =
  | { kind: 'validation'; message: string; fields: Record<string, string> }
  | { kind: 'unauthorized'; message: string }
  | { kind: 'not_found'; message: string }
  | { kind: 'conflict'; message: string; code: 'conflict' }
  | { kind: 'conflict'; message: string; code: 'guidelines_not_ready'; companyId?: string }
  | {
      kind: 'conflict';
      message: string;
      code: 'guidelines_conflict';
      latestVersionId?: string;
      uploadedBy?: string;
      uploadedAt?: string;
    }
  | { kind: 'upload'; message: string; code: 'too_large' | 'unsupported_type'; detail?: string }
  | { kind: 'rate_limited'; message: string; retryAfterSeconds?: number }
  | { kind: 'ai_provider'; message: string }
  | { kind: 'server'; message: string; requestId?: string }
  | { kind: 'network'; message: string }
  | { kind: 'unknown'; message: string };

/** `/username` → `username`, `/items/0/name` → `items.0.name` */
export const fieldPathToName = (path: string) => path.replace(/^\//, '').replace(/\//g, '.');

const str = (v: unknown) => (typeof v === 'string' ? v : undefined);
const num = (v: unknown) => (typeof v === 'number' ? v : undefined);
const fieldListSchema = z.array(
  z.object({ path: z.string().optional(), message: z.string().optional() }),
);

export function toUiError(err: unknown): UiError {
  if (err instanceof ApiError) {
    const b = err.body;
    switch (err.type) {
      case 'ValidationException': {
        const fields: Record<string, string> = {};
        const parsed = fieldListSchema.safeParse(b.fieldList);
        const list = parsed.success ? parsed.data : [];
        for (const f of list) {
          if (f.path && f.message && !(fieldPathToName(f.path) in fields))
            fields[fieldPathToName(f.path)] = f.message;
        }
        return { kind: 'validation', message: err.message, fields };
      }
      case 'UnauthorizedError':
        return { kind: 'unauthorized', message: err.message };
      case 'NotFoundError':
        return { kind: 'not_found', message: err.message };
      case 'GuidelinesNotReadyError':
        return {
          kind: 'conflict',
          code: 'guidelines_not_ready',
          message: err.message,
          companyId: str(b.companyId),
        };
      case 'GuidelinesConflictError':
        return {
          kind: 'conflict',
          code: 'guidelines_conflict',
          message: err.message,
          latestVersionId: str(b.latestVersionId),
          uploadedBy: isRecord(b.uploadedBy) ? str(b.uploadedBy.displayName) : undefined,
          uploadedAt: str(b.uploadedAt),
        };
      case 'ConflictError':
        return { kind: 'conflict', code: 'conflict', message: err.message };
      case 'PayloadTooLargeError': {
        const maxBytes = num(b.maxBytes);
        return {
          kind: 'upload',
          code: 'too_large',
          message: err.message,
          detail: maxBytes ? `${Math.round(maxBytes / 1024 / 1024)} MB` : undefined,
        };
      }
      case 'UnsupportedMediaTypeError':
        return {
          kind: 'upload',
          code: 'unsupported_type',
          message: err.message,
          detail: isStringArray(b.supported) ? b.supported.join(', ') : undefined,
        };
      case 'RateLimitedError':
        return {
          kind: 'rate_limited',
          message: err.message,
          retryAfterSeconds: num(b.retryAfterSeconds),
        };
      case 'AiProviderError':
        return { kind: 'ai_provider', message: err.message };
      case 'InternalServerError':
        return { kind: 'server', message: err.message, requestId: err.requestId };
      default:
        if (err.status === 401) return { kind: 'unauthorized', message: err.message };
        if (err.status === 404) return { kind: 'not_found', message: err.message };
        if (err.status >= 500)
          return { kind: 'server', message: err.message, requestId: err.requestId };
        return { kind: 'unknown', message: err.message };
    }
  }
  if (
    err instanceof TypeError ||
    (err instanceof Error && /network|fetch|Failed to fetch/i.test(err.message))
  ) {
    return { kind: 'network', message: err.message };
  }
  return { kind: 'unknown', message: err instanceof Error ? err.message : String(err) };
}
