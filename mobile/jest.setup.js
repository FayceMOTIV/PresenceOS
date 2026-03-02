// Global test setup for PresenceOS Mobile
jest.spyOn(console, "warn").mockImplementation(() => {});

// Mock expo module that causes scope issues in Jest 30
jest.mock("expo-modules-core", () => ({
  EventEmitter: jest.fn(),
  NativeModule: jest.fn(),
  SharedObject: jest.fn(),
  SharedRef: jest.fn(),
  requireNativeModule: jest.fn(() => ({})),
  requireOptionalNativeModule: jest.fn(() => null),
}));
