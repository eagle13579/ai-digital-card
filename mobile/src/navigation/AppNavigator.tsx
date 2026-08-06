import React from 'react';
import { Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useAuth } from '../hooks/useAuth';

import HomeScreen from '../screens/HomeScreen';
import CardDetailScreen from '../screens/CardDetailScreen';
import ProfileScreen from '../screens/ProfileScreen';
import SettingsScreen from '../screens/SettingsScreen';
import LoginScreen from '../screens/LoginScreen';
import LoadingSpinner from '../components/LoadingSpinner';

// ---------------------------------------------------------------------------
// Type definitions for navigation
// ---------------------------------------------------------------------------
export type RootStackParamList = {
  MainTabs: undefined;
  CardDetail: { cardId: string };
};

export type AuthStackParamList = {
  Login: undefined;
};

export type MainTabParamList = {
  Home: undefined;
  Profile: undefined;
  Settings: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

// ---------------------------------------------------------------------------
// Tab navigator (authenticated)
// ---------------------------------------------------------------------------
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#4a90d9',
        tabBarInactiveTintColor: '#999',
        tabBarStyle: { backgroundColor: '#fff', borderTopColor: '#eee' },
        headerStyle: { backgroundColor: '#fff' },
        headerTitleStyle: { color: '#1a1a1a', fontWeight: '600' },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          title: '名片夹',
          tabBarLabel: '首页',
          tabBarIcon: ({ color, size }) => (
            <TabIcon label="🏠" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          title: '个人中心',
          tabBarLabel: '我的',
          tabBarIcon: ({ color, size }) => (
            <TabIcon label="👤" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: '设置',
          tabBarLabel: '设置',
          tabBarIcon: ({ color, size }) => (
            <TabIcon label="⚙️" color={color} size={size} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

// Simple emoji-based tab icon (placeholder for react-native-vector-icons)
function TabIcon({ label, size }: { label: string; color: string; size: number }) {
  return <Text style={{ fontSize: size - 4 }}>{label}</Text>;
}

// ---------------------------------------------------------------------------
// Auth stack (unauthenticated)
// ---------------------------------------------------------------------------
function AuthNavigator() {
  return (
    <AuthStack.Navigator screenOptions={{ headerShown: false }}>
      <AuthStack.Screen name="Login" component={LoginScreen} />
    </AuthStack.Navigator>
  );
}

// ---------------------------------------------------------------------------
// Root navigator
// ---------------------------------------------------------------------------
const AppNavigator: React.FC = () => {
  const { isHydrated, token } = useAuth();

  if (!isHydrated) {
    return <LoadingSpinner message="加载中..." />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {token == null ? (
          <Stack.Screen name="MainTabs" component={AuthNavigator as any} />
        ) : (
          <>
            <Stack.Screen name="MainTabs" component={MainTabs} />
            <Stack.Screen
              name="CardDetail"
              component={CardDetailScreen}
              options={{
                headerShown: true,
                title: '名片详情',
                headerBackTitle: '返回',
              }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;
