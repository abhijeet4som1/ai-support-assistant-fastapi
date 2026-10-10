import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { type Message } from '@/api/types';

import { MessageThread } from './message-thread';

const at = new Date().toISOString();
const customer = (id: string, content: string): Message => ({
  id,
  conversationId: 'c1',
  role: 'customer',
  content,
  status: 'ok',
  createdBy: { id: 'u', username: 'agent1', displayName: 'Agent1' },
  createdAt: at,
});

const wrap = (ui: React.ReactNode) => render(<I18nProvider i18n={i18n}>{ui}</I18nProvider>);

describe('MessageThread paging', () => {
  it('offers to load earlier messages only while older pages exist', async () => {
    const onLoadOlder = vi.fn();
    const { rerender } = wrap(
      <MessageThread messages={[customer('m1', 'newest')]} hasOlder onLoadOlder={onLoadOlder} />,
    );
    await userEvent.click(screen.getByRole('button', { name: /load earlier messages/i }));
    expect(onLoadOlder).toHaveBeenCalledTimes(1);

    rerender(
      <I18nProvider i18n={i18n}>
        <MessageThread messages={[customer('m0', 'older'), customer('m1', 'newest')]} />
      </I18nProvider>,
    );
    expect(screen.queryByRole('button', { name: /load earlier messages/i })).toBeNull();
    expect(screen.getByText('older')).toBeInTheDocument();
  });

  it('disables the control while a page is loading', () => {
    wrap(<MessageThread messages={[customer('m1', 'x')]} hasOlder loadingOlder />);
    expect(screen.getByRole('button', { name: /load earlier messages/i })).toBeDisabled();
  });
});
