/**
 * Tests du pushNotifications
 */

jest.mock("expo-notifications", () => ({
  getPermissionsAsync: jest.fn(),
  requestPermissionsAsync: jest.fn(),
  getExpoPushTokenAsync: jest.fn(),
  setNotificationChannelAsync: jest.fn(),
  addNotificationReceivedListener: jest.fn(),
  addNotificationResponseReceivedListener: jest.fn(),
  setNotificationHandler: jest.fn(),
  AndroidImportance: { HIGH: 4 },
}));

jest.mock("expo-device", () => ({
  isDevice: true,
}));

jest.mock("expo-constants", () => ({
  default: { expoConfig: { extra: {} } },
}));

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: { post: jest.fn() },
}));

import * as Notifications from "expo-notifications";
import api from "@/lib/api";
import {
  registerForPushNotifications,
  addNotificationListener,
  addNotificationResponseListener,
  removeNotificationSubscriptions,
} from "@/lib/pushNotifications";

beforeEach(() => {
  jest.clearAllMocks();
  (Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({ status: "granted" });
  (Notifications.getExpoPushTokenAsync as jest.Mock).mockResolvedValue({ data: "ExponentPushToken[xxx]" });
  (api.post as jest.Mock).mockResolvedValue({});
});

describe("registerForPushNotifications", () => {
  test("retourne le token si permissions accordées", async () => {
    const token = await registerForPushNotifications("b1");
    expect(token).toBe("ExponentPushToken[xxx]");
  });

  test("enregistre le token sur le backend", async () => {
    await registerForPushNotifications("b1");
    expect(api.post).toHaveBeenCalledWith("/brain/b1/push-token", {
      expo_push_token: "ExponentPushToken[xxx]",
    });
  });

  test("demande permissions si pas encore accordées", async () => {
    (Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({ status: "undetermined" });
    (Notifications.requestPermissionsAsync as jest.Mock).mockResolvedValue({ status: "granted" });
    const token = await registerForPushNotifications("b1");
    expect(Notifications.requestPermissionsAsync).toHaveBeenCalled();
    expect(token).toBe("ExponentPushToken[xxx]");
  });

  test("retourne null si permissions refusées", async () => {
    (Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({ status: "denied" });
    (Notifications.requestPermissionsAsync as jest.Mock).mockResolvedValue({ status: "denied" });
    const token = await registerForPushNotifications("b1");
    expect(token).toBeNull();
  });
});

describe("addNotificationListener", () => {
  test("appelle addNotificationReceivedListener", () => {
    const handler = jest.fn();
    addNotificationListener(handler);
    expect(Notifications.addNotificationReceivedListener).toHaveBeenCalledWith(handler);
  });
});

describe("addNotificationResponseListener", () => {
  test("appelle addNotificationResponseReceivedListener", () => {
    const handler = jest.fn();
    addNotificationResponseListener(handler);
    expect(Notifications.addNotificationResponseReceivedListener).toHaveBeenCalledWith(handler);
  });
});

describe("removeNotificationSubscriptions", () => {
  test("appelle remove sur chaque subscription", () => {
    const sub1 = { remove: jest.fn() } as any;
    const sub2 = { remove: jest.fn() } as any;
    removeNotificationSubscriptions(sub1, sub2);
    expect(sub1.remove).toHaveBeenCalled();
    expect(sub2.remove).toHaveBeenCalled();
  });
});
