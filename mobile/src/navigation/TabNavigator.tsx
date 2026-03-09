// PresenceOS Mobile — Bottom Tab Navigator (Light theme, French)

import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";

// ── Screens ──
import HomeScreen from "@/screens/home/HomeScreen";
import FileHubScreen from "@/screens/files/FileHubScreen";
import AssetUploadScreen from "@/screens/files/AssetUploadScreen";
import DishFormScreen from "@/screens/files/DishFormScreen";
import ScanMenuScreen from "@/screens/files/ScanMenuScreen";
import ProposalDetailScreen from "@/screens/proposals/ProposalDetailScreen";
import BriefDuJourScreen from "@/screens/brief/BriefDuJourScreen";
import InboxScreen from "@/screens/inbox/InboxScreen";
import CMChatScreen from "@/screens/cm/CMChatScreen";
import IlyasChatScreen from "@/screens/chat/IlyasChatScreen";
import SocialAccountsScreen from "@/screens/social/SocialAccountsScreen";
import ConnectSocialsScreen from "@/screens/social/ConnectSocialsScreen";
import VideoStudioScreen from "@/screens/video/VideoStudioScreen";
import VideoPlansScreen from "@/screens/video/VideoPlansScreen";
import AIVideoScreen from "@/screens/video/AIVideoScreen";
import BreakoutScreen from "@/screens/breakout/BreakoutScreen";
import ValidationInboxScreen from "@/screens/validation/ValidationInboxScreen";
import BrainDashboardScreen from "@/screens/brain/BrainDashboardScreen";
import AnalyticsScreen from "@/screens/analytics/AnalyticsScreen";
import SettingsScreen from "@/screens/settings/SettingsScreen";
import PublishScreen from "@/screens/social/PublishScreen";

// ── Types ──
export type HomeStackParams = {
  HomeMain: undefined;
  Brief: undefined;
  SocialAccounts: undefined;
  ConnectSocials: undefined;
  Publish: undefined;
  BrainDashboard: undefined;
  Analytics: undefined;
  ValidationInbox: undefined;
  Settings: undefined;
};

export type FilesStackParams = {
  FileHub: undefined;
  AssetUpload: undefined;
  DishForm: { dishId?: string };
  ScanMenu: undefined;
};

export type IlyasStackParams = {
  IlyasChat: undefined;
  ProposalDetail: { proposalId: string };
};

export type InboxStackParams = {
  InboxMain: undefined;
  CMChat: undefined;
};

export type VideoStackParams = {
  VideoStudio: undefined;
  VideoPlans: undefined;
  AIVideo: undefined;
};

export type BreakoutStackParams = {
  BreakoutMain: undefined;
};

const Tab = createBottomTabNavigator();

// ── Home Stack ──
const HomeStackNav = createNativeStackNavigator<HomeStackParams>();
function HomeStackScreen() {
  return (
    <HomeStackNav.Navigator screenOptions={{ headerShown: false, headerBackVisible: false }}>
      <HomeStackNav.Screen name="HomeMain" component={HomeScreen} />
      <HomeStackNav.Screen
        name="Brief"
        component={BriefDuJourScreen}
        options={{ presentation: "modal" }}
      />
      <HomeStackNav.Screen
        name="SocialAccounts"
        component={SocialAccountsScreen}
        options={{ presentation: "modal" }}
      />
      <HomeStackNav.Screen
        name="ConnectSocials"
        component={ConnectSocialsScreen}
        options={{ presentation: "modal" }}
      />
      <HomeStackNav.Screen
        name="Publish"
        component={PublishScreen}
        options={{ presentation: "modal" }}
      />
      <HomeStackNav.Screen
        name="BrainDashboard"
        component={BrainDashboardScreen}
        options={{ presentation: "modal" }}
      />
      <HomeStackNav.Screen
        name="Analytics"
        component={AnalyticsScreen}
        options={{ presentation: "modal" }}
      />
      <HomeStackNav.Screen
        name="ValidationInbox"
        component={ValidationInboxScreen}
        options={{ presentation: "modal" }}
      />
      <HomeStackNav.Screen
        name="Settings"
        component={SettingsScreen}
        options={{ presentation: "modal" }}
      />
    </HomeStackNav.Navigator>
  );
}

