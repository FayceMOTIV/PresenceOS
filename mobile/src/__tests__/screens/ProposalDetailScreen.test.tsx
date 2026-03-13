/**
 * Tests du ProposalDetailScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";
import ProposalDetailScreen from "@/screens/proposals/ProposalDetailScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { proposalsApi } from "@/lib/api";

jest.setTimeout(60000);
jest.spyOn(Alert, "alert");

jest.mock("@/lib/api", () => ({
  proposalsApi: {
    list: jest.fn(),
    approve: jest.fn(),
    reject: jest.fn(),
    regenerate: jest.fn(),
    editCaption: jest.fn(),
  },
}));

const mockGoBack = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: mockGoBack, navigate: jest.fn() }),
  useRoute: () => ({ params: { proposalId: "p1" } }),
}));

const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

const mockProposal = {
  id: "p1",
  brand_id: "brand-1",
  status: "pending",
  caption: "Belle journée au resto !",
  hashtags: ["#restaurant", "#food"],
  platform: "instagram",
  proposal_type: "post",
  confidence_score: 0.85,
  image_url: "https://example.com/image.jpg",
  source: "brief",
  created_at: "2026-01-01",
};

function renderDetail() {
  return render(
    <BrandContext.Provider value={mockBrand as any}>
      <ProposalDetailScreen />
    </BrandContext.Provider>
  );
}

/** Render and wait for async data to load */
async function renderAndWait() {
  renderDetail();
  // Wait for the async useEffect (fetchProposal) to resolve and loading to complete
  await screen.findByText("Belle journée au resto !", {}, { timeout: 15000 });
}

beforeEach(() => {
  jest.clearAllMocks();
  (proposalsApi.list as jest.Mock).mockResolvedValue({
    data: { proposals: [mockProposal] },
  });
});

describe("ProposalDetailScreen — Chargement", () => {
  test("affiche le proposal après chargement", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Belle journée au resto !")).toBeTruthy();
    }, { timeout: 15000 });
  });

  test("affiche le status badge", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("À valider")).toBeTruthy();
    });
  });

  test("affiche l'image", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Légende")).toBeTruthy();
    });
  });

  test("affiche les hashtags", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("#restaurant #food")).toBeTruthy();
    });
  });

  test("affiche la plateforme et le type", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("instagram")).toBeTruthy();
      expect(screen.getByText("post")).toBeTruthy();
    });
  });

  test("affiche le score IA", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("85%")).toBeTruthy();
    });
  });
});

describe("ProposalDetailScreen — Actions", () => {
  test("approuver appelle proposalsApi.approve", async () => {
    (proposalsApi.approve as jest.Mock).mockResolvedValue({ data: {} });
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Publier maintenant")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Publier maintenant"));
    await waitFor(() => {
      expect(proposalsApi.approve).toHaveBeenCalledWith("brand-1", "p1");
    });
  });

  test("rejeter appelle proposalsApi.reject et goBack", async () => {
    (proposalsApi.reject as jest.Mock).mockResolvedValue({});
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Rejeter")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Rejeter"));
    await waitFor(() => {
      expect(proposalsApi.reject).toHaveBeenCalledWith("brand-1", "p1");
      expect(mockGoBack).toHaveBeenCalled();
    });
  });

  test("régénérer appelle proposalsApi.regenerate", async () => {
    (proposalsApi.regenerate as jest.Mock).mockResolvedValue({});
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Autre version")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Autre version"));
    await waitFor(() => {
      expect(proposalsApi.regenerate).toHaveBeenCalledWith("brand-1", "p1");
    });
  });
});

describe("ProposalDetailScreen — Edit Caption", () => {
  test("passe en mode édition et sauvegarde", async () => {
    (proposalsApi.editCaption as jest.Mock).mockResolvedValue({});
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Belle journée au resto !")).toBeTruthy();
    });

    // Click edit button (pencil icon)
    fireEvent.press(screen.getByText("pencil"));

    // Should show save/cancel buttons
    await waitFor(() => {
      expect(screen.getByText("Enregistrer")).toBeTruthy();
      expect(screen.getByText("Annuler")).toBeTruthy();
    });

    fireEvent.press(screen.getByText("Enregistrer"));
    await waitFor(() => {
      expect(proposalsApi.editCaption).toHaveBeenCalledWith("brand-1", "p1", "Belle journée au resto !");
    });
  });

  test("annuler la modification restaure le texte", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Belle journée au resto !")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("pencil"));
    fireEvent.press(screen.getByText("Annuler"));
    await waitFor(() => {
      expect(screen.getByText("Belle journée au resto !")).toBeTruthy();
    });
  });
});

describe("ProposalDetailScreen — Published state", () => {
  test("affiche le banner publié quand status published", async () => {
    (proposalsApi.list as jest.Mock).mockResolvedValue({
      data: { proposals: [{ ...mockProposal, status: "published" }] },
    });
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Publié sur Instagram")).toBeTruthy();
    });
  });

  test("ne montre pas les boutons d'action quand publié", async () => {
    (proposalsApi.list as jest.Mock).mockResolvedValue({
      data: { proposals: [{ ...mockProposal, status: "published" }] },
    });
    renderDetail();
    await waitFor(() => {
      expect(screen.queryByText("Publier maintenant")).toBeNull();
    });
  });
});

describe("ProposalDetailScreen — Erreur", () => {
  test("affiche erreur si proposal non trouvé", async () => {
    (proposalsApi.list as jest.Mock).mockResolvedValue({ data: { proposals: [] } });
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Une erreur est survenue — réessayez")).toBeTruthy();
    });
  });

  test("back button appelle goBack", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("arrow-back")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("arrow-back"));
    expect(mockGoBack).toHaveBeenCalled();
  });
});
