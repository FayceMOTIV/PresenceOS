'use client';

import { useState, useCallback } from 'react';

export function useFormField(
  initialValue: string,
  validate: (value: string) => string | null
) {
  const [value, setValue] = useState(initialValue);
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  const handleChange = useCallback((newValue: string) => {
    setValue(newValue);
    if (touched) {
      setError(validate(newValue));
    }
  }, [touched, validate]);

  const handleBlur = useCallback(() => {
    setTouched(true);
    setError(validate(value));
  }, [value, validate]);

  const reset = useCallback(() => {
    setValue(initialValue);
    setError(null);
    setTouched(false);
  }, [initialValue]);

  return {
    value,
    error,
    touched,
    onChange: handleChange,
    onBlur: handleBlur,
    reset,
    isValid: !error && touched,
  };
}
