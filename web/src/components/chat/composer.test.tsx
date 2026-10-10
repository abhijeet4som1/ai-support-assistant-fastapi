import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { Composer } from './composer';

describe('Composer', () => {
  it('sends the chosen kind and clears the box', async () => {
    const onSend = vi.fn();
    render(
      <I18nProvider i18n={i18n}>
        <Composer onSend={onSend} />
      </I18nProvider>,
    );
    const box = screen.getByRole('textbox');
    await userEvent.type(box, 'Where is my order?');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    expect(onSend).toHaveBeenCalledWith('customer', 'Where is my order?');
    expect(box).toHaveValue('');

    await userEvent.click(screen.getByRole('tab', { name: /instruction/i }));
    await userEvent.type(screen.getByRole('textbox'), 'shorter');
    await userEvent.keyboard('{Control>}{Enter}{/Control}');
    expect(onSend).toHaveBeenLastCalledWith('instruction', 'shorter');
  });

  it('does not send empty text or while disabled', () => {
    const onSend = vi.fn();
    render(
      <I18nProvider i18n={i18n}>
        <Composer onSend={onSend} disabled />
      </I18nProvider>,
    );
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled();
    expect(onSend).not.toHaveBeenCalled();
  });
});
