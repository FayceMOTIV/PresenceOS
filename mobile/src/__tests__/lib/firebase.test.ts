/**
 * Tests du firebase.ts init
 */

const mockInitializeApp = jest.fn().mockReturnValue({ name: "test-app" });
const mockGetApps = jest.fn().mockReturnValue([]);
const mockGetApp = jest.fn().mockReturnValue({ name: "test-app" });
const mockInitializeAuth = jest.fn().mockReturnValue({ currentUser: null });
const mockGetReactNativePersistence = jest.fn().mockReturnValue("rn-persistence");
const mockGetFirestore = jest.fn().mockReturnValue({ type: "firestore" });
const mockGetStorage = jest.fn().mockReturnValue({ type: "storage" });

jest.mock("firebase/app", () => ({
  initializeApp: (...args: any[]) => mockInitializeApp(...args),
  getApps: () => mockGetApps(),
  getApp: () => mockGetApp(),
}));

jest.mock("@firebase/auth", () => ({
  initializeAuth: (...args: any[]) => mockInitializeAuth(...args),
  getAuth: jest.fn(),
  getReactNativePersistence: (...args: any[]) => mockGetReactNativePersistence(...args),
}));

jest.mock("firebase/firestore", () => ({
  getFirestore: (...args: any[]) => mockGetFirestore(...args),
}));

jest.mock("firebase/storage", () => ({
  getStorage: (...args: any[]) => mockGetStorage(...args),
}));

jest.mock("@react-native-async-storage/async-storage", () => ({
  default: { getItem: jest.fn(), setItem: jest.fn() },
}));

describe("firebase.ts", () => {
  test("initialise une nouvelle app quand aucune n'existe", () => {
    // Module-level code already ran during import via jest.mock
    // Reimport to trigger module evaluation
    jest.isolateModules(() => {
      mockGetApps.mockReturnValue([]);
      require("@/lib/firebase");
      expect(mockInitializeApp).toHaveBeenCalled();
    });
  });

  test("réutilise l'app existante si déjà initialisée", () => {
    jest.isolateModules(() => {
      mockGetApps.mockReturnValue([{ name: "existing" }]);
      require("@/lib/firebase");
      expect(mockGetApp).toHaveBeenCalled();
    });
  });

  test("initialise auth avec AsyncStorage persistence", () => {
    jest.isolateModules(() => {
      mockGetApps.mockReturnValue([]);
      require("@/lib/firebase");
      expect(mockInitializeAuth).toHaveBeenCalled();
      expect(mockGetReactNativePersistence).toHaveBeenCalled();
    });
  });

  test("initialise firestore et storage", () => {
    jest.isolateModules(() => {
      mockGetApps.mockReturnValue([]);
      require("@/lib/firebase");
      expect(mockGetFirestore).toHaveBeenCalled();
      expect(mockGetStorage).toHaveBeenCalled();
    });
  });

  test("exporte app, auth, db, storage", () => {
    jest.isolateModules(() => {
      mockGetApps.mockReturnValue([]);
      const firebase = require("@/lib/firebase");
      expect(firebase.app).toBeDefined();
      expect(firebase.auth).toBeDefined();
      expect(firebase.db).toBeDefined();
      expect(firebase.storage).toBeDefined();
    });
  });
});
