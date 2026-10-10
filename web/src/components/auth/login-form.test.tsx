import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { clearSession, getTokens, getUser, isAuthenticated } from '@/auth/atoms';
import { isRecord } from '@/lib/guards';
import { errorResponse, installFetchMock, jsonResponse, type FetchMock } from '@/test/setup-fetch';

import { LoginForm } from './login-form';

function renderForm(onSuccess = vi.fn()) {
  const qc = new QueryClient({ defaultOptions: { mutations: { retry: 0 } } });
  render(
    <I18nProvider i18n={i18n}>
      <QueryClientProvider client={qc}>
        <LoginForm onSuccess={onSuccess} />
      </QueryClientProvider>
    </I18nProvider>,
  );
  return { onSuccess };
}

describe('LoginForm', () => {
  let mock: FetchMock | undefined;
  beforeEach(() => clearSession());
  afterEach(() => vi.unstubAllGlobals());

  it('validates client-side before calling the api', async () => {
    mock = installFetchMock(() => jsonResponse({}));
    renderForm();
    await userEvent.click(screen.getByRole('button', { name: /log in/i }));
    expect(await screen.findAllByRole('alert')).toHaveLength(2);
    expect(mock.calls).toHaveLength(0);
  });

  it('maps a server ValidationException onto the fields', async () => {
    installFetchMock(() =>
      errorResponse('ValidationException', 400, {
        message: 'invalid',
        fieldList: [{ path: '/username', message: 'Value at /username failed length constraint' }],
      }),
    );
    renderForm();
    await userEvent.type(screen.getByLabelText(/username/i), 'x');
    await userEvent.type(screen.getByLabelText(/password/i), 'y');
    await userEvent.click(screen.getByRole('button', { name: /log in/i }));
    expect(await screen.findByText(/failed length constraint/)).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toHaveAttribute('aria-invalid', 'true');
  });

  it('shows a friendly message on 401', async () => {
    installFetchMock(() =>
      errorResponse('UnauthorizedError', 401, { message: 'Invalid username or password' }),
    );
    renderForm();
    await userEvent.type(screen.getByLabelText(/username/i), 'agent1');
    await userEvent.type(screen.getByLabelText(/password/i), 'wrong');
    await userEvent.click(screen.getByRole('button', { name: /log in/i }));
    expect(await screen.findByText(/invalid username or password/i)).toBeInTheDocument();
    expect(isAuthenticated()).toBe(false);
  });

  it('stores the session and calls onSuccess', async () => {
    mock = installFetchMock((req, body) =>
      req.method === 'POST' &&
      new URL(req.url).pathname === '/api/auth/login' &&
      isRecord(body) &&
      body.username === 'agent1'
        ? jsonResponse({
            tokens: {
              accessToken: 'tok',
              accessExpiresAt: new Date(Date.now() + 60_000).toISOString(),
              refreshToken: 'ref',
              refreshExpiresAt: new Date(Date.now() + 7 * 24 * 3600_000).toISOString(),
            },
            user: { id: 'u1', username: 'agent1', displayName: 'Agent1' },
          })
        : undefined,
    );
    const { onSuccess } = renderForm();
    await userEvent.type(screen.getByLabelText(/username/i), 'agent1');
    await userEvent.type(screen.getByLabelText(/password/i), 'agent1pass');
    await userEvent.click(screen.getByRole('button', { name: /log in/i }));
    await waitFor(() => expect(onSuccess).toHaveBeenCalled());
    expect(getTokens()?.accessToken).toBe('tok');
    expect(getUser()?.username).toBe('agent1');
    expect(isAuthenticated()).toBe(true);
    expect(mock.calls[0]!.body).toEqual({ username: 'agent1', password: 'agent1pass' });
  });
});
