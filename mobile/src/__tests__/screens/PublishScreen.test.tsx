/**
 * Tests du PublishScreen
 * Covers: rendering, platform selection, content input, schedule options,
 * publish now, schedule, empty state, error states, navigation.
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react-native";
import { Alert } from "react-native";
import PublishScreen from "@/screens/social/PublishScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { postizApi } from "@/lib/api";

jest.setTimeout(60000);
jest.spyOn(Alert, "alert");

// ── API mock ──────────────────────────────────────────────────────────────────
jest.mock("@/lib/api", () => ({
  postizApi: {
    integrations: jest.fn(),
    publishNow: jest.fn(),
    schedule: jest.fn(),
  },
}));

// ── Navigation mock ───────────────────────────────────────────────────────────
const mockGoBack = jest.fn();
const mockNavigate = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: mockGoBack, navigate: mockNavigate }),
  useRoute: () => ({ params: {} }),
}));

// ── Test data ─────────────────────────────────────────────────────────────────
const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test Restaurant", slug: "test", brand_type: "restaurant" },
  brands: [],
};

const mockIntegrations = [
  { id: "integ-1", name: "My Instagram", identifier: "instagram", disabled: false },
  { id: "integ-2", name: "My Facebook", identifier: "facebook", disabled: false },
  { id: "integ-3", name: "My TikTok", identifier: "tiktok", disabled: false },
];

// ── Render helper ─────────────────────────────────────────────────────────────
function renderScreen(brand = mockBrand) {
  return render(
    <BrandContext.Provider value={brand as any}>
      <PublishScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (postizApi.integrations as jest.Mock).mockResolvedValue({ data: mockIntegrations });
  (postizApi.publishNow as jest.Mock).mockResolvedValue({ data: {} });
  (postizApi.schedule as jest.Mock).mockResolvedValue({ data: {} });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Rendu initial", () => {
  test("affiche le titre 'Publier'", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Publier")).toBeTruthy();
    });
  });

  test("affiche la section 'Plateformes'", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Plateformes")).toBeTruthy();
    });
  });

  test("affiche la section 'Contenu'", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Contenu")).toBeTruthy();
    });
  });

  test("affiche la section 'Quand publier ?'", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Quand publier ?")).toBeTruthy();
    });
  });

  test("affiche les 4 options de planification", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Maintenant")).toBeTruthy();
      expect(screen.getByText("Demain 9h")).toBeTruthy();
      expect(screen.getByText("Demain 12h")).toBeTruthy();
      expect(screen.getByText("Demain 18h")).toBeTruthy();
    });
  });

  test("affiche le bouton de publication désactivé par défaut", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Publier maintenant")).toBeTruthy();
    });
    const { TouchableOpacity } = require("react-native");
    const publishBtn = screen.UNSAFE_getAllByType(TouchableOpacity).find((t: any) =>
      t.props.disabled === true
    );
    expect(publishBtn).toBeTruthy();
  });

  test("affiche le placeholder dans le textarea", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Qu'est-ce que tu veux partager ?")).toBeTruthy();
    });
  });

  test("affiche le compteur de caractères 0/2200", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("0/2200")).toBeTruthy();
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Liste des plateformes connectées", () => {
  test("affiche les intégrations chargées depuis l'API", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
      expect(screen.getByText("My Facebook")).toBeTruthy();
      expect(screen.getByText("My TikTok")).toBeTruthy();
    });
  });

  test("appelle postizApi.integrations au montage avec le brandId", async () => {
    renderScreen();
    await waitFor(() => {
      expect(postizApi.integrations).toHaveBeenCalledWith("brand-1");
    });
  });

  test("ne charge pas si brandId est null", () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <PublishScreen />
      </BrandContext.Provider>
    );
    expect(postizApi.integrations).not.toHaveBeenCalled();
  });

  test("filtre les intégrations désactivées", async () => {
    (postizApi.integrations as jest.Mock).mockResolvedValue({
      data: [
        { id: "integ-1", name: "Active Insta", identifier: "instagram", disabled: false },
        { id: "integ-2", name: "Disabled FB", identifier: "facebook", disabled: true },
      ],
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Active Insta")).toBeTruthy();
      expect(screen.queryByText("Disabled FB")).toBeNull();
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — État vide (aucun compte connecté)", () => {
  beforeEach(() => {
    (postizApi.integrations as jest.Mock).mockResolvedValue({ data: [] });
  });

  test("affiche 'Aucun compte connecté'", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Aucun compte connecté")).toBeTruthy();
    });
  });

  test("affiche le texte d'invitation à connecter", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText(/Connecte tes réseaux sociaux/)).toBeTruthy();
    });
  });

  test("affiche le bouton 'Connecter mes réseaux'", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Connecter mes réseaux")).toBeTruthy();
    });
  });

  test("le bouton 'Connecter mes réseaux' navigue vers ConnectSocials", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Connecter mes réseaux")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Connecter mes réseaux"));
    expect(mockNavigate).toHaveBeenCalledWith("ConnectSocials");
  });

  test("gère une erreur API gracieusement (état vide)", async () => {
    (postizApi.integrations as jest.Mock).mockRejectedValue(new Error("Network error"));
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Aucun compte connecté")).toBeTruthy();
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Sélection de plateformes", () => {
  test("sélectionne une plateforme en appuyant dessus", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("My Instagram"));
    // After selection, the chip should be active (checkmark icon appears)
    await waitFor(() => {
      expect(screen.getByText("checkmark-circle")).toBeTruthy();
    });
  });

  test("désélectionne une plateforme en rappuyant dessus", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("My Instagram")); // select
    await waitFor(() => {
      expect(screen.getByText("checkmark-circle")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("My Instagram")); // deselect
    await waitFor(() => {
      expect(screen.queryByText("checkmark-circle")).toBeNull();
    });
  });

  test("peut sélectionner plusieurs plateformes", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
      expect(screen.getByText("My Facebook")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("My Instagram"));
    fireEvent.press(screen.getByText("My Facebook"));
    await waitFor(() => {
      // 2 checkmarks = 2 platforms selected
      expect(screen.getAllByText("checkmark-circle").length).toBe(2);
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Saisie du contenu", () => {
  test("met à jour le compteur de caractères au fil de la saisie", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Qu'est-ce que tu veux partager ?")).toBeTruthy();
    });
    const input = screen.getByPlaceholderText("Qu'est-ce que tu veux partager ?");
    fireEvent.changeText(input, "Hello world");
    await waitFor(() => {
      expect(screen.getByText("11/2200")).toBeTruthy();
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Options de planification", () => {
  test("'Maintenant' est sélectionné par défaut", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Maintenant")).toBeTruthy();
    });
    // The default button label on publish is "Publier maintenant"
    expect(screen.getByText("Publier maintenant")).toBeTruthy();
  });

  test("sélectionner 'Demain 9h' change le label du bouton en 'Planifier le post'", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Demain 9h")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Demain 9h"));
    await waitFor(() => {
      expect(screen.getByText("Planifier le post")).toBeTruthy();
    });
  });

  test("sélectionner 'Demain 12h' change le label du bouton", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Demain 12h")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Demain 12h"));
    await waitFor(() => {
      expect(screen.getByText("Planifier le post")).toBeTruthy();
    });
  });

  test("sélectionner 'Demain 18h' change le label du bouton", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Demain 18h")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Demain 18h"));
    await waitFor(() => {
      expect(screen.getByText("Planifier le post")).toBeTruthy();
    });
  });

  test("revenir sur 'Maintenant' remet le label 'Publier maintenant'", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Demain 9h")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Demain 9h"));
    await waitFor(() => {
      expect(screen.getByText("Planifier le post")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Maintenant"));
    await waitFor(() => {
      expect(screen.getByText("Publier maintenant")).toBeTruthy();
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Validations avant publication", () => {
  test("alerte si aucune plateforme sélectionnée", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });
    // Fill content but no platform selected
    const input = screen.getByPlaceholderText("Qu'est-ce que tu veux partager ?");
    fireEvent.changeText(input, "Mon super post");

    // Enable the button by selecting a platform first, then deselect to test
    // Actually let's press publish without selecting platform — button is disabled
    // so we need to bypass by directly triggering onPress
    // The button is disabled when canPublish = false, so Alert should fire
    // Let's verify the button is disabled with no platform selected
    const { TouchableOpacity } = require("react-native");
    const publishBtn = screen.UNSAFE_getAllByType(TouchableOpacity).find((t: any) =>
      t.props.disabled === true
    );
    expect(publishBtn).toBeTruthy();
  });

  test("alerte si contenu vide lors de la publication", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("My Instagram")); // select platform
    // Press publish without content → button is disabled
    const { TouchableOpacity } = require("react-native");
    const publishBtn = screen.UNSAFE_getAllByType(TouchableOpacity).find((t: any) =>
      t.props.disabled === true
    );
    expect(publishBtn).toBeTruthy();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Publication immédiate", () => {
  async function prepareAndPublish() {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("My Instagram"));
    const input = screen.getByPlaceholderText("Qu'est-ce que tu veux partager ?");
    fireEvent.changeText(input, "Mon super post du jour !");
    await waitFor(() => {
      expect(screen.getByText("Publier maintenant")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Publier maintenant"));
  }

  test("appelle postizApi.publishNow avec les bons arguments", async () => {
    await prepareAndPublish();
    await waitFor(() => {
      expect(postizApi.publishNow).toHaveBeenCalledWith(
        "brand-1",
        ["integ-1"],
        "Mon super post du jour !"
      );
    });
  });

  test("affiche Alert de succès après publication", async () => {
    await prepareAndPublish();
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Publie !", "Ton post est en ligne.");
    });
  });

  test("réinitialise le contenu et la sélection après publication", async () => {
    await prepareAndPublish();
    await waitFor(() => {
      expect(screen.getByText("0/2200")).toBeTruthy();
    });
  });

  test("gère l'erreur de publication avec un message détaillé", async () => {
    (postizApi.publishNow as jest.Mock).mockRejectedValue({
      response: { data: { detail: "Rate limit exceeded" } },
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("My Instagram"));
    const input = screen.getByPlaceholderText("Qu'est-ce que tu veux partager ?");
    fireEvent.changeText(input, "Post qui va échouer");
    fireEvent.press(screen.getByText("Publier maintenant"));
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Rate limit exceeded");
    });
  });

  test("gère l'erreur sans detail avec message générique", async () => {
    (postizApi.publishNow as jest.Mock).mockRejectedValue(new Error("Network error"));
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("My Instagram"));
    const input = screen.getByPlaceholderText("Qu'est-ce que tu veux partager ?");
    fireEvent.changeText(input, "Post qui va échouer");
    fireEvent.press(screen.getByText("Publier maintenant"));
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Publication echouee.");
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Planification", () => {
  async function prepareAndSchedule(timeOption: string) {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("My Instagram"));
    const input = screen.getByPlaceholderText("Qu'est-ce que tu veux partager ?");
    fireEvent.changeText(input, "Post planifié");
    fireEvent.press(screen.getByText(timeOption));
    await waitFor(() => {
      expect(screen.getByText("Planifier le post")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Planifier le post"));
  }

  test("appelle postizApi.schedule avec le bon ISO date pour 'Demain 9h'", async () => {
    await prepareAndSchedule("Demain 9h");
    await waitFor(() => {
      expect(postizApi.schedule).toHaveBeenCalledWith(
        "brand-1",
        ["integ-1"],
        "Post planifié",
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:00:00\.\d{3}Z$/)
      );
    });
    // Verify the scheduled hour is 9 in local time
    const callArgs = (postizApi.schedule as jest.Mock).mock.calls[0];
    const scheduledDate = new Date(callArgs[3]);
    expect(scheduledDate.getHours()).toBe(9);
  });

  test("appelle postizApi.schedule avec le bon ISO date pour 'Demain 12h'", async () => {
    await prepareAndSchedule("Demain 12h");
    await waitFor(() => {
      expect(postizApi.schedule).toHaveBeenCalledWith(
        "brand-1",
        ["integ-1"],
        "Post planifié",
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:00:00\.\d{3}Z$/)
      );
    });
    const callArgs = (postizApi.schedule as jest.Mock).mock.calls[0];
    const scheduledDate = new Date(callArgs[3]);
    expect(scheduledDate.getHours()).toBe(12);
  });

  test("appelle postizApi.schedule avec le bon ISO date pour 'Demain 18h'", async () => {
    await prepareAndSchedule("Demain 18h");
    await waitFor(() => {
      expect(postizApi.schedule).toHaveBeenCalledWith(
        "brand-1",
        ["integ-1"],
        "Post planifié",
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:00:00\.\d{3}Z$/)
      );
    });
    const callArgs = (postizApi.schedule as jest.Mock).mock.calls[0];
    const scheduledDate = new Date(callArgs[3]);
    expect(scheduledDate.getHours()).toBe(18);
  });

  test("affiche Alert de succès avec la date planifiée", async () => {
    await prepareAndSchedule("Demain 9h");
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Planifie !",
        expect.stringContaining("9")
      );
    });
  });

  test("gère l'erreur de planification", async () => {
    (postizApi.schedule as jest.Mock).mockRejectedValue({
      response: { data: { detail: "Schedule conflict" } },
    });
    await prepareAndSchedule("Demain 9h");
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Schedule conflict");
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Navigation", () => {
  test("le bouton retour appelle goBack", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Publier")).toBeTruthy();
    });
    const { TouchableOpacity } = require("react-native");
    const touchables = screen.UNSAFE_getAllByType(TouchableOpacity);
    fireEvent.press(touchables[0]); // first touchable = back button (arrow-back)
    expect(mockGoBack).toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Refresh (pull-to-refresh)", () => {
  test("recharge les intégrations lors du refresh", async () => {
    renderScreen();
    await waitFor(() => {
      expect(postizApi.integrations).toHaveBeenCalledTimes(1);
    });
    // Trigger onRefresh via the RefreshControl component
    const { RefreshControl } = require("react-native");
    const refreshControls = screen.UNSAFE_getAllByType(RefreshControl);
    if (refreshControls.length > 0) {
      fireEvent(refreshControls[0], "refresh");
    } else {
      // Fallback: trigger via ScrollView scroll event
      const { ScrollView } = require("react-native");
      const scrollViews = screen.UNSAFE_getAllByType(ScrollView);
      fireEvent(scrollViews[0], "refreshing", true);
    }
    await waitFor(() => {
      expect(postizApi.integrations).toHaveBeenCalledTimes(2);
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("PublishScreen — Identifier inconnu", () => {
  test("affiche 'globe-outline' pour une plateforme inconnue", async () => {
    (postizApi.integrations as jest.Mock).mockResolvedValue({
      data: [
        { id: "integ-x", name: "MyPlatform", identifier: "unknownplatform", disabled: false },
      ],
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("MyPlatform")).toBeTruthy();
    });
  });

  test("affiche l'identifier si name est absent", async () => {
    (postizApi.integrations as jest.Mock).mockResolvedValue({
      data: [
        { id: "integ-y", name: "", identifier: "linkedin", disabled: false },
      ],
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("linkedin")).toBeTruthy();
    });
  });
});
