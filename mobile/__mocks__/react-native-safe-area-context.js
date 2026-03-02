const React = require("react");
const { View } = require("react-native");

module.exports = {
  SafeAreaView: (props) => React.createElement(View, props, props.children),
  SafeAreaProvider: (props) => React.createElement(View, props, props.children),
  useSafeAreaInsets: jest.fn(() => ({ top: 0, bottom: 0, left: 0, right: 0 })),
};
