/**
 * Tests for businessStore (backend API version)
 */
import { useBusinessStore } from "@/stores/businessStore";
import { brandsV2Api } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  brandsV2Api: {
    mine: jest.fn(),
  },
}));

jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn().mockResolvedValue(null),
  setItemAsync: jest.fn().mockResolvedValue(undefined),
  deleteItemAsync: jest.fn().mockResolvedValue(undefined),
}));

const mockBrands = [
  { id: "brand-1", name: "Restaurant A", slug: "restaurant-a", brand_type: "restaurant", description: null, logo_url: null },
  { id: "brand-2", name: "Restaurant B", slug: "restaurant-b", brand_type: "restaurant", description: null, logo_url: null },
];

beforeEach(() => {
  useBusinessStore.getState().reset();
  jest.clearAllMocks();
});

describe("businessStore — initial state", () => {
  test("has correct defaults", () => {
    const state = useBusinessStore.getState();
    expect(state.brands).toEqual([]);
    expect(state.activeBrand).toBeNull();
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });
});

describe("businessStore — fetchBrands", () => {
  test("fetches brands from backend API", async () => {
    (brandsV2Api.mine as jest.Mock).mockResolvedValue({
      data: { brands: mockBrands },
    });

    await useBusinessStore.getState().fetchBrands();

    const state = useBusinessStore.getState();
    expect(state.brands).toHaveLength(2);
    expect(state.activeBrand?.id).toBe("brand-1");
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  test("sets first brand as active when no saved preference", async () => {
    (brandsV2Api.mine as jest.Mock).mockResolvedValue({
      data: { brands: mockBrands },
    });

    await useBusinessStore.getState().fetchBrands();

    expect(useBusinessStore.getState().activeBrand?.id).toBe("brand-1");
  });

  test("handles empty brands list", async () => {
    (brandsV2Api.mine as jest.Mock).mockResolvedValue({
      data: { brands: [] },
    });

    await useBusinessStore.getState().fetchBrands();

    const state = useBusinessStore.getState();
    expect(state.brands).toEqual([]);
    expect(state.activeBrand).toBeNull();
    expect(state.isLoading).toBe(false);
  });

  test("handles API error", async () => {
    (brandsV2Api.mine as jest.Mock).mockRejectedValue(new Error("Network error"));

    await useBusinessStore.getState().fetchBrands();

    const state = useBusinessStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe("Network error");
  });
});

describe("businessStore — switchBusiness", () => {
  test("switches active brand", async () => {
    (brandsV2Api.mine as jest.Mock).mockResolvedValue({
      data: { brands: mockBrands },
    });
    await useBusinessStore.getState().fetchBrands();

    useBusinessStore.getState().switchBusiness("brand-2");

    expect(useBusinessStore.getState().activeBrand?.id).toBe("brand-2");
    expect(useBusinessStore.getState().activeBrand?.name).toBe("Restaurant B");
  });

  test("ignores invalid brand id", async () => {
    (brandsV2Api.mine as jest.Mock).mockResolvedValue({
      data: { brands: mockBrands },
    });
    await useBusinessStore.getState().fetchBrands();

    useBusinessStore.getState().switchBusiness("invalid");

    expect(useBusinessStore.getState().activeBrand?.id).toBe("brand-1");
  });
});

describe("businessStore — reset", () => {
  test("resets to initial state", async () => {
    (brandsV2Api.mine as jest.Mock).mockResolvedValue({
      data: { brands: mockBrands },
    });
    await useBusinessStore.getState().fetchBrands();

    useBusinessStore.getState().reset();

    const state = useBusinessStore.getState();
    expect(state.brands).toEqual([]);
    expect(state.activeBrand).toBeNull();
    expect(state.isLoading).toBe(true);
  });
});

describe("businessStore — helpers", () => {
  test("getActiveBrand returns current active", async () => {
    (brandsV2Api.mine as jest.Mock).mockResolvedValue({
      data: { brands: mockBrands },
    });
    await useBusinessStore.getState().fetchBrands();

    const brand = useBusinessStore.getState().getActiveBrand();
    expect(brand?.name).toBe("Restaurant A");
  });

  test("getBrands returns all brands", async () => {
    (brandsV2Api.mine as jest.Mock).mockResolvedValue({
      data: { brands: mockBrands },
    });
    await useBusinessStore.getState().fetchBrands();

    const brands = useBusinessStore.getState().getBrands();
    expect(brands).toHaveLength(2);
  });
});
