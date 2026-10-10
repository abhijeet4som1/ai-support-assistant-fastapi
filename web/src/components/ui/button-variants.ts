import { cva } from 'class-variance-authority';

export const buttonVariants = cva(
  'focus-visible:ring-ring focus-visible:outline-hidden inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground shadow-xs hover:bg-primary-hover',
        secondary: 'bg-primary-soft text-primary-soft-foreground hover:bg-primary-soft/70',
        outline: 'border-border bg-surface text-foreground shadow-xs hover:bg-muted border',
        ghost: 'text-foreground hover:bg-muted',
        danger: 'bg-danger text-danger-foreground shadow-xs hover:bg-danger/90',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-9 px-4',
        lg: 'h-10 px-6',
        icon: 'size-9',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
);
