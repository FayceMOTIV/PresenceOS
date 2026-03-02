/**
 * Tests du AssetUploadScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import AssetUploadScreen from "@/screens/files/AssetUploadScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { assetsApi, contentApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  assetsApi: { upload: jest.fn() },
  contentApi: { listDishes: jest.fn() },
}));

jest.mock("expo-image-picker", () => ({
  launchImageLibraryAsync: jest.fn().mockResolvedValue({
    canceled: false,
    assets: [{ uri: "file://photo.jpg" }],
  }),
  launchCameraAsync: jest.fn().mockResolvedValue({
    canceled: false,
    assets: [{ uri: "file://camera.jpg" }],
  }),
  requestCameraPermissionsAsync: jest.fn().mockResolvedValue({ status: "granted" }),
}));

const mockGoBack = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: mockGoBack, navigate: jest.fn() }),
}));

const mockBrand = {
  activeBrand: { id: "b1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

function renderUpload() {
  return render(
    <BrandContext.Provider value={mockBrand as any}>
      <AssetUploadScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (contentApi.listDishes as jest.Mock).mockResolvedValue({ data: { dishes: [] } });
  (assetsApi.upload as jest.Mock).mockResolvedValue({});
});

describe("AssetUploadScreen — Rendu", () => {
  test("affiche le titre", () => {
    renderUpload();
    expect(screen.getByText("Ajouter un média")).toBeTruthy();
  });

  test("affiche les 2 boutons picker", () => {
    renderUpload();
    expect(screen.getByText("Choisir une photo")).toBeTruthy();
    expect(screen.getByText("Prendre une photo")).toBeTruthy();
  });

  test("affiche le champ label", () => {
    renderUpload();
    expect(screen.getByPlaceholderText("Nom du plat ou description...")).toBeTruthy();
  });

  test("bouton upload présent", () => {
    renderUpload();
    expect(screen.getByText("Uploader")).toBeTruthy();
  });
});

describe("AssetUploadScreen — Dishes", () => {
  test("affiche les dishes quand disponibles", async () => {
    (contentApi.listDishes as jest.Mock).mockResolvedValue({
      data: { dishes: [{ id: "d1", name: "Couscous" }] },
    });
    renderUpload();
    await waitFor(() => {
      expect(screen.getByText("Couscous")).toBeTruthy();
    });
  });
});

describe("AssetUploadScreen — Image Picker", () => {
  test("choisir une photo appelle launchImageLibraryAsync", async () => {
    const ImagePicker = require("expo-image-picker");
    renderUpload();
    fireEvent.press(screen.getByText("Choisir une photo"));
    await waitFor(() => {
      expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalled();
    });
  });

  test("prendre une photo demande permission puis lance la caméra", async () => {
    const ImagePicker = require("expo-image-picker");
    renderUpload();
    fireEvent.press(screen.getByText("Prendre une photo"));
    await waitFor(() => {
      expect(ImagePicker.requestCameraPermissionsAsync).toHaveBeenCalled();
      expect(ImagePicker.launchCameraAsync).toHaveBeenCalled();
    });
  });
});

describe("AssetUploadScreen — Upload", () => {
  test("upload appelle assetsApi.upload et goBack", async () => {
    const ImagePicker = require("expo-image-picker");
    (assetsApi.upload as jest.Mock).mockResolvedValue({});
    renderUpload();
    // First pick an image
    fireEvent.press(screen.getByText("Choisir une photo"));
    await waitFor(() => {
      expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalled();
    });
    // Set a label
    fireEvent.changeText(screen.getByPlaceholderText("Nom du plat ou description..."), "Mon plat");
    // Press upload
    fireEvent.press(screen.getByText("Uploader"));
    await waitFor(() => {
      expect(assetsApi.upload).toHaveBeenCalledWith("b1", expect.any(FormData));
      expect(mockGoBack).toHaveBeenCalled();
    });
  });
});

describe("AssetUploadScreen — Dish linking", () => {
  test("sélectionner un dish puis le désélectionner", async () => {
    (contentApi.listDishes as jest.Mock).mockResolvedValue({
      data: { dishes: [{ id: "d1", name: "Couscous" }] },
    });
    renderUpload();
    await waitFor(() => {
      expect(screen.getByText("Couscous")).toBeTruthy();
    });
    // Select
    fireEvent.press(screen.getByText("Couscous"));
    // Deselect
    fireEvent.press(screen.getByText("Couscous"));
  });
});

describe("AssetUploadScreen — Navigation", () => {
  test("close appelle goBack", () => {
    renderUpload();
    fireEvent.press(screen.getByText("close"));
    expect(mockGoBack).toHaveBeenCalled();
  });
});
