const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

const config = getDefaultConfig(__dirname);

// Inject URL polyfill before all other modules
// This fixes Hermes "Cannot assign to property 'protocol'" error
const originalGetModulesRunBeforeMainModule =
  config.serializer?.getModulesRunBeforeMainModule;

config.serializer = {
  ...config.serializer,
  getModulesRunBeforeMainModule() {
    const original = originalGetModulesRunBeforeMainModule
      ? originalGetModulesRunBeforeMainModule()
      : [];
    return [
      path.resolve(__dirname, "node_modules/react-native-url-polyfill/auto.js"),
      ...original,
    ];
  },
};

module.exports = config;
