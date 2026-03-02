/**
 * Tests du composant KBCompletenessBar
 */

import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react-native";
import KBCompletenessBar from "@/components/KBCompletenessBar";

// Use fake timers to avoid Animated.spring act() warnings
beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  act(() => {
    jest.runOnlyPendingTimers();
  });
  jest.useRealTimers();
});

describe("KBCompletenessBar", () => {
  test("affiche le score en pourcentage", () => {
    render(<KBCompletenessBar score={72} />);
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("72%")).toBeTruthy();
  });

  test("niveau 0-10: affiche le message débutant", () => {
    render(<KBCompletenessBar score={5} />);
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText(/L'IA ne vous connaît pas encore/)).toBeTruthy();
    expect(screen.getByText("Commencer →")).toBeTruthy();
  });

  test("niveau 10-35: affiche le message apprentissage", () => {
    render(<KBCompletenessBar score={25} />);
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText(/L'IA apprend/)).toBeTruthy();
  });

  test("niveau 35-65: affiche le message intermédiaire", () => {
    render(<KBCompletenessBar score={50} />);
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText(/L'IA maîtrise les bases/)).toBeTruthy();
  });

  test("niveau 65-85: affiche le message avancé", () => {
    render(<KBCompletenessBar score={75} />);
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText(/L'IA connaît bien/)).toBeTruthy();
  });

  test("niveau 85+: affiche le message expert sans CTA", () => {
    render(<KBCompletenessBar score={95} />);
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText(/L'IA est experte/)).toBeTruthy();
    expect(screen.queryByText(/→/)).toBeNull();
  });

  test("gère le onPress", () => {
    const onPress = jest.fn();
    render(<KBCompletenessBar score={50} onPress={onPress} />);
    act(() => { jest.advanceTimersByTime(500); });
    fireEvent.press(screen.getByText("50%"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  test("score 0 est géré", () => {
    render(<KBCompletenessBar score={0} />);
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("0%")).toBeTruthy();
  });

  test("score 100 est géré", () => {
    render(<KBCompletenessBar score={100} />);
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("100%")).toBeTruthy();
  });
});
