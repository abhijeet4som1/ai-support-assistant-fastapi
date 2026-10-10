/**
 * Error thrown by the api client for any non-2xx response. `type` is the modelled Smithy error
 * name carried in the `X-Amzn-Errortype` header (e.g. "GuidelinesConflictError"), which lets the
 * UI tell apart errors that share a status code.
 */
import { isRecord } from '@/lib/guards';

export class ApiError extends Error {
  readonly status: number;
  readonly type: string | undefined;
  readonly requestId: string | undefined;
  readonly body: Record<string, unknown>;

  constructor(init: {
    status: number;
    type?: string;
    requestId?: string;
    body?: unknown;
    message?: string;
  }) {
    const body = isRecord(init.body) ? init.body : {};
    const message =
      init.message ??
      (typeof body.message === 'string' ? body.message : undefined) ??
      `Request failed with status ${init.status}`;
    super(message);
    this.name = 'ApiError';
    this.status = init.status;
    this.type = init.type;
    this.requestId =
      init.requestId ?? (typeof body.requestId === 'string' ? body.requestId : undefined);
    this.body = body;
  }
}

/** `X-Amzn-Errortype` may look like "Name", "ns#Name" or "Name:http://...": keep the bare name. */
export function parseErrorType(header: string | null | undefined): string | undefined {
  if (!header) return undefined;
  const beforeColon = header.split(':')[0] ?? header;
  const afterHash = beforeColon.split('#').pop() ?? beforeColon;
  return afterHash.trim() || undefined;
}

export async function apiErrorFromResponse(response: Response): Promise<ApiError> {
  let body: unknown;
  try {
    const text = await response.clone().text();
    body = text ? JSON.parse(text) : undefined;
  } catch {
    body = undefined;
  }
  return new ApiError({
    status: response.status,
    type: parseErrorType(response.headers.get('x-amzn-errortype')),
    requestId: response.headers.get('x-request-id') ?? undefined,
    body,
  });
}
