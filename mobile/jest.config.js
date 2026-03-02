module.exports = {
  preset: "jest-expo",
  setupFiles: ["<rootDir>/jest.setup.js"],
  transformIgnorePatterns: [
    "node_modules/(?!(jest-)?react-native|@react-native(-community)?|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|native-base|react-native-svg|zustand|expo-modules-core|expo-secure-store|expo-constants|expo-linear-gradient|expo-notifications|expo-linking|expo-web-browser|expo-camera|expo-image-picker|expo-av|expo-file-system|expo-status-bar|expo-font|expo-asset|expo-keep-awake|expo-device|firebase)",
  ],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/__tests__/**",
  ],
  testMatch: ["<rootDir>/src/__tests__/**/*.test.(ts|tsx)"],
};
