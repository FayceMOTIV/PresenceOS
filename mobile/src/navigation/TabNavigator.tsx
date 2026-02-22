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
import ProposalsListScreen from "@/screens/proposals/ProposalsListScreen";
import ProposalDetailScreen from "@/screens/proposals/ProposalDetailScreen";
import BriefDuJourScreen from "@/screens/brief/BriefDuJourScreen";
import InboxScreen from "@/screens/inbox/InboxScreen";
import SocialAccountsScreen from "@/screens/social/SocialAccountsScreen";
import VideoStudioScreen from "@/screens/video/VideoStudioScreen";
import VideoPlansScreen from "@/screens/video/VideoPlansScreen";

// ── Types ──
export type HomeStackParams = {
  HomeMain: undefined;
  Brief: undefined;
  SocialAccounts: undefined;
};

export type FilesStackParams = {
  FileHub: undefined;
  AssetUpload: undefined;
  DishForm: { dishId?: string };
  ScanMenu: undefined;
};

export type ProposalsStackParams = {
  ProposalsList: undefined;
  ProposalDetail: { proposalId: string };
};

export type InboxStackParams = {
  InboxMain: undefined;
};

export type VideoStackParams = {
  VideoStudio: undefined;
  VideoPlans: undefined;
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

// ── Proposals Stack ──
const ProposalsStackNav = createNativeStackNavigator<ProposalsStackParams>();
function ProposalsStackScreen() {
  return (
    <ProposalsStackNav.Navigator screenOptions={{ headerShown: false, headerBackVisible: false }}>
      <ProposalsStackNav.Screen name="ProposalsList" component={ProposalsListScreen} />
      <ProposalsStackNav.Screen name="ProposalDetail" component={ProposalDetailScreen} />
    </ProposalsStackNav.Navigator>
  );
}

// ── Inbox Stack ──
const InboxStackNav = createNativeStackNavigator<InboxStackParams>();
function InboxStackScreen() {
  return (
    <InboxStackNav.Navigator screenOptions={{ headerShown: false, headerBackVisible: false }}>
      <InboxStackNav.Screen name="InboxMain" component={InboxScreen} />
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
    </VideoStackNav.Navigator>
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
            Proposals: "sparkles",
            Video: "videocam",
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
        name="Proposals"
        component={ProposalsStackScreen}
        options={{ tabBarLabel: FR.tab_proposals }}
      />
      <Tab.Screen
        name="Video"
        component={VideoStackScreen}
        options={{ tabBarLabel: "Vidéo" }}
      />
      <Tab.Screen
        name="Inbox"
        component={InboxStackScreen}
        options={{ tabBarLabel: FR.tab_inbox }}
      />
    </Tab.Navigator>
  );
}
