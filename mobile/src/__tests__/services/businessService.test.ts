/**
 * Tests du businessService
 */

import {
  getMyBusinesses,
  createBusiness,
  updateBusiness,
  subscribeToMyBusinesses,
} from "@/services/businessService";

// Mock Firestore
const mockGetDocs = jest.fn();
const mockSetDoc = jest.fn();
const mockUpdateDoc = jest.fn();
const mockOnSnapshot = jest.fn();
const mockDoc = jest.fn();
const mockCollection = jest.fn();
const mockQuery = jest.fn();
const mockWhere = jest.fn();

jest.mock("firebase/firestore", () => ({
  collection: (...args: any[]) => mockCollection(...args),
  query: (...args: any[]) => mockQuery(...args),
  where: (...args: any[]) => mockWhere(...args),
  getDocs: (...args: any[]) => mockGetDocs(...args),
  onSnapshot: (...args: any[]) => mockOnSnapshot(...args),
  doc: (...args: any[]) => mockDoc(...args),
  setDoc: (...args: any[]) => mockSetDoc(...args),
  updateDoc: (...args: any[]) => mockUpdateDoc(...args),
}));

jest.mock("@/lib/firebase", () => ({
  db: { type: "mock-db" },
}));

beforeEach(() => {
  jest.clearAllMocks();
  mockQuery.mockReturnValue("mock-query");
  mockDoc.mockReturnValue("mock-doc-ref");
  mockCollection.mockReturnValue("mock-collection");
  mockWhere.mockReturnValue("mock-where");
});

describe("getMyBusinesses", () => {
  test("retourne les businesses de l'utilisateur", async () => {
    mockGetDocs.mockResolvedValue({
      docs: [
        { id: "biz-1", data: () => ({ name: "Restaurant A", slug: "a", businessType: "restaurant", ownerId: "u1", memberIds: ["u1"], isActive: true }) },
        { id: "biz-2", data: () => ({ name: "Restaurant B", slug: "b", businessType: "restaurant", ownerId: "u1", memberIds: ["u1"], isActive: true }) },
      ],
    });
    const result = await getMyBusinesses("u1");
    expect(result.length).toBe(2);
    expect(result[0].id).toBe("biz-1");
    expect(result[0].name).toBe("Restaurant A");
    expect(result[1].id).toBe("biz-2");
    expect(mockCollection).toHaveBeenCalled();
    expect(mockWhere).toHaveBeenCalledWith("memberIds", "array-contains", "u1");
  });
});

describe("subscribeToMyBusinesses", () => {
  test("appelle onSnapshot avec le bon callback", () => {
    const mockUnsub = jest.fn();
    mockOnSnapshot.mockReturnValue(mockUnsub);
    const callback = jest.fn();
    const unsub = subscribeToMyBusinesses("u1", callback);
    expect(mockOnSnapshot).toHaveBeenCalled();
    expect(unsub).toBe(mockUnsub);
  });
});

describe("createBusiness", () => {
  test("appelle setDoc avec les bonnes données", async () => {
    mockSetDoc.mockResolvedValue(undefined);
    await createBusiness({
      id: "biz-new",
      name: "New Place",
      slug: "new-place",
      businessType: "restaurant",
      ownerId: "u1",
      memberIds: ["u1"],
      isActive: true,
    });
    expect(mockDoc).toHaveBeenCalled();
    expect(mockSetDoc).toHaveBeenCalledWith("mock-doc-ref", expect.objectContaining({
      name: "New Place",
      slug: "new-place",
      businessType: "restaurant",
    }));
  });
});

describe("updateBusiness", () => {
  test("appelle updateDoc avec les bons params", async () => {
    mockUpdateDoc.mockResolvedValue(undefined);
    await updateBusiness("biz-1", { name: "Updated" });
    expect(mockDoc).toHaveBeenCalled();
    expect(mockUpdateDoc).toHaveBeenCalledWith("mock-doc-ref", { name: "Updated" });
  });
});
