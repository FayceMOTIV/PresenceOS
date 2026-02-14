'use client';

import { cn } from '@/lib/utils';

interface TouchButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost';
}

export function TouchButton({
  children,
  variant = 'primary',
  className,
  ...props
}: TouchButtonProps) {
  return (
    <button
      {...props}
      className={cn(
        'min-h-[44px] px-6 rounded-xl font-semibold transition-all active:scale-95',
        variant === 'primary' &&
          'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg',
        variant === 'secondary' &&
          'border-2 border-gray-300 hover:border-purple-500 hover:bg-gray-50',
        variant === 'ghost' && 'hover:bg-gray-100',
        className
      )}
    >
      {children}
    </button>
  );
}
