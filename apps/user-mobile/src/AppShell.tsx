import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Image, Platform } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { 
  Home as IconHome, ShoppingBag as IconShoppingBag, Package as IconPackage, 
  Wallet as IconWallet, User as IconUser, ClipboardList as IconClipboardList,
  HandCoins as IconHandCoins
} from 'lucide-react-native';
import { theme } from './styles';
import { saveSession, getSession, clearSession, setOnboarded, hasOnboarded } from './utils/auth';
import { setupNotificationHandler, registerForPushNotifications } from './utils/notifications';

// Screens
import OnboardingScreen from './screens/OnboardingScreen';
import { LoginScreen } from './screens/LoginScreen';
import FarmerDashboardScreen from './screens/FarmerDashboardScreen';
import BuyerDashboardScreen from './screens/BuyerDashboardScreen';
import MarketplaceScreen from './screens/MarketplaceScreen';
import ListingDetailScreen from './screens/ListingDetailScreen';
import CreateListingScreen from './screens/CreateListingScreen';
import OrderDetailsScreen from './screens/OrderDetailsScreen';
import MakeOfferScreen from './screens/MakeOfferScreen';
import ConfirmationScreen from './screens/ConfirmationScreen';
import WalletScreen from './screens/WalletScreen';
import WalletScreen from './screens/WalletScreen';
import MyListingsScreen from './screens/MyListingsScreen';
import MyOrdersScreen from './screens/MyOrdersScreen';
import MyOrdersScreen from './screens/MyOrdersScreen';
import OffersReceivedScreen from './screens/OffersReceivedScreen';
import MyOffersScreen from './screens/MyOffersScreen';
import SavedListingsScreen from './screens/SavedListingsScreen';
import RateUserScreen from './screens/RateUserScreen';
import WithdrawScreen from './screens/WithdrawScreen';
import PaymentScreen from './screens/PaymentScreen';
import ProfileScreen from './screens/ProfileScreen';
import AgentApplicationScreen from './screens/AgentApplicationScreen';
import EditProfileScreen from './screens/EditProfileScreen';
import ChangePinScreen from './screens/ChangePinScreen';
import SettingsScreen from './screens/SettingsScreen';
import PrivacyScreen from './screens/PrivacyScreen';
import SupportScreen from './screens/SupportScreen';
import DisputesScreen from './screens/DisputesScreen';
import RaiseDisputeScreen from './screens/RaiseDisputeScreen';
import VerificationScreen from './screens/VerificationScreen';
import AgentVerificationScreen from './screens/AgentVerificationScreen';
import AnalyticsScreen from './screens/AnalyticsScreen';
import ChatScreen from './screens/ChatScreen';
import HomeScreen from './screens/HomeScreen';
import RiskScoreScreen from './screens/RiskScoreScreen';
import TransactionsScreen from './screens/TransactionsScreen';
import TransportNegotiationScreen from './screens/TransportNegotiationScreen';
import TransportSelectionScreen from './screens/TransportSelectionScreen';
import RegistrationScreen from './screens/RegistrationScreen';

let Stack = null;
if (Platform.OS !== 'web') {
  const { createStackNavigator } = require('@react-navigation/stack');
  Stack = createStackNavigator();
}
const Tab = createBottomTabNavigator();

