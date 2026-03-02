const React = require("react");
const { View } = require("react-native");

const BottomSheetModal = React.forwardRef((props, ref) => {
  React.useImperativeHandle(ref, () => ({
    present: jest.fn(),
    dismiss: jest.fn(),
    close: jest.fn(),
  }));
  return React.createElement(View, { testID: "bottom-sheet" }, props.children);
});
BottomSheetModal.displayName = "BottomSheetModal";

module.exports = {
  BottomSheetModal,
  BottomSheetModalProvider: ({ children }) => React.createElement(View, null, children),
  BottomSheetBackdrop: (props) => React.createElement(View, props),
  BottomSheetView: (props) => React.createElement(View, props, props.children),
  BottomSheetFlatList: (props) => React.createElement(View, props),
};
