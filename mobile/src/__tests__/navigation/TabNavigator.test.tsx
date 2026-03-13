/**
 * Tests du TabNavigator
 *
 * The TabNavigator imports dozens of screens and React Navigation primitives.
 * We mock all screen components and navigation libs so the test only
 * verifies that the tabs and stacks are wired up correctly.
 *
 * Key constraint: jest.mock() factories cannot close over out-of-scope
 * variables unless those variables are prefixed with "mock" (case-insensitive).
 */

jest.setTimeout(60000);

// ── Tracking arrays (prefixed "mock" → allowed in jest.mock factories) ───────
const mockRegisteredTabs: Array<{ name: string; component: any; options?: any }> = [];
const mockRegisteredScreens: Array<{ name: string; options?: any }> = [];

// ── Mock every screen imported by TabNavigator ──────────────────────────────
jest.mock("@/screens/home/HomeScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "HomeScreen" });
});
jest.mock("@/screens/files/FileHubScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "FileHubScreen" });
});
jest.mock("@/screens/files/AssetUploadScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "AssetUploadScreen" });
});
jest.mock("@/screens/files/DishFormScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "DishFormScreen" });
});
jest.mock("@/screens/files/ScanMenuScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "ScanMenuScreen" });
});
jest.mock("@/screens/proposals/ProposalDetailScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "ProposalDetailScreen" });
});
jest.mock("@/screens/brief/BriefDuJourScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "BriefDuJourScreen" });
});
jest.mock("@/screens/inbox/InboxScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "InboxScreen" });
});
jest.mock("@/screens/cm/CMChatScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "CMChatScreen" });
});
jest.mock("@/screens/chat/IlyasChatScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "IlyasChatScreen" });
});
jest.mock("@/screens/social/SocialAccountsScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "SocialAccountsScreen" });
});
jest.mock("@/screens/social/ConnectSocialsScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "ConnectSocialsScreen" });
});
jest.mock("@/screens/video/VideoStudioScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "VideoStudioScreen" });
});
jest.mock("@/screens/video/VideoPlansScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "VideoPlansScreen" });
});
jest.mock("@/screens/video/AIVideoScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "AIVideoScreen" });
});
jest.mock("@/screens/video/VideoTemplatesScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "VideoTemplatesScreen" });
});
jest.mock("@/screens/breakout/BreakoutScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "BreakoutScreen" });
});
jest.mock("@/screens/validation/ValidationInboxScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "ValidationInboxScreen" });
});
jest.mock("@/screens/brain/BrainDashboardScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "BrainDashboardScreen" });
});
jest.mock("@/screens/analytics/AnalyticsScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "AnalyticsScreen" });
});
jest.mock("@/screens/settings/SettingsScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "SettingsScreen" });
});
jest.mock("@/screens/social/PublishScreen", () => {
  const { View } = require("react-native");
  return () => require("react").createElement(View, { testID: "PublishScreen" });
});

// ── Mock @react-navigation/bottom-tabs ──────────────────────────────────────
// The Tab.Navigator collects all <Tab.Screen> children, records them in
// mockRegisteredTabs, and ALSO renders each component so the stack navigators
// inside each component get a chance to mount and populate mockRegisteredScreens.
jest.mock("@react-navigation/bottom-tabs", () => {
  const React = require("react");
  const { View } = require("react-native");

  const Tab = {
    Navigator: ({ children, screenOptions }: any) => {
      const tabChildren: any[] = [];
      React.Children.forEach(children, (child: any) => {
        if (child && child.props) {
          mockRegisteredTabs.push({
            name: child.props.name,
            component: child.props.component,
            options: child.props.options,
          });
          tabChildren.push(child);
        }
      });
      // Render each tab's component so nested stack navigators also run
      const renderedStacks = mockRegisteredTabs.map((tab) => {
        if (tab.component) {
          return React.createElement(tab.component, {
            key: tab.name,
            navigation: {},
            route: {},
          });
        }
        return null;
      });
      return React.createElement(
        View,
        { testID: "tab-navigator" },
        ...renderedStacks
      );
    },
    Screen: (_props: any) => null,
  };

  return { createBottomTabNavigator: () => Tab };
});

// ── Mock @react-navigation/native-stack ──────────────────────────────────────
jest.mock("@react-navigation/native-stack", () => {
  const React = require("react");
  const { View } = require("react-native");

  const Stack = {
    Navigator: ({ children }: any) => {
      React.Children.forEach(children, (child: any) => {
        if (child && child.props) {
          mockRegisteredScreens.push({
            name: child.props.name,
            options: child.props.options,
          });
        }
      });
      return React.createElement(View, { testID: "stack-navigator" }, null);
    },
    Screen: (_props: any) => null,
  };

  return { createNativeStackNavigator: () => Stack };
});

// ── Import AFTER mocks are set up ────────────────────────────────────────────
import React from "react";
import { render, screen } from "@testing-library/react-native";
import TabNavigator from "@/navigation/TabNavigator";

// ── Reset tracking arrays between tests ──────────────────────────────────────
beforeEach(() => {
  mockRegisteredTabs.length = 0;
  mockRegisteredScreens.length = 0;
});

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

describe("TabNavigator — Structure de base", () => {
  test("rend sans crash", () => {
    const { toJSON } = render(<TabNavigator />);
    expect(toJSON()).toBeTruthy();
  });

  test("rend le composant tab-navigator", () => {
    render(<TabNavigator />);
    expect(screen.getByTestId("tab-navigator")).toBeTruthy();
  });
});

