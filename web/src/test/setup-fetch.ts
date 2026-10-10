/**
 * Test helper: routes `fetch` calls made by the api client to in-test handlers, so component
 * tests exercise the real client, middleware and error mapping.
 */
export type FetchHandler = (
  req: Request,
  body: unknown,
) => Response | Promise<Response> | undefined;

export function jsonResponse(
  data: unknown,
  init: { status?: number; headers?: Record<string, string> } = {},
) {
  return new Response(JSON.stringify(data), {
    status: init.status ?? 200,
    headers: { 'content-type': 'application/json', ...init.headers },
  });
}

/** A modelled api error as the server would send it (body + X-Amzn-Errortype header). */
export function errorResponse(type: string, status: number, body: Record<string, unknown>) {
  return jsonResponse(body, {
    status,
    headers: { 'x-amzn-errortype': type, 'x-request-id': 'test-req' },
  });
}

export interface FetchMock {
  calls: { req: Request; body: unknown }[];
}

/** jsdom's Blob is not Node's Blob; Node's Request would stringify it. Read it into text first. */
async function normaliseBody(
  body: BodyInit | null | undefined,
): Promise<BodyInit | null | undefined> {
  if (typeof Blob !== 'undefined' && body instanceof Blob && typeof FileReader !== 'undefined') {
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : '');
      reader.onerror = () => reject(reader.error ?? new Error('read failed'));
      reader.readAsText(body);
    });
  }
  return body;
}

export function installFetchMock(handler: FetchHandler): FetchMock {
  const mock: FetchMock = { calls: [] };
  vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    const req = new Request(
      input,
      init ? { ...init, body: await normaliseBody(init.body) } : undefined,
    );
    const text = await req.clone().text();
    let body: unknown = undefined;
    if (text) {
      try {
        body = JSON.parse(text);
      } catch {
        body = text;
      }
    }
    mock.calls.push({ req, body });
    const res = await handler(req, body);
    if (!res)
      throw new Error(`unhandled request in test: ${req.method} ${new URL(req.url).pathname}`);
    return res;
  });
  return mock;
}
