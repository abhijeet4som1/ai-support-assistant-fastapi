import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { type Message } from '@/api/types';
import { setTokens, setUser } from '@/auth/atoms';
import { installFetchMock, jsonResponse, type FetchMock } from '@/test/setup-fetch';

import { FeedbackControls } from './feedback-controls';

const me = { id: 'u1', username: 'agent1', displayName: 'Agent1' };
const message: Message = {
  id: 'm1',
  conversationId: 'c1',
  role: 'assistant',
  content: 'Hello [Name]',
  status: 'ok',
  createdBy: me,
  createdAt: '2026-09-13T09:00:00Z',
  guidance: {
    coverage: 'covered',
    recommendedReply: 'Hello [Name], draft reply.',
    handlingSteps: [],
    agentDecisions: [],
    escalation: { recommended: false },
    citations: [],
  },
  feedback: [
    {
      id: 'f2',
      rating: 'up',
      user: { id: 'u2', username: 'agent2', displayName: 'Agent2' },
      createdAt: '2026-09-13T09:00:00Z',
    },
  ],
};

const correction = (rating: 'up' | 'down') => ({
  id: 'f1',
  companyId: 'co',
  conversationId: 'c1',
  messageId: 'm1',
  rating,
  queryText: 'q',
  guidelineVersionId: 'g',
  active: true,
  user: me,
  createdAt: '2026-09-13T09:00:00Z',
});

function renderControls() {
  const qc = new QueryClient({ defaultOptions: { mutations: { retry: 0 } } });
  render(
    <I18nProvider i18n={i18n}>
      <QueryClientProvider client={qc}>
        <FeedbackControls message={message} conversationId="c1" />
      </QueryClientProvider>
    </I18nProvider>,
  );
}

describe('FeedbackControls', () => {
  let mock: FetchMock;
  beforeEach(() => {
    setTokens({
      accessToken: 't',
      accessExpiresAt: new Date(Date.now() + 60_000).toISOString(),
      refreshToken: 'r',
      refreshExpiresAt: new Date(Date.now() + 7 * 24 * 3600_000).toISOString(),
    });
    setUser(me);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('sends a thumbs up and shows other ratings', async () => {
    mock = installFetchMock(() => jsonResponse({ correction: correction('up') }));
    renderControls();
    expect(screen.getByText(/1 other rating/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /helpful/i }));
    await waitFor(() => expect(mock.calls).toHaveLength(1));
    expect(mock.calls[0]!.req.method).toBe('PUT');
    expect(new URL(mock.calls[0]!.req.url).pathname).toBe('/api/messages/m1/feedback');
    expect(mock.calls[0]!.body).toEqual({ rating: 'up' });
  });

  it('requires a corrected answer before saving a thumbs down, prefilled with the draft', async () => {
    mock = installFetchMock(() => jsonResponse({ correction: correction('down') }));
    renderControls();
    await userEvent.click(screen.getByRole('button', { name: /needs correction/i }));
    const answer = screen.getByLabelText(/correct answer/i);
    expect(answer).toHaveValue('Hello [Name], draft reply.');
    await userEvent.clear(answer);
    await userEvent.click(screen.getByRole('button', { name: /save correction/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/provide the answer/i);
    expect(mock.calls).toHaveLength(0);

    await userEvent.type(answer, 'Hello there, the corrected reply.');
    await userEvent.type(screen.getByLabelText(/what was wrong/i), 'Too vague');
    await userEvent.click(screen.getByRole('button', { name: /save correction/i }));
    await waitFor(() => expect(mock.calls).toHaveLength(1));
    expect(mock.calls[0]!.body).toMatchObject({
      rating: 'down',
      whatWasWrong: 'Too vague',
      correctedAnswer: 'Hello there, the corrected reply.',
    });
  });
});
