'use client';

import { CheckCircle2, AlertCircle } from 'lucide-react';

interface FormFieldProps {
  label: string;
  error?: string | null;
  success?: string;
  helper?: string;
  required?: boolean;
  children: React.ReactNode;
}

export function FormField({
  label,
  error,
  success,
  helper,
  required,
  children,
}: FormFieldProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-900">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {children}

      {error && (
        <div className="flex items-start gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && !error && (
        <div className="flex items-center gap-2 text-sm text-green-600">
          <CheckCircle2 className="w-4 h-4" />
          <span>{success}</span>
        </div>
      )}

      {helper && !error && !success && (
        <p className="text-sm text-gray-500">{helper}</p>
      )}
    </div>
  );
}
