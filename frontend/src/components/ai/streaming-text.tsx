'use client';

import { useState, useEffect } from 'react';

export function StreamingText({ text, speed = 30 }: { text: string; speed?: number }) {
  const [displayed, setDisplayed] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    setDisplayed('');
    setCurrentIndex(0);
  }, [text]);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayed(text.slice(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, speed);
      return () => clearTimeout(timeout);
    }
  }, [currentIndex, text, speed]);

  return <span>{displayed}</span>;
}