describe("TabNavigator — 6 onglets enregistrés", () => {
  test("enregistre l'onglet Home", () => {
    render(<TabNavigator />);
    expect(mockRegisteredTabs.find((t) => t.name === "Home")).toBeDefined();
  });

  test("enregistre l'onglet Files", () => {
    render(<TabNavigator />);
    expect(mockRegisteredTabs.find((t) => t.name === "Files")).toBeDefined();
  });

  test("enregistre l'onglet Ilyas", () => {
    render(<TabNavigator />);
    expect(mockRegisteredTabs.find((t) => t.name === "Ilyas")).toBeDefined();
  });

  test("enregistre l'onglet Video", () => {
    render(<TabNavigator />);
    expect(mockRegisteredTabs.find((t) => t.name === "Video")).toBeDefined();
  });

  test("enregistre l'onglet Breakout", () => {
    render(<TabNavigator />);
    expect(mockRegisteredTabs.find((t) => t.name === "Breakout")).toBeDefined();
  });

  test("enregistre l'onglet Inbox", () => {
    render(<TabNavigator />);
    expect(mockRegisteredTabs.find((t) => t.name === "Inbox")).toBeDefined();
  });

  test("enregistre exactement 6 onglets", () => {
    render(<TabNavigator />);
    expect(mockRegisteredTabs).toHaveLength(6);
  });
});

describe("TabNavigator — Labels des onglets", () => {
  test("Home a le label 'Accueil'", () => {
    render(<TabNavigator />);
    const tab = mockRegisteredTabs.find((t) => t.name === "Home");
    expect(tab?.options?.tabBarLabel).toBe("Accueil");
  });

  test("Files a le label 'Médiathèque'", () => {
    render(<TabNavigator />);
    const tab = mockRegisteredTabs.find((t) => t.name === "Files");
    expect(tab?.options?.tabBarLabel).toBe("Médiathèque");
  });

  test("Ilyas a le label 'Ilyas'", () => {
    render(<TabNavigator />);
    const tab = mockRegisteredTabs.find((t) => t.name === "Ilyas");
    expect(tab?.options?.tabBarLabel).toBe("Ilyas");
  });

  test("Video a le label 'Vidéo'", () => {
    render(<TabNavigator />);
    const tab = mockRegisteredTabs.find((t) => t.name === "Video");
    expect(tab?.options?.tabBarLabel).toBe("Vidéo");
  });

  test("Breakout a le label 'Breakout'", () => {
    render(<TabNavigator />);
    const tab = mockRegisteredTabs.find((t) => t.name === "Breakout");
    expect(tab?.options?.tabBarLabel).toBe("Breakout");
  });

  test("Inbox a le label 'Avis'", () => {
    render(<TabNavigator />);
    const tab = mockRegisteredTabs.find((t) => t.name === "Inbox");
    expect(tab?.options?.tabBarLabel).toBe("Avis");
  });
});

describe("TabNavigator — HomeStack sub-screens", () => {
  test("enregistre HomeMain", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "HomeMain")
    ).toBeDefined();
  });

  test("enregistre Brief avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "Brief");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });

  test("enregistre SocialAccounts avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "SocialAccounts");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });

  test("enregistre ConnectSocials", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "ConnectSocials")
    ).toBeDefined();
  });

  test("enregistre Publish avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "Publish");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });

  test("enregistre BrainDashboard avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "BrainDashboard");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });

  test("enregistre Analytics avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "Analytics");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });

  test("enregistre ValidationInbox avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "ValidationInbox");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });

  test("enregistre Settings avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "Settings");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });
});

describe("TabNavigator — FilesStack sub-screens", () => {
  test("enregistre FileHub", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "FileHub")
    ).toBeDefined();
  });

  test("enregistre AssetUpload avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "AssetUpload");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });

  test("enregistre DishForm avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "DishForm");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });

  test("enregistre ScanMenu avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "ScanMenu");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });
});

describe("TabNavigator — IlyasStack sub-screens", () => {
  test("enregistre IlyasChat", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "IlyasChat")
    ).toBeDefined();
  });

  test("enregistre ProposalDetail", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "ProposalDetail")
    ).toBeDefined();
  });
});

describe("TabNavigator — InboxStack sub-screens", () => {
  test("enregistre InboxMain", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "InboxMain")
    ).toBeDefined();
  });

  test("enregistre CMChat", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "CMChat")
    ).toBeDefined();
  });
});

describe("TabNavigator — VideoStack sub-screens", () => {
  test("enregistre VideoStudio", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "VideoStudio")
    ).toBeDefined();
  });

  test("enregistre VideoPlans avec presentation modal", () => {
    render(<TabNavigator />);
    const s = mockRegisteredScreens.find((s) => s.name === "VideoPlans");
    expect(s).toBeDefined();
    expect(s?.options?.presentation).toBe("modal");
  });

  test("enregistre AIVideo", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "AIVideo")
    ).toBeDefined();
  });

  test("enregistre VideoTemplates", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "VideoTemplates")
    ).toBeDefined();
  });
});

describe("TabNavigator — BreakoutStack sub-screens", () => {
  test("enregistre BreakoutMain", () => {
    render(<TabNavigator />);
    expect(
      mockRegisteredScreens.find((s) => s.name === "BreakoutMain")
    ).toBeDefined();
  });
});
