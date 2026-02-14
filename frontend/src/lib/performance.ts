/**
 * Core Web Vitals monitoring.
 * Targets: LCP < 2.5s, INP < 200ms, CLS < 0.1
 */

interface WebVitalMetric {
  name: string;
  value: number;
  rating: "good" | "needs-improvement" | "poor";
}

type ReportHandler = (metric: WebVitalMetric) => void;

const thresholds: Record<string, [number, number]> = {
  LCP: [2500, 4000],
  FID: [100, 300],
  CLS: [0.1, 0.25],
  TTFB: [800, 1800],
};

function getRating(name: string, value: number): WebVitalMetric["rating"] {
  const t = thresholds[name];
  if (!t) return "good";
  if (value <= t[0]) return "good";
  if (value <= t[1]) return "needs-improvement";
  return "poor";
}

export function measureWebVitals(onReport?: ReportHandler) {
  if (typeof window === "undefined") return;

  const report = (name: string, value: number) => {
    const metric: WebVitalMetric = { name, value, rating: getRating(name, value) };
    if (onReport) onReport(metric);
    if (process.env.NODE_ENV === "development") {
      const color = metric.rating === "good" ? "#10B981" : metric.rating === "needs-improvement" ? "#F59E0B" : "#EF4444";
      console.log(`%c[${name}] ${value.toFixed(1)}ms — ${metric.rating}`, `color: ${color}; font-weight: bold`);
    }
  };

  // LCP
  try {
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const last = entries[entries.length - 1] as PerformanceEntry & { renderTime?: number; loadTime?: number };
      report("LCP", last.renderTime || last.loadTime || last.startTime);
    }).observe({ type: "largest-contentful-paint", buffered: true });
  } catch {}

  // FID
  try {
    new PerformanceObserver((list) => {
      list.getEntries().forEach((entry: PerformanceEntry & { processingStart?: number }) => {
        if (entry.processingStart) {
          report("FID", entry.processingStart - entry.startTime);
        }
      });
    }).observe({ type: "first-input", buffered: true });
  } catch {}

  // CLS
  try {
    let clsScore = 0;
    new PerformanceObserver((list) => {
      list.getEntries().forEach((entry: PerformanceEntry & { hadRecentInput?: boolean; value?: number }) => {
        if (!entry.hadRecentInput && entry.value) {
          clsScore += entry.value;
          report("CLS", clsScore);
        }
      });
    }).observe({ type: "layout-shift", buffered: true });
  } catch {}
}
