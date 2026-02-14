'use client';

export function LoadingMessage({ message, emoji = '✨' }: { message: string; emoji?: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-8">
      <div className="text-4xl animate-bounce">{emoji}</div>
      <p className="text-sm text-gray-600 animate-pulse">{message}</p>
    </div>
  );
}
