/**
 * Tests du InboxScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import InboxScreen from "@/screens/inbox/InboxScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { cmApi, engageApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  cmApi: { listInteractions: jest.fn(), approve: jest.fn(), reject: jest.fn() },
  engageApi: { inbox: jest.fn(), scan: jest.fn(), approve: jest.fn(), reject: jest.fn() },
}));

jest.mock("@/components/EmptyStateCard", () => {
  const React = require("react");
  const { Text, TouchableOpacity } = require("react-native");
  return function MockEmptyStateCard({ title, body, ctaLabel, onCta }: any) {
    return (
      <>
        <Text>{title}</Text>
        <Text>{body}</Text>
        {ctaLabel && onCta && (
          <TouchableOpacity onPress={onCta}>
            <Text>{ctaLabel}</Text>
          </TouchableOpacity>
        )}
      </>
    );
  };
});

const mockNavigate = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ navigate: mockNavigate, goBack: jest.fn() }),
  useRoute: () => ({ params: {} }),
}));

const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

function renderInbox(brand = mockBrand) {
  return render(
    <BrandContext.Provider value={brand as any}>
      <InboxScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (cmApi.listInteractions as jest.Mock).mockResolvedValue({
    data: { interactions: [] },
  });
  (engageApi.inbox as jest.Mock).mockResolvedValue({ data: [] });
});

describe("InboxScreen — Rendu", () => {
  test("affiche le titre Inbox", async () => {
    renderInbox();
    expect(screen.getByText("Inbox")).toBeTruthy();
  });

  test("affiche les onglets de filtre", async () => {
    renderInbox();
    await waitFor(() => {
      expect(screen.getByText(/Tout/)).toBeTruthy();
      expect(screen.getByText(/En attente/)).toBeTruthy();
      expect(screen.getByText(/Urgents/)).toBeTruthy();
      expect(screen.getByText(/Traites/)).toBeTruthy();
    });
  });

  test("affiche le bouton CM Chat IA", () => {
    renderInbox();
    expect(screen.getByText("CM Chat IA")).toBeTruthy();
  });
});

describe("InboxScreen — Chargement", () => {
  test("appelle cmApi et engageApi au montage", async () => {
    renderInbox();
    await waitFor(() => {
      expect(cmApi.listInteractions).toHaveBeenCalledWith("brand-1");
      expect(engageApi.inbox).toHaveBeenCalledWith("brand-1");
    });
  });

  test("affiche empty state si aucun item", async () => {
    renderInbox();
    await waitFor(() => {
      expect(screen.getByText("Aucun message")).toBeTruthy();
    });
  });
});

describe("InboxScreen — Items", () => {
  const mockItems = [
    {
      id: "c1",
      platform: "instagram",
      author_name: "Alice",
      text: "Super restaurant !",
      sentiment: "positive",
      urgency_score: 3,
      suggested_reply: "Merci Alice !",
      reply_status: "pending",
      final_reply: "",
      created_at: "2026-01-01",
      is_dm: false,
    },
  ];

  test("affiche les items de la inbox (engage)", async () => {
    (engageApi.inbox as jest.Mock).mockResolvedValue({ data: mockItems });
    renderInbox();
    await waitFor(() => {
      expect(screen.getByText("Alice")).toBeTruthy();
      expect(screen.getByText("Super restaurant !")).toBeTruthy();
    });
  });

  test("affiche les items de la inbox (cm)", async () => {
    (cmApi.listInteractions as jest.Mock).mockResolvedValue({
      data: {
        interactions: [{
          id: "r1",
          platform: "google",
          commenter_name: "Bob",
          content: "Excellent !",
          ai_response_draft: "Merci Bob",
          response_status: "pending",
          created_at: "2026-01-01",
        }],
      },
    });
    renderInbox();
    await waitFor(() => {
      expect(screen.getByText("Bob")).toBeTruthy();
      expect(screen.getByText("Excellent !")).toBeTruthy();
    });
  });
});

describe("InboxScreen — Navigation", () => {
  test("CM Chat button navigue vers CMChat", () => {
    renderInbox();
    fireEvent.press(screen.getByText("CM Chat IA"));
    expect(mockNavigate).toHaveBeenCalledWith("CMChat");
  });
});

describe("InboxScreen — Filtres", () => {
  test("filtre En attente filtre correctement", async () => {
    const items = [
      { id: "c1", platform: "instagram", author_name: "A", text: "T1", sentiment: "neutral", urgency_score: 0, suggested_reply: "", reply_status: "pending", final_reply: "", created_at: "", is_dm: false },
      { id: "c2", platform: "instagram", author_name: "B", text: "T2", sentiment: "neutral", urgency_score: 0, suggested_reply: "", reply_status: "approved", final_reply: "", created_at: "", is_dm: false },
    ];
    (engageApi.inbox as jest.Mock).mockResolvedValue({ data: items });
    renderInbox();
    await waitFor(() => {
      expect(screen.getByText("A")).toBeTruthy();
      expect(screen.getByText("B")).toBeTruthy();
    });
    fireEvent.press(screen.getByText(/En attente/));
    await waitFor(() => {
      expect(screen.getByText("A")).toBeTruthy();
      expect(screen.queryByText("B")).toBeNull();
    });
  });
});

describe("InboxScreen — Sans brand", () => {
  test("ne charge pas sans brandId", async () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <InboxScreen />
      </BrandContext.Provider>
    );
    expect(cmApi.listInteractions).not.toHaveBeenCalled();
    expect(engageApi.inbox).not.toHaveBeenCalled();
  });
});
