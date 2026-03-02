const React = require("react");
const { View } = require("react-native");

module.exports = {
  Video: React.forwardRef((props, ref) =>
    React.createElement(View, { testID: "expo-av-video", ...props })
  ),
  ResizeMode: {
    CONTAIN: "contain",
    COVER: "cover",
    STRETCH: "stretch",
  },
  Audio: {
    setAudioModeAsync: jest.fn(),
  },
};
