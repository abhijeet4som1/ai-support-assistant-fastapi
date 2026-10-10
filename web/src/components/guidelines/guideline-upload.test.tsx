import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { type GuidelineVersionSummary } from '@/api/types';
import { errorResponse, installFetchMock, jsonResponse, type FetchMock } from '@/test/setup-fetch';

import { GuidelineUpload } from './guideline-upload';

// applyAccept:false lets us exercise the component's own extension check.
const user = userEvent.setup({ applyAccept: false });

const version: GuidelineVersionSummary = {
  id: 'v1',
  companyId: 'c1',
  filename: 'old.txt',
  contentType: 'text/plain',
  sizeBytes: 1,
  status: 'ready',
  chunksTotal: 1,
  chunksEmbedded: 1,
  isActive: true,
  uploadedBy: { id: 'u', username: 'agent1', displayName: 'Agent1' },
  createdAt: '2026-09-13T09:00:00Z',
  updatedAt: '2026-09-13T09:00:00Z',
};

function renderUpload(latest?: GuidelineVersionSummary) {
  const qc = new QueryClient({ defaultOptions: { mutations: { retry: 0 } } });
  render(
    <I18nProvider i18n={i18n}>
      <QueryClientProvider client={qc}>
        <GuidelineUpload companyId="c1" latestVersion={latest} />
      </QueryClientProvider>
    </I18nProvider>,
  );
}

const fileInput = () => document.querySelector<HTMLInputElement>('input[type=file]')!;

describe('GuidelineUpload', () => {
  let mock: FetchMock;
  afterEach(() => vi.unstubAllGlobals());

  it('rejects unsupported extensions before uploading', async () => {
    mock = installFetchMock(() => jsonResponse({}));
    renderUpload();
    await user.upload(
      fileInput(),
      new File(['x'], 'setup.exe', { type: 'application/octet-stream' }),
    );
    expect(await screen.findByRole('alert')).toHaveTextContent(/unsupported file type/i);
    expect(screen.queryByRole('button', { name: /upload guidelines/i })).not.toBeInTheDocument();
    expect(mock.calls).toHaveLength(0);
  });

  it('uploads raw bytes with filename and expected-version headers', async () => {
    mock = installFetchMock(() =>
      jsonResponse({ version: { ...version, id: 'v2', status: 'queued' } }, { status: 202 }),
    );
    renderUpload(version);
    await user.upload(
      fileInput(),
      new File(['hello guidelines'], 'new.txt', { type: 'text/plain' }),
    );
    await user.click(await screen.findByRole('button', { name: /replace guidelines/i }));
    await waitFor(() => expect(mock.calls).toHaveLength(1));
    const { req, body } = mock.calls[0]!;
    expect(req.method).toBe('PUT');
    expect(new URL(req.url).pathname).toBe('/api/companies/c1/guidelines');
    expect(req.headers.get('x-filename')).toBe('new.txt');
    expect(req.headers.get('x-expected-version')).toBe('v1');
    expect(req.headers.get('content-type')).toBe('application/octet-stream');
    expect(body).toBe('hello guidelines');
  });

  it('asks before replacing when someone else uploaded meanwhile, then forces', async () => {
    let attempt = 0;
    mock = installFetchMock(() =>
      ++attempt === 1
        ? errorResponse('GuidelinesConflictError', 409, {
            message: 'newer',
            latestVersionId: 'v9',
            uploadedBy: { id: 'u2', username: 'agent2', displayName: 'Agent2' },
            uploadedAt: '2026-09-13T10:00:00Z',
          })
        : jsonResponse({ version: { ...version, id: 'v10', status: 'queued' } }, { status: 202 }),
    );
    renderUpload(version);
    await user.upload(fileInput(), new File(['x'], 'new.txt', { type: 'text/plain' }));
    await user.click(await screen.findByRole('button', { name: /replace guidelines/i }));
    expect(await screen.findByRole('dialog')).toHaveTextContent(/Agent2 uploaded new guidelines/);
    await user.click(screen.getByRole('button', { name: /replace anyway/i }));
    await waitFor(() => expect(mock.calls).toHaveLength(2));
    expect(mock.calls[1]!.req.headers.get('x-expected-version')).toBeNull();
  });
});
