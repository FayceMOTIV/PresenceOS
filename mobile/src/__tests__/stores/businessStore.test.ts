/**
 * Tests du businessStore
 */

import { useBusinessStore } from "@/stores/businessStore";
import * as businessService from "@/services/businessService";

jest.mock("@/services/businessService", () => ({
  subscribeToMyBusinesses: jest.fn(),
}));

jest.mock("@/lib/firebase", () => ({
  db: {},
  auth: {},
  storage: {},
}));

const mockUnsubscribe = jest.fn();
let capturedCallback: ((businesses: any[]) => void) | null = null;

beforeEach(() => {
  jest.clearAllMocks();
  capturedCallback = null;
  (businessService.subscribeToMyBusinesses as jest.Mock).mockImplementation(
    (_uid: string, callback: (businesses: any[]) => void) => {
      capturedCallback = callback;
      return mockUnsubscribe;
    }
  );
  // Reset store
  useBusinessStore.getState().reset();
});

const mockBusinesses = [
  {
    id: "biz-1",
    name: "Le Family's",
    slug: "familys",
    businessType: "restaurant",
    ownerId: "user-1",
    memberIds: ["user-1"],
    isActive: true,
  },
  {
    id: "biz-2",
    name: "Pizza Roma",
    slug: "pizza-roma",
    businessType: "restaurant",
    ownerId: "user-1",
    memberIds: ["user-1"],
    isActive: true,
  },
];

describe("businessStore — Initial state", () => {
  test("état initial correct", () => {
    const state = useBusinessStore.getState();
    expect(state.businesses).toEqual([]);
    expect(state.activeBusiness).toBeNull();
    expect(state.isLoading).toBe(true);
    expect(state.brands).toEqual([]);
    expect(state.activeBrand).toBeNull();
  });
});

describe("businessStore — startListening", () => {
  test("appelle subscribeToMyBusinesses", () => {
    useBusinessStore.getState().startListening("user-1");
    expect(businessService.subscribeToMyBusinesses).toHaveBeenCalledWith("user-1", expect.any(Function));
  });

  test("met à jour le state quand callback reçoit des businesses", async () => {
    useBusinessStore.getState().startListening("user-1");
    expect(capturedCallback).not.toBeNull();
    capturedCallback!(mockBusinesses);
    // Wait for async SecureStore operations
    await new Promise((r) => setTimeout(r, 50));
    const state = useBusinessStore.getState();
    expect(state.businesses.length).toBe(2);
    expect(state.activeBusiness?.id).toBe("biz-1");
    expect(state.isLoading).toBe(false);
    expect(state.brands.length).toBe(2);
    expect(state.activeBrand?.id).toBe("biz-1");
    expect(state.activeBrand?.name).toBe("Le Family's");
  });
});

describe("businessStore — switchBusiness", () => {
  test("change la business active", async () => {
    useBusinessStore.getState().startListening("user-1");
    capturedCallback!(mockBusinesses);
    await new Promise((r) => setTimeout(r, 50));
    useBusinessStore.getState().switchBusiness("biz-2");
    const state = useBusinessStore.getState();
    expect(state.activeBusiness?.id).toBe("biz-2");
    expect(state.activeBrand?.name).toBe("Pizza Roma");
  });

  test("ne change rien si bizId invalide", async () => {
    useBusinessStore.getState().startListening("user-1");
    capturedCallback!(mockBusinesses);
    await new Promise((r) => setTimeout(r, 50));
    useBusinessStore.getState().switchBusiness("invalid");
    expect(useBusinessStore.getState().activeBusiness?.id).toBe("biz-1");
  });
});

describe("businessStore — getters", () => {
  test("getActiveBrand retourne le brand actif", async () => {
    useBusinessStore.getState().startListening("user-1");
    capturedCallback!(mockBusinesses);
    await new Promise((r) => setTimeout(r, 50));
    const brand = useBusinessStore.getState().getActiveBrand();
    expect(brand?.id).toBe("biz-1");
    expect(brand?.brand_type).toBe("restaurant");
  });

  test("getBrands retourne tous les brands", async () => {
    useBusinessStore.getState().startListening("user-1");
    capturedCallback!(mockBusinesses);
    await new Promise((r) => setTimeout(r, 50));
    const brands = useBusinessStore.getState().getBrands();
    expect(brands.length).toBe(2);
  });
});

describe("businessStore — stopListening & reset", () => {
  test("stopListening appelle unsubscribe", () => {
    useBusinessStore.getState().startListening("user-1");
    useBusinessStore.getState().stopListening();
    expect(mockUnsubscribe).toHaveBeenCalled();
  });

  test("reset remet tout à zéro", async () => {
    useBusinessStore.getState().startListening("user-1");
    capturedCallback!(mockBusinesses);
    await new Promise((r) => setTimeout(r, 50));
    useBusinessStore.getState().reset();
    const state = useBusinessStore.getState();
    expect(state.businesses).toEqual([]);
    expect(state.activeBusiness).toBeNull();
    expect(state.isLoading).toBe(true);
  });
});
