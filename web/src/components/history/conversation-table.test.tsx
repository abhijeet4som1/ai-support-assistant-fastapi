import { screen } from '@testing-library/react';

import { type ConversationSummary } from '@/api/types';
import { renderWithRouter } from '@/test/render-with-router';

import { ConversationTable } from './conversation-table';

const conv = (over: Partial<ConversationSummary>): ConversationSummary => ({
  id: 'c1',
  companyId: 'co',
  companyName: 'Bookshop',
  title: 'Where is my order?',
  messageCount: 4,
  lastCoverage: 'covered',
  createdBy: { id: 'u', username: 'agent1', displayName: 'Agent1' },
  createdAt: new Date().toISOString(),
  lastMessageAt: new Date().toISOString(),
  ...over,
});

describe('ConversationTable', () => {
  it('renders rows with coverage and links to the detail page', async () => {
    renderWithRouter(
      <ConversationTable
        conversations={[
          conv({}),
          conv({ id: 'c2', title: 'Refund?', lastCoverage: 'not_covered' }),
        ]}
        hasMore
      />,
    );
    expect(await screen.findByText('Where is my order?')).toBeInTheDocument();
    expect(screen.getByText(/covered by guidelines/i)).toBeInTheDocument();
    expect(screen.getByText(/^not covered/i)).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'View' })).toHaveLength(2);
    expect(screen.getByRole('button', { name: /load more/i })).toBeInTheDocument();
  });

  it('shows an empty state', async () => {
    renderWithRouter(<ConversationTable conversations={[]} />);
    expect(await screen.findByText(/no conversations match/i)).toBeInTheDocument();
  });
});
