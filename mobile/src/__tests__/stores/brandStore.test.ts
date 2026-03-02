/**
 * Tests du Brand Store (legacy Zustand + SecureStore)
 */

import * as SecureStore from "expo-secure-store";
import { useBrandStore } from "@/stores/brandStore";

const BRANDS = [
  { id: "b1", name: "Le Family's", slug: "familys", brand_type: "restaurant" },
  { id: "b2", name: "Chez Marco", slug: "chez-marco", brand_type: "restaurant" },
];

beforeEach(() => {
  useBrandStore.setState({
    brands: [],
    activeBrand: null,
    isLoading: true,
  });
  jest.clearAllMocks();
});

describe("BrandStore — setBrands", () => {
  test("met à jour la liste des marques", () => {
    useBrandStore.getState().setBrands(BRANDS as any);
    expect(useBrandStore.getState().brands).toHaveLength(2);
  });
});

describe("BrandStore — switchBrand", () => {
  test("change la marque active et persiste", () => {
    useBrandStore.setState({ brands: BRANDS as any });
    useBrandStore.getState().switchBrand("b2");

    expect(useBrandStore.getState().activeBrand?.id).toBe("b2");
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
      "active_brand_id",
      "b2"
    );
  });

  test("ignore un brandId inexistant", () => {
    useBrandStore.setState({ brands: BRANDS as any, activeBrand: BRANDS[0] as any });
    useBrandStore.getState().switchBrand("inexistant");

    expect(useBrandStore.getState().activeBrand?.id).toBe("b1");
  });
});

describe("BrandStore — loadBrands", () => {
  test("restaure la marque sauvegardée", async () => {
    (SecureStore.getItemAsync as jest.Mock).mockResolvedValue("b2");

    await useBrandStore.getState().loadBrands(BRANDS as any);

    expect(useBrandStore.getState().activeBrand?.id).toBe("b2");
    expect(useBrandStore.getState().isLoading).toBe(false);
  });

  test("prend la première si aucune sauvegardée", async () => {
    (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);

    await useBrandStore.getState().loadBrands(BRANDS as any);

    expect(useBrandStore.getState().activeBrand?.id).toBe("b1");
  });

  test("gère une liste vide", async () => {
    await useBrandStore.getState().loadBrands([]);

    expect(useBrandStore.getState().brands).toHaveLength(0);
    expect(useBrandStore.getState().activeBrand).toBeNull();
    expect(useBrandStore.getState().isLoading).toBe(false);
  });
});

describe("BrandStore — reset", () => {
  test("réinitialise le state et supprime la clé SecureStore", () => {
    useBrandStore.setState({
      brands: BRANDS as any,
      activeBrand: BRANDS[0] as any,
      isLoading: false,
    });

    useBrandStore.getState().reset();

    const state = useBrandStore.getState();
    expect(state.brands).toHaveLength(0);
    expect(state.activeBrand).toBeNull();
    expect(state.isLoading).toBe(true);
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith("active_brand_id");
  });
});
