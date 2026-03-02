/**
 * Tests des écrans d'onboarding
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react-native";
import WelcomeScreen from "@/screens/onboarding/WelcomeScreen";
import ConnectAccountScreen from "@/screens/onboarding/ConnectAccountScreen";
import CompleteScreen from "@/screens/onboarding/CompleteScreen";
import RestaurantInfoScreen from "@/screens/onboarding/RestaurantInfoScreen";
import FirstMessageScreen from "@/screens/onboarding/FirstMessageScreen";

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

// ── WelcomeScreen ──
describe("WelcomeScreen", () => {
  test("affiche le titre 'Bienvenue sur PresenceOS'", () => {
    render(<WelcomeScreen onNext={jest.fn()} />);
    expect(screen.getByText("Bienvenue sur PresenceOS")).toBeTruthy();
  });

  test("affiche les 3 features", () => {
    render(<WelcomeScreen onNext={jest.fn()} />);
    expect(screen.getByText(/Posts IA personnalises/)).toBeTruthy();
    expect(screen.getByText(/Analysez vos photos/)).toBeTruthy();
    expect(screen.getByText(/Publiez sur Instagram/)).toBeTruthy();
  });

  test("bouton Commencer appelle onNext", () => {
    const onNext = jest.fn();
    render(<WelcomeScreen onNext={onNext} />);
    fireEvent.press(screen.getByText("Commencer"));
    expect(onNext).toHaveBeenCalled();
  });
});

// ── ConnectAccountScreen ──
describe("ConnectAccountScreen", () => {
  test("affiche le titre et sous-titre", () => {
    render(<ConnectAccountScreen onNext={jest.fn()} />);
    expect(screen.getByText("Connectez vos reseaux")).toBeTruthy();
    expect(screen.getByText("Etape 1/4")).toBeTruthy();
  });

  test("affiche les 3 plateformes", () => {
    render(<ConnectAccountScreen onNext={jest.fn()} />);
    expect(screen.getByText("Instagram")).toBeTruthy();
    expect(screen.getByText("Facebook")).toBeTruthy();
    expect(screen.getByText("TikTok")).toBeTruthy();
  });

  test("bouton Continuer appelle onNext", () => {
    const onNext = jest.fn();
    render(<ConnectAccountScreen onNext={onNext} />);
    fireEvent.press(screen.getByText("Continuer"));
    expect(onNext).toHaveBeenCalled();
  });

  test("Passer cette etape appelle onNext", () => {
    const onNext = jest.fn();
    render(<ConnectAccountScreen onNext={onNext} />);
    fireEvent.press(screen.getByText("Passer cette etape"));
    expect(onNext).toHaveBeenCalled();
  });
});

// ── RestaurantInfoScreen ──
describe("RestaurantInfoScreen", () => {
  test("affiche le formulaire", () => {
    render(<RestaurantInfoScreen onNext={jest.fn()} />);
    expect(screen.getByText("Parlez-moi de votre restaurant")).toBeTruthy();
    expect(screen.getByText("Etape 2/4")).toBeTruthy();
    expect(screen.getByText("Nom du restaurant")).toBeTruthy();
    expect(screen.getByText("Type de cuisine")).toBeTruthy();
    expect(screen.getByText("Ton de communication")).toBeTruthy();
  });

  test("affiche les chips de cuisine", () => {
    render(<RestaurantInfoScreen onNext={jest.fn()} />);
    expect(screen.getByText("Francais")).toBeTruthy();
    expect(screen.getByText("Italien")).toBeTruthy();
    expect(screen.getByText("Marocain")).toBeTruthy();
  });

  test("affiche les chips de ton", () => {
    render(<RestaurantInfoScreen onNext={jest.fn()} />);
    expect(screen.getByText("Chaleureux")).toBeTruthy();
    expect(screen.getByText("Pro & elegant")).toBeTruthy();
    expect(screen.getByText("Fun & decale")).toBeTruthy();
  });

  test("Continuer appelle onNext avec les infos", () => {
    const onNext = jest.fn();
    render(<RestaurantInfoScreen onNext={onNext} />);
    fireEvent.changeText(screen.getByPlaceholderText("Ex : Le Family's"), "Mon Restaurant");
    fireEvent.press(screen.getByText("Marocain"));
    fireEvent.press(screen.getByText("Chaleureux"));
    fireEvent.press(screen.getByText("Continuer"));
    expect(onNext).toHaveBeenCalledWith({
      name: "Mon Restaurant",
      cuisine: "Marocain",
      tone: "Chaleureux",
    });
  });
});

// ── CompleteScreen ──
describe("CompleteScreen", () => {
  test("affiche 'C'est parti !'", () => {
    render(<CompleteScreen onFinish={jest.fn()} />);
    expect(screen.getByText("C'est parti !")).toBeTruthy();
  });

  test("affiche les instructions recap", () => {
    render(<CompleteScreen onFinish={jest.fn()} />);
    expect(screen.getByText(/Parlez a Ilyas/)).toBeTruthy();
    expect(screen.getByText(/Uploadez des photos/)).toBeTruthy();
    expect(screen.getByText(/Validez les posts IA/)).toBeTruthy();
  });

  test("bouton Commencer appelle onFinish", () => {
    const onFinish = jest.fn();
    render(<CompleteScreen onFinish={onFinish} />);
    fireEvent.press(screen.getByText("Commencer"));
    expect(onFinish).toHaveBeenCalled();
  });
});

// ── FirstMessageScreen ──
describe("FirstMessageScreen", () => {
  test("affiche le titre et les quick chips", () => {
    render(<FirstMessageScreen onNext={jest.fn()} />);
    expect(screen.getByText("Dites bonjour a Ilyas")).toBeTruthy();
    expect(screen.getByText("Etape 3/4")).toBeTruthy();
    expect(screen.getByText("Cree un post pour ce weekend")).toBeTruthy();
    expect(screen.getByText("Idee de Reel pour mon restaurant")).toBeTruthy();
  });

  test("quick chip remplit le champ", () => {
    render(<FirstMessageScreen onNext={jest.fn()} />);
    fireEvent.press(screen.getByText("Cree un post pour ce weekend"));
    const input = screen.getByPlaceholderText("Ecrivez a Ilyas...");
    expect(input.props.value).toBe("Cree un post pour ce weekend");
  });

  test("envoyer un message affiche la réponse après timeout", async () => {
    render(<FirstMessageScreen onNext={jest.fn()} />);
    fireEvent.changeText(screen.getByPlaceholderText("Ecrivez a Ilyas..."), "Hello");
    fireEvent.press(screen.getByText("send"));
    // User message shown
    expect(screen.getByText("Hello")).toBeTruthy();
    expect(screen.getByText("Ilyas reflechit...")).toBeTruthy();
    // Advance timer for response
    act(() => {
      jest.advanceTimersByTime(1600);
    });
    await waitFor(() => {
      expect(screen.getByText(/Super ! Je suis ravi/)).toBeTruthy();
      expect(screen.getByText("Continuer")).toBeTruthy();
    });
  });

  test("Continuer appelle onNext après réponse", async () => {
    const onNext = jest.fn();
    render(<FirstMessageScreen onNext={onNext} />);
    fireEvent.changeText(screen.getByPlaceholderText("Ecrivez a Ilyas..."), "Bonjour");
    fireEvent.press(screen.getByText("send"));
    act(() => {
      jest.advanceTimersByTime(1600);
    });
    await waitFor(() => {
      expect(screen.getByText("Continuer")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Continuer"));
    expect(onNext).toHaveBeenCalled();
  });
});
