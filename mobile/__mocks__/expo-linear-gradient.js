const React = require("react");
const { View } = require("react-native");

function LinearGradient(props) {
  return React.createElement(View, { testID: "linear-gradient", ...props }, props.children);
}
module.exports = { LinearGradient };
