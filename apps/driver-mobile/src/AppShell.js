import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Platform, TouchableOpacity, Image } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MapPin, Truck, DollarSign, User } from 'lucide-react-native';
import { theme } from './styles';
import { saveSession, getSession, clearSession } from './utils/auth';
import { setupNotificationHandler, registerForPushNotifications } from './utils/notifications';

// Screens
import LoginScreen from './screens/LoginScreen';
import RegistrationScreen from './screens/RegistrationScreen';
import JobsScreen from './screens/JobsScreen';
import DeliveriesScreen from './screens/DeliveriesScreen';
import EarningsScreen from './screens/EarningsScreen';
import ProfileScreen from './screens/ProfileScreen';
import JobDetailsScreen from './screens/JobDetailsScreen';
import DeliveryTrackingScreen from './screens/DeliveryTrackingScreen';

let Stack = null;
if (Platform.OS !== 'web') {
  const { createStackNavigator } = require('@react-navigation/stack');
  Stack = createStackNavigator();
}
const Tab = createBottomTabNavigator();

// Simple web-only tab bar for fallback
function WebTabBar({ activeTab, onChangeTab, token, profile, onLogout }) {
  const tabs = [
    { key: 'Jobs', icon: MapPin, label: 'Jobs' },
    { key: 'Deliveries', icon: Truck, label: 'Deliveries' },
    { key: 'Earnings', icon: DollarSign, label: 'Earnings' },
    { key: 'Profile', icon: User, label: 'Profile' },
  ];

  const screens = {
    Jobs: <JobsScreen route={{ params: { token, profile } }} navigation={{ navigate: () => {} }} />,
    Deliveries: <DeliveriesScreen route={{ params: { token } }} navigation={{ navigate: () => {} }} />,
    Earnings: <EarningsScreen route={{ params: { token } }} />,
    Profile: <ProfileScreen route={{ params: { token, profile, onLogout } }} />,
  };

  return (
    <View style={{ flex: 1 }}>
      <View style={{ flex: 1 }}>{screens[activeTab]}</View>
      <View style={styles.webTabBar}>
        {tabs.map(t => {
          const Icon = t.icon;
          const active = activeTab === t.key;
          return (
            <TouchableOpacity key={t.key} style={styles.webTab} onPress={() => onChangeTab(t.key)}>
              <Icon size={22} color={active ? theme.colors.sky : '#999'} />
              <Text style={[styles.webTabLabel, active && { color: theme.colors.sky }]}>{t.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

function DriverTabs({ route }) {
  const { token, profile = {}, onLogout } = route.params || {};

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: theme.colors.sky,
        tabBarInactiveTintColor: '#999',
        tabBarLabelStyle: { fontSize: 11, fontWeight: '700', marginTop: -4 },
      }}
    >
      <Tab.Screen
        name="Jobs"
        component={JobsScreen}
        initialParams={{ token, profile }}
        options={{
          tabBarLabel: 'Jobs',
          tabBarIcon: ({ color, size }) => <MapPin size={size || 22} color={color} />,
        }}
      />
      <Tab.Screen
        name="Deliveries"
        component={DeliveriesScreen}
        initialParams={{ token }}
        options={{
          tabBarLabel: 'Deliveries',
          tabBarIcon: ({ color, size }) => <Truck size={size || 22} color={color} />,
        }}
      />
      <Tab.Screen
        name="Earnings"
        component={EarningsScreen}
        initialParams={{ token }}
        options={{
          tabBarLabel: 'Earnings',
          tabBarIcon: ({ color, size }) => <DollarSign size={size || 22} color={color} />,
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        initialParams={{ token, profile, onLogout }}
        options={{
          tabBarLabel: 'Profile',
          tabBarIcon: ({ color, size }) => <User size={size || 22} color={color} />,
        }}
      />
    </Tab.Navigator>
  );
}

export default function AppShell() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSplashing, setIsSplashing] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [session, setSession] = useState(null);
  const [webTab, setWebTab] = useState('Jobs');
  const [showRegister, setShowRegister] = useState(false);
  const [pendingApproval, setPendingApproval] = useState(false);

  // Restore session on mount
  useEffect(() => {
    setupNotificationHandler();
    (async () => {
      try {
        const savedSession = await getSession();
        if (savedSession?.access_token) {
          setSession(savedSession);
          setAuthenticated(true);
        }
      } catch (e) {
        console.warn('Session restore failed:', e);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  // Splash timer
  useEffect(() => {
    const timer = setTimeout(() => setIsSplashing(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleAuth = useCallback(async (authData) => {
    setSession(authData);
    setAuthenticated(true);
    await saveSession(authData.access_token, authData.profile || authData.user, authData.refresh_token);
    registerForPushNotifications().catch(() => {});
  }, []);

  const handleLogout = useCallback(async () => {
    await clearSession();
    setSession(null);
    setAuthenticated(false);
  }, []);

  if (isLoading || isSplashing) {
    return (
      <View style={styles.splash}>
        <View style={styles.splashLogoContainer}>
          <Image source={require('../assets/logo.png')} style={{ width: 100, height: 100, resizeMode: 'contain' }} />
        </View>
        <Text style={styles.splashBrand}>ZIMAGRITRUST</Text>
        <Text style={styles.splashMarket}>DRIVER PORTAL</Text>
        <ActivityIndicator size="large" color="rgba(255,255,255,0.7)" style={{ marginTop: 32 }} />
        <View style={styles.onboardBox}>
          <Text style={styles.onboardText}>Professional Logistics Solutions</Text>
        </View>
      </View>
    );
  }

  if (!authenticated) {
    if (pendingApproval) {
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32, backgroundColor: '#f8f9fa' }}>
          <Text style={{ fontSize: 48, marginBottom: 16 }}>⏳</Text>
          <Text style={{ fontSize: 20, fontWeight: '700', color: '#1a1a1a', marginBottom: 8, textAlign: 'center' }}>Application Submitted</Text>
          <Text style={{ fontSize: 14, color: '#666', textAlign: 'center', lineHeight: 22 }}>
            Your driver application is under review. An admin will verify your documents within 24–48 hours.{`\n\n`}You will be notified via SMS and WhatsApp once approved.
          </Text>
          <TouchableOpacity
            style={{ marginTop: 24, paddingVertical: 12, paddingHorizontal: 32, backgroundColor: '#0ea5e9', borderRadius: 10 }}
            onPress={() => setPendingApproval(false)}>
            <Text style={{ color: '#fff', fontWeight: '700' }}>Back to Login</Text>
          </TouchableOpacity>
        </View>
      );
    }
    if (showRegister) {
      return (
        <RegistrationScreen
          onRegistered={(data) => {
            setShowRegister(false);
            if (data?.status === 'PENDING_APPROVAL') { setPendingApproval(true); return; }
            handleAuth(data);
          }}
          onBack={() => setShowRegister(false)}
        />
      );
    }
    return (
      <LoginScreen
        onAuthenticated={handleAuth}
        onRegister={() => setShowRegister(true)}
      />
    );
  }

  // Web: simple tab rendering without Stack navigator
  if (Platform.OS === 'web') {
    return (
      <WebTabBar
        activeTab={webTab}
        onChangeTab={setWebTab}
        token={session?.access_token}
        profile={session?.profile}
        onLogout={handleLogout}
      />
    );
  }

  // Native: full navigation stack
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen
          name="Main"
          component={DriverTabs}
          initialParams={{
            token: session?.access_token,
            profile: session?.profile,
            onLogout: handleLogout,
          }}
        />
        <Stack.Screen name="JobDetails" component={JobDetailsScreen} />
        <Stack.Screen name="DeliveryTracking" component={DeliveryTrackingScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    height: 80,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#EEEEEE',
    paddingBottom: 25,
    paddingTop: 10,
    position: 'absolute',
    bottom: 25,
    left: 20,
    right: 20,
    borderRadius: 25,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
  },
  splash: { flex: 1, backgroundColor: theme.colors.sky, justifyContent: 'center', alignItems: 'center' },
  splashLogoContainer: { width: 140, height: 140, borderRadius: 70, backgroundColor: 'rgba(255,255,255,0.15)', justifyContent: 'center', alignItems: 'center', marginBottom: 24, borderWidth: 2, borderColor: 'rgba(255,255,255,0.3)' },
  splashLogo: { fontSize: 52 },
  splashBrand: { fontSize: 28, fontWeight: '800', color: '#FFF', letterSpacing: 3, textTransform: 'uppercase' },
  splashMarket: { fontSize: 18, fontWeight: '600', color: theme.colors.gold, letterSpacing: 2, textTransform: 'uppercase', marginTop: 8 },
  onboardBox: { position: 'absolute', bottom: 100, paddingHorizontal: 40, alignItems: 'center' },
  onboardText: { color: '#FFF', fontSize: 16, textAlign: 'center', marginBottom: 40, lineHeight: 24, fontWeight: '500', letterSpacing: 0.5 },
  webTabBar: { flexDirection: 'row', backgroundColor: '#FFF', borderTopWidth: 1, borderTopColor: '#EEE', paddingVertical: 10, paddingBottom: 20 },
  webTab: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 4 },
  webTabLabel: { fontSize: 11, fontWeight: '700', color: '#999' },
});
