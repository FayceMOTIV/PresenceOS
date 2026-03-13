// Global test setup for PresenceOS Mobile
jest.spyOn(console, "warn").mockImplementation(() => {});
jest.spyOn(console, "error").mockImplementation(() => {});

// Mock AsyncStorage (native module)
jest.mock("@react-native-async-storage/async-storage", () =>
  require("@react-native-async-storage/async-storage/jest/async-storage-mock")
);

// Mock Firebase (ESM modules incompatible with Jest)
jest.mock("firebase/app", () => ({
  initializeApp: jest.fn(() => ({ name: "[DEFAULT]" })),
  getApps: jest.fn(() => []),
  getApp: jest.fn(() => ({ name: "[DEFAULT]" })),
}));
jest.mock("@firebase/auth", () => ({
  initializeAuth: jest.fn(() => ({ currentUser: null })),
  getAuth: jest.fn(() => ({ currentUser: null })),
  getReactNativePersistence: jest.fn(() => ({})),
  signInWithEmailAndPassword: jest.fn(),
  createUserWithEmailAndPassword: jest.fn(),
  signInWithCredential: jest.fn(),
  signOut: jest.fn(),
  sendPasswordResetEmail: jest.fn(),
  updateProfile: jest.fn(),
  onAuthStateChanged: jest.fn(),
  GoogleAuthProvider: { credential: jest.fn() },
}));
// Also mock firebase/auth (some tests import from here instead of @firebase/auth)
jest.mock("firebase/auth", () => ({
  initializeAuth: jest.fn(() => ({ currentUser: null })),
  getAuth: jest.fn(() => ({ currentUser: null })),
  getReactNativePersistence: jest.fn(() => ({})),
  signInWithEmailAndPassword: jest.fn(),
  createUserWithEmailAndPassword: jest.fn(),
  signInWithCredential: jest.fn(),
  signOut: jest.fn(),
  sendPasswordResetEmail: jest.fn(),
  updateProfile: jest.fn(),
  onAuthStateChanged: jest.fn(),
  GoogleAuthProvider: { credential: jest.fn() },
}));
jest.mock("firebase/firestore", () => ({
  getFirestore: jest.fn(() => ({})),
  doc: jest.fn(),
  getDoc: jest.fn(),
  setDoc: jest.fn(),
  collection: jest.fn(),
}));
jest.mock("firebase/storage", () => ({
  getStorage: jest.fn(() => ({})),
  ref: jest.fn(),
  uploadBytes: jest.fn(),
  getDownloadURL: jest.fn(),
}));

// Mock expo-auth-session (causes _inherits error in Jest)
jest.mock("expo-auth-session/providers/google", () => ({
  useAuthRequest: jest.fn(() => [null, null, jest.fn()]),
  useIdTokenAuthRequest: jest.fn(() => [null, null, jest.fn()]),
}));
jest.mock("expo-auth-session", () => ({
  makeRedirectUri: jest.fn(() => "rs3://redirect"),
  ResponseType: { Token: "token" },
  AuthRequest: jest.fn(),
}));

// Mock expo-web-browser (maybeCompleteAuthSession called at module level)
jest.mock("expo-web-browser", () => ({
  openAuthSessionAsync: jest.fn().mockResolvedValue({ type: "success" }),
  openBrowserAsync: jest.fn().mockResolvedValue({ type: "success" }),
  maybeCompleteAuthSession: jest.fn(),
  dismissBrowser: jest.fn(),
}));

// Mock expo module that causes scope issues in Jest 30
jest.mock("expo-modules-core", () => ({
  EventEmitter: jest.fn(),
  NativeModule: jest.fn(),
  SharedObject: jest.fn(),
  SharedRef: jest.fn(),
  requireNativeModule: jest.fn(() => ({})),
  requireOptionalNativeModule: jest.fn(() => null),
}));
