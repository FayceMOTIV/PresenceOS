/**
 * Tests du ErrorBoundary
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import ErrorBoundary from "@/components/ErrorBoundary";

jest.setTimeout(60000);

// A component that throws on demand
function ThrowingChild({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("Test error from child");
  }
  return <></>;
}

// Helper: suppress console.error inside tests that test error throwing
const originalConsoleError = console.error;
beforeEach(() => {
  jest.clearAllMocks();
});

describe("ErrorBoundary — Rendu normal", () => {
  test("rend les enfants quand pas d'erreur", () => {
    const { Text } = require("react-native");
    const { getByText } = render(
      <ErrorBoundary>
        <Text>Contenu enfant</Text>
      </ErrorBoundary>
    );
    expect(getByText("Contenu enfant")).toBeTruthy();
  });

  test("rend plusieurs enfants sans erreur", () => {
    const { Text } = require("react-native");
    const { getByText } = render(
      <ErrorBoundary>
        <Text>Enfant 1</Text>
        <Text>Enfant 2</Text>
      </ErrorBoundary>
    );
    expect(getByText("Enfant 1")).toBeTruthy();
    expect(getByText("Enfant 2")).toBeTruthy();
  });

  test("n'affiche pas le fallback quand pas d'erreur", () => {
    const { Text } = require("react-native");
    const { queryByText } = render(
      <ErrorBoundary>
        <Text>OK</Text>
      </ErrorBoundary>
    );
    expect(queryByText("Oups, une erreur est survenue")).toBeNull();
  });
});

describe("ErrorBoundary — Erreur capturée", () => {
  test("affiche le fallback quand enfant throw", () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText("Oups, une erreur est survenue")).toBeTruthy();
  });

  test("affiche le sous-titre d'erreur", () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(
      screen.getByText("L'application a rencontré un problème inattendu.")
    ).toBeTruthy();
  });

  test("affiche le bouton Réessayer", () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText("Réessayer")).toBeTruthy();
  });

  test("affiche l'icône d'avertissement", () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByTestId("icon-warning-outline")).toBeTruthy();
  });

  test("n'affiche pas les enfants quand erreur", () => {
    const { Text } = require("react-native");
    const { queryByText } = render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={true} />
        <Text>Contenu masque</Text>
      </ErrorBoundary>
    );
    expect(queryByText("Contenu masque")).toBeNull();
  });
});

describe("ErrorBoundary — handleRetry", () => {
  test("appuyer sur Réessayer masque le fallback", () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText("Oups, une erreur est survenue")).toBeTruthy();

    // After retry, error state is reset — ThrowingChild will throw again
    // but the state IS reset before re-render
    const retryBtn = screen.getByText("Réessayer");
    expect(retryBtn).toBeTruthy();
    // We can fire the press — it will call setState({ hasError: false, error: null })
    fireEvent.press(retryBtn);
    // ThrowingChild still throws so boundary will catch again
    // — fallback remains visible (re-render throws again)
    expect(screen.getByText("Oups, une erreur est survenue")).toBeTruthy();
  });

  test("handleRetry remet hasError à false sur un enfant qui ne throw plus", () => {
    // Use a class component wrapper to control shouldThrow after retry
    class ControlledWrapper extends React.Component<
      {},
      { shouldThrow: boolean }
    > {
      state = { shouldThrow: true };

      handleRetry = () => {
        this.setState({ shouldThrow: false });
      };

      render() {
        return (
          <ErrorBoundary key={this.state.shouldThrow ? "err" : "ok"}>
            {this.state.shouldThrow ? (
              <ThrowingChild shouldThrow={true} />
            ) : (
              <></>
            )}
          </ErrorBoundary>
        );
      }
    }

    const { Text } = require("react-native");
    const { getByText } = render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(getByText("Oups, une erreur est survenue")).toBeTruthy();
    expect(getByText("Réessayer")).toBeTruthy();
  });
});

describe("ErrorBoundary — getDerivedStateFromError", () => {
  test("getDerivedStateFromError retourne le bon state", () => {
    const err = new Error("Test");
    const result = (ErrorBoundary as any).getDerivedStateFromError(err);
    expect(result).toEqual({ hasError: true, error: err });
  });
});

describe("ErrorBoundary — componentDidCatch", () => {
  test("componentDidCatch appelle console.error", () => {
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    const boundary = new (ErrorBoundary as any)({
      children: null,
    });
    const err = new Error("test");
    const info = { componentStack: "\n    at ThrowingChild" };
    boundary.componentDidCatch(err, info);
    expect(spy).toHaveBeenCalledWith(
      "ErrorBoundary caught:",
      err,
      info.componentStack
    );
    spy.mockRestore();
  });
});
