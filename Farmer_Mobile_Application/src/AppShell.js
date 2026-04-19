import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView, Dimensions } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { theme } from './styles';

// Screens
import OnboardingScreen from './screens/OnboardingScreen';
import { LoginScreen } from './screens/LoginScreen';
import HomeScreen from './screens/HomeScreen';
import MarketplaceScreen from './screens/MarketplaceScreen';
import CreateListingScreen from './screens/CreateListingScreen';
import OrderDetailsScreen from './screens/OrderDetailsScreen';
import MakeOfferScreen from './screens/MakeOfferScreen';
import ConfirmationScreen from './screens/ConfirmationScreen';
import WalletScreen from './screens/WalletScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs({ route }) {
  const { role = 'buyer' } = route.params || {};

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: role === 'farmer' ? theme.colors.green : theme.colors.sky,
        tabBarInactiveTintColor: '#999',
      }}
    >
      {role === 'farmer' ? (
        <Tab.Screen
            name="FarmerDash"
            component={HomeScreen}
            options={{
                tabBarLabel: 'HOME',
                tabBarIcon: ({ color }) => <Text style={{ fontSize: 20, color }}>📍</Text>,
            }}
        />
      ) : (
        <Tab.Screen
            name="Marketplace"
            component={MarketplaceScreen}
            options={{
                tabBarLabel: 'MARKET',
                tabBarIcon: ({ color }) => <Text style={{ fontSize: 20, color }}>📍</Text>,
            }}
        />
      )}

      <Tab.Screen
        name="Orders"
        component={WalletScreen}
        options={{
            tabBarLabel: 'ORDERS',
            tabBarIcon: ({ color }) => <Text style={{ fontSize: 20, color }}>🛒</Text>,
        }}
      />

      {role === 'farmer' && (
        <Tab.Screen
            name="AddListing"
            component={CreateListingScreen}
            options={{
                tabBarLabel: 'ADD',
                tabBarIcon: ({ color }) => <View style={styles.addBtn}><Text style={styles.addBtnText}>+</Text></View>,
            }}
        />
      )}

      <Tab.Screen
        name="Ledger"
        component={HomeScreen}
        options={{
            tabBarLabel: 'LEDGER',
            tabBarIcon: ({ color }) => <Text style={{ fontSize: 20, color }}>📊</Text>,
        }}
      />

      <Tab.Screen
        name="Profile"
        component={HomeScreen}
        options={{
            tabBarLabel: 'PROFILE',
            tabBarIcon: ({ color }) => <Text style={{ fontSize: 20, color }}>👤</Text>,
        }}
      />
    </Tab.Navigator>
  );
}

export default function AppShell() {
  const [isSplashing, setIsSplashing] = useState(true);
  const [onboarded, setOnboarded] = useState(false);
  const [role, setRole] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [session, setSession] = useState(null);

  React.useEffect(() => {
    // Splash for 2 seconds
    const timer = setTimeout(() => {
        setIsSplashing(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleOnboardingComplete = (selectedRole) => {
    setRole(selectedRole);
    setOnboarded(true);
  };

  const handleAuth = (authData) => {
    setSession(authData);
    setAuthenticated(true);
  };

  if (isSplashing) {
    return (
      <View style={styles.splash}>
         <Text style={styles.splashLogo}>🚜</Text>
         <Text style={styles.splashBrand}>AGRI-TELECOM</Text>
         <Text style={styles.splashMarket}>MARKETPLACE</Text>
         <View style={styles.pulseContainer}>
            <Text style={styles.dotPulse}>...</Text>
         </View>
         <View style={styles.onboardBox}>
            <Text style={styles.onboardText}>Connecting Zimbabwean Farmers to Markets</Text>
         </View>
      </View>
    );
  }

  if (!onboarded) {
    return <OnboardingScreen onComplete={handleOnboardingComplete} />;
  }

  if (!authenticated) {
    return <LoginScreen role={role} onAuthenticated={handleAuth} />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Main" component={MainTabs} initialParams={{ role, profile: session?.profile }} />
        <Stack.Screen name="OrderDetails" component={OrderDetailsScreen} />
        <Stack.Screen name="MakeOffer" component={MakeOfferScreen} />
        <Stack.Screen name="ConfirmDelivery" component={ConfirmationScreen} />
        <Stack.Screen name="Wallet" component={WalletScreen} />
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
  addBtn: {
    width: 60,
    height: 60,
    backgroundColor: theme.colors.green,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    bottom: 15,
    elevation: 8,
    shadowColor: theme.colors.green,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
  },
  addBtnText: { color: '#FFF', fontSize: 32, fontWeight: '800' },
  splash: { flex: 1, backgroundColor: theme.colors.green, justifyContent: 'center', alignItems: 'center' },
  splashLogo: { fontSize: 80, marginBottom: 20 },
  splashBrand: { fontSize: 32, fontWeight: '900', color: '#FFF', letterSpacing: 2 },
  splashMarket: { fontSize: 24, fontWeight: '500', color: theme.colors.gold },
  onboardBox: { position: 'absolute', bottom: 80, paddingHorizontal: 40, alignItems: 'center' },
  onboardText: { color: '#FFF', fontSize: 18, textAlign: 'center', marginBottom: 40, lineHeight: 28 },
  startBtn: { backgroundColor: theme.colors.gold, paddingVertical: 20, paddingHorizontal: 60, borderRadius: 20 },
  startBtnText: { color: theme.colors.black, fontWeight: '800', fontSize: 16 }
});
