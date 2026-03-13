/**
 * Tests du AnalyticsScreen
 */

import React from "react";
import { render, renderAsync, screen, waitFor } from "@testing-library/react-native";
import AnalyticsScreen from "@/screens/analytics/AnalyticsScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { brainApi } from "@/lib/api";

jest.setTimeout(60000);

jest.mock("@/lib/api", () => ({
  brainApi: {
    analytics: jest.fn(),
    calendarEvents: jest.fn(),
  },
}));

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: jest.fn(), navigate: jest.fn() }),
  useRoute: () => ({ params: {} }),
}));

const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

const mockAnalytics = {
  period_days: 30,
  total_posts: 24,
  total_engagement: 1580,
  avg_engagement_rate: 4.2,
  best_performing_type: "Reel",
  best_day: "Vendredi",
  best_time: "12:00",
  growth_trend: "up",
  ai_insights: ["Les Reels performent 2x mieux que les posts classiques"],
  recommendations: ["Publiez plus de contenu vidéo le vendredi"],
};

const mockEvents = [
  {
    name: "Ramadan",
    date: "2026-03-15",
    content_ideas: ["Menu spécial iftar", "Ambiance ramadan"],
    priority: "high" as const,
  },
  {
    name: "Fête des mères",
    date: "2026-05-31",
    content_ideas: ["Offre spéciale maman"],
    priority: "medium" as const,
  },
];

async function renderAnalytics(brand = mockBrand) {
  return renderAsync(
    <BrandContext.Provider value={brand as any}>
      <AnalyticsScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (brainApi.analytics as jest.Mock).mockResolvedValue({ data: mockAnalytics });
  (brainApi.calendarEvents as jest.Mock).mockResolvedValue({ data: { events: mockEvents } });
});

describe("AnalyticsScreen — Rendu", () => {
  test("affiche le titre Analytics", async () => {
    await renderAnalytics();
    expect(screen.getByText("Analytics")).toBeTruthy();
  });

  test("affiche le sous-titre", async () => {
    await renderAnalytics();
    expect(screen.getByText("Performance de votre contenu")).toBeTruthy();
  });
});

describe("AnalyticsScreen — KPIs", () => {
  test("affiche le nombre de posts", async () => {
    await renderAnalytics();
    expect(screen.getByText("24")).toBeTruthy();
    expect(screen.getByText("Posts")).toBeTruthy();
  });

  test("affiche les engagements", async () => {
    await renderAnalytics();
    expect(screen.getByText("1580")).toBeTruthy();
    expect(screen.getByText("Engagements")).toBeTruthy();
  });

  test("affiche le taux moyen", async () => {
    await renderAnalytics();
    expect(screen.getByText("4.2%")).toBeTruthy();
    expect(screen.getByText("Taux moy.")).toBeTruthy();
  });
});

describe("AnalyticsScreen — Meilleure performance", () => {
  test("affiche le type de contenu le plus performant", async () => {
    await renderAnalytics();
    expect(screen.getByText("Meilleure performance")).toBeTruthy();
    expect(screen.getByText("Reel")).toBeTruthy();
  });

  test("affiche le meilleur jour et heure", async () => {
    await renderAnalytics();
    expect(screen.getByText("Vendredi")).toBeTruthy();
    expect(screen.getByText("12:00")).toBeTruthy();
  });

  test("affiche la tendance de croissance", async () => {
    await renderAnalytics();
    expect(screen.getByText("↑ En hausse")).toBeTruthy();
  });

  test("affiche tendance stable", async () => {
    (brainApi.analytics as jest.Mock).mockResolvedValue({
      data: { ...mockAnalytics, growth_trend: "stable" },
    });
    await renderAnalytics();
    expect(screen.getByText("→ Stable")).toBeTruthy();
  });

  test("affiche tendance en baisse", async () => {
    (brainApi.analytics as jest.Mock).mockResolvedValue({
      data: { ...mockAnalytics, growth_trend: "down" },
    });
    await renderAnalytics();
    expect(screen.getByText("↓ En baisse")).toBeTruthy();
  });
});

describe("AnalyticsScreen — Insights & Recommandations", () => {
  test("affiche les insights IA", async () => {
    await renderAnalytics();
    expect(screen.getByText("Insights IA")).toBeTruthy();
    expect(screen.getByText("Les Reels performent 2x mieux que les posts classiques")).toBeTruthy();
  });

  test("affiche les recommandations", async () => {
    await renderAnalytics();
    expect(screen.getByText("Recommandations")).toBeTruthy();
    expect(screen.getByText("Publiez plus de contenu vidéo le vendredi")).toBeTruthy();
  });
});

describe("AnalyticsScreen — Événements", () => {
  test("affiche les événements à venir", async () => {
    await renderAnalytics();
    expect(screen.getByText("Événements à venir")).toBeTruthy();
    expect(screen.getByText("Ramadan")).toBeTruthy();
    expect(screen.getByText("Fête des mères")).toBeTruthy();
  });

  test("affiche les priorités", async () => {
    await renderAnalytics();
    expect(screen.getByText("Haute priorité")).toBeTruthy();
    expect(screen.getByText("Moyenne")).toBeTruthy();
  });

  test("affiche les idées de contenu", async () => {
    await renderAnalytics();
    expect(screen.getByText(/Menu spécial iftar/)).toBeTruthy();
  });
});

describe("AnalyticsScreen — API", () => {
  test("appelle brainApi avec brandId", async () => {
    await renderAnalytics();
    expect(brainApi.analytics).toHaveBeenCalledWith("brand-1");
    expect(brainApi.calendarEvents).toHaveBeenCalledWith("brand-1");
  });

  test("ne charge pas sans activeBrand", async () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <AnalyticsScreen />
      </BrandContext.Provider>
    );
    await waitFor(() => {
      expect(brainApi.analytics).not.toHaveBeenCalled();
    });
  });
});
