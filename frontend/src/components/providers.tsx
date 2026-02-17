"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
// import { SessionProvider } from "next-auth/react"; // DISABLED FOR TESTING
import { useEffect, useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { measureWebVitals } from "@/lib/performance";
import { analytics } from '@/lib/analytics';

export function Providers({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    measureWebVitals();
    analytics.page(window.location.pathname);
  }, []);

  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="light"
        forcedTheme="light"
        disableTransitionOnChange
      >
        {children}
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
