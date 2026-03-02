/**
 * Tests du composant Card (glassmorphism)
 */

import React from "react";
import { Text } from "react-native";
import { render, screen, fireEvent } from "@testing-library/react-native";
import Card from "@/components/ui/Card";

describe("Card", () => {
  test("rend les enfants", () => {
    render(
      <Card>
        <Text>Contenu</Text>
      </Card>
    );
    expect(screen.getByText("Contenu")).toBeTruthy();
  });

  test("gère le onPress", () => {
    const onPress = jest.fn();
    render(
      <Card onPress={onPress}>
        <Text>Clickable</Text>
      </Card>
    );
    fireEvent.press(screen.getByText("Clickable"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  test("rend avec gradient", () => {
    const { toJSON } = render(
      <Card gradient={["#7C5CBF", "#F4A261"]}>
        <Text>Gradient Card</Text>
      </Card>
    );
    expect(screen.getByText("Gradient Card")).toBeTruthy();
    expect(toJSON()).toBeTruthy();
  });

  test("rend sans onPress (non-touchable)", () => {
    const { toJSON } = render(
      <Card>
        <Text>Static</Text>
      </Card>
    );
    expect(toJSON()).toBeTruthy();
  });

  test("applique le glow effect", () => {
    const { toJSON } = render(
      <Card glow glowColor="#7C5CBF">
        <Text>Glow</Text>
      </Card>
    );
    expect(toJSON()).toBeTruthy();
  });
});