// Web-only simple tab bar fallback
function WebTabBar({ activeTab, onChangeTab, role, token, profile, onLogout }) {
  const accent = role === 'farmer' ? theme.colors.green : theme.colors.sky;
  const webNavigation = {
    navigate: (screen) => onChangeTab(['Dashboard', 'Market', 'Listings', 'Offers', 'Orders', 'Profile'].includes(screen) ? screen : 'Profile'),
    goBack: () => onChangeTab('Dashboard'),
  };
  
  const tabs = [
    ...(role === 'farmer' 
      ? [
          { key: 'Dashboard', icon: IconHome, label: 'Dashboard' },
          { key: 'Market', icon: IconShoppingBag, label: 'Market' },
          { key: 'Listings', icon: IconClipboardList, label: 'Listings' },
        ] 
      : [
          { key: 'Dashboard', icon: IconHome, label: 'Dashboard' },
          { key: 'Market', icon: IconShoppingBag, label: 'Market' },
          { key: 'Offers', icon: IconHandCoins, label: 'Offers' },
        ]
    ),
    { key: 'Orders', icon: IconPackage, label: 'Orders' },
    { key: 'Profile', icon: IconUser, label: 'Profile' },
  ];

  const screens = {
    Dashboard: role === 'farmer'
      ? <FarmerDashboardScreen route={{ params: { role, token, profile } }} navigation={webNavigation} />
      : <BuyerDashboardScreen route={{ params: { role, token, profile } }} navigation={webNavigation} />,
    Market: <MarketplaceScreen route={{ params: { role, token, profile } }} navigation={webNavigation} />,
    Listings: <MyListingsScreen route={{ params: { token } }} navigation={webNavigation} />,
    Offers: <MyOffersScreen route={{ params: { token } }} navigation={webNavigation} />,
    Orders: <MyOrdersScreen route={{ params: { role, token } }} navigation={webNavigation} />,
    Profile: <ProfileScreen route={{ params: { role, token, profile, onLogout } }} navigation={webNavigation} />,
  };

  return (
    <View style={{ flex: 1 }}>
      <View style={{ flex: 1 }}>{screens[activeTab]}</View>
      <View style={styles.webTabBar}>
        {tabs.map(t => {
          const IconComp = t.icon;
          const active = activeTab === t.key;
          return (
            <TouchableOpacity key={t.key} style={styles.webTab} onPress={() => onChangeTab(t.key)}>
              <IconComp size={22} color={active ? accent : '#999'} />
              <Text style={[styles.webTabLabel, active && { color: accent }]}>{t.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

function MainTabs({ route }) {
  const { role = 'buyer', token, profile = {}, onLogout } = route.params || {};

  if (role === 'driver' || role === 'transporter') {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
        <Text style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 10 }}>Wrong App</Text>
        <Text style={{ fontSize: 16, textAlign: 'center', color: '#666' }}>
          Drivers should use the ZimAgriTrust Driver App
        </Text>
        <Text style={{ fontSize: 14, marginTop: 20, color: '#999' }}>
          Please download the driver app from the app store
        </Text>
      </View>
    );
  }

  const accent = role === 'farmer' ? theme.colors.green : theme.colors.sky;

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: accent,
        tabBarInactiveTintColor: '#999',
        tabBarLabelStyle: { fontSize: 11, fontWeight: '700', marginTop: -4 },
      }}
    >
      {role === 'farmer' ? (
        <Tab.Screen
          name="FarmerDashboard"
          component={FarmerDashboardScreen}
          initialParams={{ role, token, profile }}
          options={{
            tabBarLabel: 'Dashboard',
            tabBarIcon: ({ color, size }) => <IconHome size={size || 22} color={color} />,
          }}
        />
      ) : (
        <Tab.Screen
          name="BuyerDashboard"
          component={BuyerDashboardScreen}
          initialParams={{ role, token, profile }}
          options={{
            tabBarLabel: 'Dashboard',
            tabBarIcon: ({ color, size }) => <IconHome size={size || 22} color={color} />,
          }}
        />
      )}

      <Tab.Screen
        name="Marketplace"
        component={MarketplaceScreen}
        initialParams={{ role, token, profile }}
        options={{
          tabBarLabel: 'Market',
          tabBarIcon: ({ color, size }) => <IconShoppingBag size={size || 22} color={color} />,
        }}
      />

      <Tab.Screen
        name={role === 'farmer' ? 'FarmerListings' : 'BuyerOffers'}
        component={role === 'farmer' ? MyListingsScreen : MyOffersScreen}
        initialParams={{ token }}
        options={{
          tabBarLabel: role === 'farmer' ? 'Listings' : 'Offers',
          tabBarIcon: ({ color, size }) => role === 'farmer'
            ? <IconClipboardList size={size || 22} color={color} />
            : <IconHandCoins size={size || 22} color={color} />,
        }}
      />

      <Tab.Screen
        name={role === 'farmer' ? 'FarmerOrders' : 'BuyerOrders'}
        component={MyOrdersScreen}
        initialParams={{ role, token }}
        options={{
          tabBarLabel: 'Orders',
          tabBarIcon: ({ color, size }) => <IconPackage size={size || 22} color={color} />,
        }}
      />

      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        initialParams={{ role, token, profile, onLogout }}
        options={{
          tabBarLabel: 'Profile',
          tabBarIcon: ({ color, size }) => <IconUser size={size || 22} color={color} />,
        }}
      />
    </Tab.Navigator>
  );
}

export default function AppShell() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSplashing, setIsSplashing] = useState(true);
  const [onboardedState, setOnboardedState] = useState(false);
  const [role, setRole] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [session, setSession] = useState(null);
  const [webTab, setWebTab] = useState('Home');
  const [showRegister, setShowRegister] = useState(false);

  // Sync webTab if role changes
  useEffect(() => {
    setWebTab('Dashboard');
  }, [role]);

  // Restore session on mount
  useEffect(() => {
    setupNotificationHandler();
    (async () => {
      try {
        const wasOnboarded = await hasOnboarded();
        const savedSession = await getSession();

        if (wasOnboarded) setOnboardedState(true);
        if (savedSession?.access_token) {
          setSession(savedSession);
          setRole(savedSession.role || savedSession.profile?.role?.toLowerCase() || 'farmer');
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

  const handleOnboardingComplete = useCallback(async (selectedRole) => {
    setRole(selectedRole);
    setOnboardedState(true);
    await setOnboarded(true);
  }, []);

  const handleAuth = useCallback(async (authData) => {
    setSession(authData);
    setAuthenticated(true);
    const serverRole = authData.profile?.role?.toLowerCase() || authData.user?.role?.toLowerCase() || role;
    setRole(serverRole);
    setOnboardedState(true);
    await saveSession(authData.access_token, authData.profile || authData.user, serverRole, authData.refresh_token);
    await setOnboarded(true);
    registerForPushNotifications().catch(() => {});
  }, [role]);

  const handleLogout = useCallback(async () => {
    await clearSession();
    setSession(null);
    setAuthenticated(false);
    setRole(null);
    setOnboardedState(false);
  }, []);

  const handleGuest = useCallback(() => {
    setRole('buyer');
    setSession({ guest: true, profile: { role: 'buyer', full_name: 'Guest' } });
    setAuthenticated(true);
  }, []);

  if (isLoading || isSplashing) {
    return (
      <View style={styles.splash}>
        <View style={styles.splashLogoContainer}>
          <Image source={require('../assets/logo.png')} style={{ width: 100, height: 100, resizeMode: 'contain' }} />
        </View>
        <Text style={styles.splashBrand}>ZIMAGRITRUST</Text>
        <Text style={styles.splashMarket}>AGRICULTURAL MARKETPLACE</Text>
        <ActivityIndicator size="large" color="rgba(255,255,255,0.7)" style={{ marginTop: 32 }} />
        <View style={styles.onboardBox}>
          <Text style={styles.onboardText}>Connecting Zimbabwe's Agricultural Value Chain</Text>
        </View>
      </View>
    );
  }

  if (!authenticated) {
    if (showRegister) {
      return <RegistrationScreen onRegistered={handleAuth} onBack={() => setShowRegister(false)} />;
    }
    return <LoginScreen role={role || 'buyer'} onAuthenticated={handleAuth} onGuest={handleGuest} onRegister={() => setShowRegister(true)} />;
  }

  if (!onboardedState && !session?.guest) {
    return <OnboardingScreen onComplete={handleOnboardingComplete} />;
  }

  if (Platform.OS === 'web') {
    return (
      <WebTabBar
        activeTab={webTab}
        onChangeTab={setWebTab}
        role={role}
        token={session?.access_token}
        profile={session?.profile}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen
          name="Main"
          component={MainTabs}
          initialParams={{
            role,
            token: session?.access_token,
            profile: session?.profile,
            onLogout: handleLogout,
          }}
        />
        <Stack.Screen name="ListingDetail" component={ListingDetailScreen} />
        <Stack.Screen name="OrderDetails" component={OrderDetailsScreen} />
        <Stack.Screen name="MakeOffer" component={MakeOfferScreen} />
        <Stack.Screen name="ConfirmDelivery" component={ConfirmationScreen} />
        <Stack.Screen name="Wallet" component={WalletScreen} />
        <Stack.Screen name="FarmerWallet" component={WalletScreen} />
        <Stack.Screen name="BuyerWallet" component={WalletScreen} />
        <Stack.Screen name="MyListings" component={MyListingsScreen} />
        <Stack.Screen name="OffersReceived" component={OffersReceivedScreen} />
        <Stack.Screen name="MyOffers" component={MyOffersScreen} />
        <Stack.Screen name="SavedListings" component={SavedListingsScreen} />
        <Stack.Screen name="MyOrders" component={MyOrdersScreen} />
        <Stack.Screen name="FarmerOrders" component={MyOrdersScreen} />
        <Stack.Screen name="BuyerOrders" component={MyOrdersScreen} />
        <Stack.Screen name="RateUser" component={RateUserScreen} />
        <Stack.Screen name="Withdraw" component={WithdrawScreen} />
        <Stack.Screen name="CreateListing" component={CreateListingScreen} />
        <Stack.Screen name="Payment" component={PaymentScreen} />
        <Stack.Screen name="AgentApplication" component={AgentApplicationScreen} />
        <Stack.Screen name="EditProfile" component={EditProfileScreen} />
        <Stack.Screen name="ChangePin" component={ChangePinScreen} />
        <Stack.Screen name="Settings" component={SettingsScreen} />
        <Stack.Screen name="Privacy" component={PrivacyScreen} />
        <Stack.Screen name="Support" component={SupportScreen} />
        <Stack.Screen name="Disputes" component={DisputesScreen} />
        <Stack.Screen name="RaiseDispute" component={RaiseDisputeScreen} />
        <Stack.Screen name="Verification" component={VerificationScreen} />
        <Stack.Screen name="AgentVerification" component={AgentVerificationScreen} />
        <Stack.Screen name="Analytics" component={AnalyticsScreen} />
        <Stack.Screen name="Chat" component={ChatScreen} />
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="RiskScore" component={RiskScoreScreen} />
        <Stack.Screen name="Transactions" component={TransactionsScreen} />
        <Stack.Screen name="TransportNegotiation" component={TransportNegotiationScreen} />
        <Stack.Screen name="TransportSelection" component={TransportSelectionScreen} />
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
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    bottom: 12,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
  },
  splash: { flex: 1, backgroundColor: theme.colors.green, justifyContent: 'center', alignItems: 'center' },
  splashLogoContainer: { width: 140, height: 140, borderRadius: 70, backgroundColor: 'rgba(255,255,255,0.15)', justifyContent: 'center', alignItems: 'center', marginBottom: 24, borderWidth: 2, borderColor: 'rgba(255,255,255,0.3)' },
  splashLogo: { fontSize: 52 },
  splashBrand: { fontSize: 28, fontWeight: '800', color: '#FFF', letterSpacing: 3, textTransform: 'uppercase' },
  splashMarket: { fontSize: 16, fontWeight: '600', color: theme.colors.gold, letterSpacing: 2, textTransform: 'uppercase', marginTop: 8 },
  onboardBox: { position: 'absolute', bottom: 100, paddingHorizontal: 40, alignItems: 'center' },
  onboardText: { color: '#FFF', fontSize: 16, textAlign: 'center', marginBottom: 40, lineHeight: 24, fontWeight: '500', letterSpacing: 0.5 },
  webTabBar: { flexDirection: 'row', backgroundColor: '#FFF', borderTopWidth: 1, borderTopColor: '#EEE', paddingVertical: 10, paddingBottom: 20 },
  webTab: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 4 },
  webTabLabel: { fontSize: 11, fontWeight: '700', color: '#999' },
});
