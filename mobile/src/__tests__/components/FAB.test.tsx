/**
 * Tests du FAB (Floating Action Button)
 */

import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import FAB from "@/components/FAB";

jest.mock("expo-linear-gradient", () => {
  const { View } = require("react-native");
  return { LinearGradient: (props: any) => <View {...props} /> };
});

jest.mock("@expo/vector-icons", () => {
  const { Text } = require("react-native");
  return { Ionicons: ({ name }: any) => <Text>{name}</Text> };
});

describe("FAB", () => {
  test("rend sans crash", () => {
    const onPress = jest.fn();
    const { root } = render(<FAB icon="add" onPress={onPress} />);
    expect(root).toBeTruthy();
  });

  test("appelle onPress au press", () => {
    const onPress = jest.fn();
    const { root } = render(<FAB icon="add" onPress={onPress} />);
    fireEvent.press(root);
    expect(onPress).toHaveBeenCalled();
  });

  test("affiche l'icône", () => {
    const onPress = jest.fn();
    const { getByText } = render(<FAB icon="camera" onPress={onPress} />);
    expect(getByText("camera")).toBeTruthy();
  });

  test("accepte un style custom", () => {
    const onPress = jest.fn();
    const { root } = render(<FAB icon="add" onPress={onPress} style={{ bottom: 100 }} />);
    expect(root).toBeTruthy();
  });
});
