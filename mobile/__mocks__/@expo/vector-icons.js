const React = require("react");
const { Text } = require("react-native");

const Icon = (props) => React.createElement(Text, { testID: `icon-${props.name}` }, props.name);

module.exports = {
  Ionicons: Icon,
  MaterialCommunityIcons: Icon,
  FontAwesome: Icon,
  Feather: Icon,
};
