/**
 * AI数字名片 — 移动端应用入口
 * React Navigation (Stack + Bottom Tabs) + React Native Paper + Theme Provider
 *
 * Tab 导航结构:
 *  1. 首页 (Home) — 动态流 / 控制台
 *  2. 名片 (Card) — 我的电子名片
 *  3. 匹配 (Match) — 发现 / 人脉匹配
 *  4. 设置 (Settings) — 账户 / 外观 / 隐私
 */

import React from 'react';
import { StatusBar, Platform, Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PaperProvider } from 'react-native-paper';
import { ThemeProvider, useTheme } from './src/theme/theme-context';

// Screens (Tab)
import HomeScreen from './src/screens/HomeScreen';
import CardScreen from './src/screens/CardScreen';
import MatchScreen from './src/screens/MatchScreen';
import SettingsScreen from './src/screens/SettingsScreen';

// Screens (Stack / Detail)
import CardDetailScreen from './src/screens/CardDetailScreen';
import EditCardScreen from './src/screens/EditCardScreen';
import MatchDetailScreen from './src/screens/MatchDetailScreen';

// ── Navigators ──────────────────────────────────────────────────────────────

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function TabIcon({ routeName, focused }: { routeName: string; focused: boolean; color: string }) {
  const iconMap: Record<string, string> = {
    Home: focused ? '🏠' : '🏡',
    Card: focused ? '💳' : '🪪',
    Match: focused ? '🤝' : '👋',
    Settings: focused ? '⚙️' : '🔧',
  };
  return <Text style={{ fontSize: 22 }}>{iconMap[routeName] || '📄'}</Text>;
}

function MainTabs() {
  const { colors, isDark } = useTheme();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused, color }) => (
          <TabIcon routeName={route.name} focused={focused} color={color} />
        ),
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textTertiary,
        tabBarStyle: {
          backgroundColor: colors.tabBarBg,
          borderTopColor: colors.tabBarBorder,
          borderTopWidth: 0.5,
          elevation: 0,
          shadowOpacity: 0,
          height: Platform.OS === 'ios' ? 88 : 64,
          paddingBottom: Platform.OS === 'ios' ? 28 : 8,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600' as const,
          letterSpacing: 0.2,
          marginTop: 2,
        },
        tabBarItemStyle: {
          paddingVertical: 4,
        },
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarLabel: '首页',
          tabBarIcon: ({ focused, color }) => <TabIcon routeName="Home" focused={focused} color={color} />,
        }}
      />
      <Tab.Screen
        name="Card"
        component={CardScreen}
        options={{
          tabBarLabel: '名片',
          tabBarIcon: ({ focused, color }) => <TabIcon routeName="Card" focused={focused} color={color} />,
        }}
      />
      <Tab.Screen
        name="Match"
        component={MatchScreen}
        options={{
          tabBarLabel: '匹配',
          tabBarIcon: ({ focused, color }) => <TabIcon routeName="Match" focused={focused} color={color} />,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarLabel: '设置',
          tabBarIcon: ({ focused, color }) => <TabIcon routeName="Settings" focused={focused} color={color} />,
        }}
      />
    </Tab.Navigator>
  );
}

// ── Root Stack Navigator ─────────────────────────────────────────────────────

function AppContent() {
  const { paperTheme, isDark } = useTheme();

  return (
    <PaperProvider theme={paperTheme}>
      <StatusBar
        barStyle={isDark ? 'light-content' : 'dark-content'}
        backgroundColor="transparent"
        translucent
      />
      <NavigationContainer
        theme={{
          dark: isDark,
          colors: {
            primary: paperTheme.colors.primary,
            background: paperTheme.colors.background,
            card: paperTheme.colors.surface,
            text: paperTheme.colors.onBackground,
            border: paperTheme.colors.outline,
            notification: paperTheme.colors.error,
          },
          fonts: {
            regular: { fontFamily: 'System', fontWeight: '400' },
            medium: { fontFamily: 'System', fontWeight: '500' },
            bold: { fontFamily: 'System', fontWeight: '700' },
            heavy: { fontFamily: 'System', fontWeight: '800' },
          },
        }}
      >
        <Stack.Navigator
          screenOptions={{
            headerShown: false,
            animation: 'slide_from_right',
          }}
        >
          <Stack.Screen name="MainTabs" component={MainTabs} />
          <Stack.Screen name="CardDetail" component={CardDetailScreen} />
          <Stack.Screen name="EditCard" component={EditCardScreen} />
          <Stack.Screen name="MatchDetail" component={MatchDetailScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </PaperProvider>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AppContent />
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
