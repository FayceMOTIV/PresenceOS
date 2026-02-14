'use client';

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { HelpCircle } from 'lucide-react';

interface Props {
  content: string;
}

export function HelpTooltip({ content }: Props) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button className="inline-flex items-center justify-center w-4 h-4 ml-1.5 text-gray-400 hover:text-gray-600 cursor-help">
            <HelpCircle className="w-4 h-4" />
          </button>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs bg-gray-900 text-white p-3 text-sm">
          {content}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