// ── Files Stack ──
const FilesStackNav = createNativeStackNavigator<FilesStackParams>();
function FilesStackScreen() {
  return (
    <FilesStackNav.Navigator screenOptions={{ headerShown: false, headerBackVisible: false }}>
      <FilesStackNav.Screen name="FileHub" component={FileHubScreen} />
      <FilesStackNav.Screen
        name="AssetUpload"
        component={AssetUploadScreen}
        options={{ presentation: "modal" }}
      />
      <FilesStackNav.Screen
        name="DishForm"
        component={DishFormScreen}
        options={{ presentation: "modal" }}
      />
      <FilesStackNav.Screen
        name="ScanMenu"
        component={ScanMenuScreen}
        options={{ presentation: "modal" }}
      />
    </FilesStackNav.Navigator>
  );
}

// ── Ilyas Stack ──
const IlyasStackNav = createNativeStackNavigator<IlyasStackParams>();
function IlyasStackScreen() {
  return (
    <IlyasStackNav.Navigator screenOptions={{ headerShown: false, headerBackVisible: false }}>
      <IlyasStackNav.Screen name="IlyasChat" component={IlyasChatScreen} />
      <IlyasStackNav.Screen name="ProposalDetail" component={ProposalDetailScreen} />
    </IlyasStackNav.Navigator>
  );
}

// ── Inbox Stack ──
const InboxStackNav = createNativeStackNavigator<InboxStackParams>();
function InboxStackScreen() {
  return (
    <InboxStackNav.Navigator screenOptions={{ headerShown: false, headerBackVisible: false }}>
      <InboxStackNav.Screen name="InboxMain" component={InboxScreen} />
      <InboxStackNav.Screen name="CMChat" component={CMChatScreen} />
    </InboxStackNav.Navigator>
  );
}

// ── Video Stack ──
const VideoStackNav = createNativeStackNavigator<VideoStackParams>();
function VideoStackScreen() {
  return (
    <VideoStackNav.Navigator screenOptions={{ headerShown: false, headerBackVisible: false }}>
      <VideoStackNav.Screen name="VideoStudio" component={VideoStudioScreen} />
      <VideoStackNav.Screen
        name="VideoPlans"
        component={VideoPlansScreen}
        options={{ presentation: "modal" }}
      />
      <VideoStackNav.Screen name="AIVideo" component={AIVideoScreen} />
    </VideoStackNav.Navigator>
  );
}

// ── Breakout Stack ──
const BreakoutStackNav = createNativeStackNavigator<BreakoutStackParams>();
function BreakoutStackScreen() {
  return (
    <BreakoutStackNav.Navigator screenOptions={{ headerShown: false, headerBackVisible: false }}>
      <BreakoutStackNav.Screen name="BreakoutMain" component={BreakoutScreen} />
    </BreakoutStackNav.Navigator>
  );
}

// ── Tab Navigator ──
export default function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: Colors.brand.primary,
        tabBarInactiveTintColor: Colors.text.muted,
        tabBarStyle: {
          backgroundColor: "#FFFFFF",
          borderTopColor: Colors.border.default,
          borderTopWidth: 1,
          height: 85,
          paddingBottom: 28,
          paddingTop: 8,
          shadowColor: "#000",
          shadowOpacity: 0.05,
          shadowRadius: 3,
          elevation: 2,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: "600",
          marginTop: 2,
        },
        tabBarIcon: ({ color, size }) => {
          const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
            Home: "home",
            Files: "folder",
            Ilyas: "chatbubble-ellipses",
            Video: "videocam",
            Breakout: "layers",
            Inbox: "chatbubbles",
          };
          return (
            <Ionicons
              name={icons[route.name] || "ellipse"}
              size={size}
              color={color}
            />
          );
        },
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeStackScreen}
        options={{ tabBarLabel: FR.tab_home }}
      />
      <Tab.Screen
        name="Files"
        component={FilesStackScreen}
        options={{ tabBarLabel: FR.tab_files }}
      />
      <Tab.Screen
        name="Ilyas"
        component={IlyasStackScreen}
        options={{ tabBarLabel: FR.tab_ilyas }}
      />
      <Tab.Screen
        name="Video"
        component={VideoStackScreen}
        options={{ tabBarLabel: "Vidéo" }}
      />
      <Tab.Screen
        name="Breakout"
        component={BreakoutStackScreen}
        options={{ tabBarLabel: "Breakout" }}
      />
      <Tab.Screen
        name="Inbox"
        component={InboxStackScreen}
        options={{ tabBarLabel: FR.tab_inbox }}
      />
    </Tab.Navigator>
  );
}
