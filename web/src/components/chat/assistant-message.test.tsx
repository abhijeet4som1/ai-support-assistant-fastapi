import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { type Message } from '@/api/types';

import { AssistantMessage } from './assistant-message';

const base: Message = {
  id: 'm1',
  conversationId: 'c1',
  role: 'assistant',
  content: 'Hello [Name]',
  status: 'ok',
  model: 'gemini',
  latencyMs: 1234,
  createdBy: { id: 'u', username: 'agent1', displayName: 'Agent1' },
  createdAt: new Date().toISOString(),
  guidance: {
    coverage: 'partial',
    recommendedReply: 'Hello [Name], your refund is on its way.',
    handlingSteps: ['Check the order', 'Issue the refund'],
    clarifications: ['Would you prefer a replacement or a refund?'],
    agentDecisions: ['Offer a discount code if appropriate'],
    escalation: { recommended: true, to: 'Finance', reason: 'Refund above limit' },
    citations: [{ chunkId: 'k1', title: 'Returns and Refunds' }],
    notes: 'Timeline not specified in guidelines.',
  },
};

const wrap = (ui: React.ReactNode) => render(<I18nProvider i18n={i18n}>{ui}</I18nProvider>);

describe('AssistantMessage', () => {
  it('orders sections as steps, clarifications, decisions, then the reply', () => {
    wrap(<AssistantMessage message={base} />);
    const headings = screen.getAllByRole('heading', { level: 3 }).map((h) => h.textContent);
    expect(headings).toEqual([
      'Handling steps',
      'Clarify with the customer',
      'Your call',
      'Recommended reply',
    ]);
  });

  it('renders every part of the structured guidance', () => {
    wrap(<AssistantMessage message={base} />);
    expect(screen.getByText(/partially covered/i)).toBeInTheDocument();
    expect(screen.getByText(/escalation recommended/i)).toBeInTheDocument();
    expect(screen.getByText(/Finance/)).toBeInTheDocument();
    expect(screen.getByText('Hello [Name], your refund is on its way.')).toBeInTheDocument();
    expect(screen.getByText('Issue the refund')).toBeInTheDocument();
    expect(screen.getByText(/clarify with the customer/i)).toBeInTheDocument();
    expect(screen.getByText(/replacement or a refund/)).toBeInTheDocument();
    expect(screen.getByText(/asks the customer the questions above/i)).toBeInTheDocument();
    expect(screen.getByText(/offer a discount code/i)).toBeInTheDocument();
    expect(screen.getByText(/timeline not specified/i)).toBeInTheDocument();
    expect(screen.getByText('Returns and Refunds')).toBeInTheDocument();
  });

  it('shows the error and a retry action for failed turns', async () => {
    const onRetry = vi.fn();
    wrap(
      <AssistantMessage
        message={{ ...base, status: 'failed', error: 'quota exceeded', guidance: undefined }}
        onRetry={onRetry}
      />,
    );
    expect(screen.getByRole('alert')).toHaveTextContent('quota exceeded');
    await userEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(onRetry).toHaveBeenCalled();
  });
});
