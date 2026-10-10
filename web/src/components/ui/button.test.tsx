import { render, screen } from '@testing-library/react';

import { Button } from './button';

describe('Button', () => {
  it('renders children and applies the variant classes', () => {
    render(<Button variant="danger">Delete</Button>);
    const btn = screen.getByRole('button', { name: 'Delete' });
    expect(btn).toHaveClass('bg-danger');
  });

  it('is disabled and busy while loading', () => {
    render(<Button loading>Save</Button>);
    const btn = screen.getByRole('button', { name: 'Save' });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute('aria-busy', 'true');
  });
});
