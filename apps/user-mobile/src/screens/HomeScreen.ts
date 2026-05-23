import React from "react";
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, SafeAreaView } from "react-native";
import { 
  Bell as IconBell, 
  Trophy as IconTrophy, 
  Sprout as IconSprout, 
  DollarSign as IconDollar, 
  Package as IconPackage, 
  Star as IconStar, 
  Plus as IconPlus, 
  BarChart3 as IconAnalytics 
} from 'lucide-react-native';
import { theme } from "../styles";

export default function HomeScreen({ route, navigation }) {
  const { profile = {}, role = 'farmer', token } = route.params || {};
  const name = profile.name || "User";
  const trustScore = profile.trust_score || 0;
  const balance = profile.balance || 0;
  const zigBalance = profile.zig_balance || 0;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
            <View>
                <Text style={styles.greetingText}>Good Day,</Text>
                <Text style={styles.nameText}>{name.split(' ')[0]}</Text>
            </View>
            <View style={styles.headerIcons}>
                <TouchableOpacity style={styles.iconBtn} onPress={() => navigation.navigate('Notifications', { token })}>
                    <IconBell size={24} color={theme.colors.black} />
                </TouchableOpacity>
                <View style={styles.walletBox}>
                    <Text style={styles.walletText}>${balance.toLocaleString()} | ZiG {zigBalance.toLocaleString()}</Text>
                </View>
            </View>
        </View>

        {/* Trust Score Card */}
        <TouchableOpacity style={styles.trustCard}>
            <View style={styles.row}>
                <View style={styles.trustInfo}>
                    <Text style={styles.trustLabel}>Network Trust</Text>
                    <View style={styles.rowCenter}>
                        <Text style={styles.trustValue}>{trustScore}</Text>
                        <Text style={styles.trustStatus}>{trustScore > 80 ? 'Elite Tier' : 'Standard'}</Text>
                    </View>
                </View>
                <IconTrophy size={48} color="#FFD700" />
            </View>
            <View style={styles.progressBar}>
                <View style={[styles.progressFill, { width: `${trustScore}%` }]} />
            </View>
        </TouchableOpacity>

        {/* Metric Grid */}
        <View style={styles.grid}>
            <View style={styles.gridRow}>
                <MetricCard icon={<IconSprout size={28} color={theme.colors.green} />} label="My Listings" value={profile.listing_count || "0"} />
                <MetricCard icon={<IconDollar size={28} color={theme.colors.green} />} label="Total Sales" value={`$${profile.total_sales || "0"}`} />
            </View>
            <View style={styles.gridRow}>
                <MetricCard icon={<IconPackage size={28} color={theme.colors.green} />} label="Pending Handover" value={profile.pending_orders || "0"} />
                <MetricCard icon={<IconStar size={28} color={theme.colors.green} />} label="Reliability" value={profile.rating || "---"} />
            </View>
        </View>

        {/* Quick Actions */}
        <Text style={styles.sectionTitle}>Operational Hub</Text>
        <View style={styles.row}>
            <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('CreateListing', { token })}>
                <IconPlus size={18} color={theme.colors.green} style={{ marginRight: 8 }} />
                <Text style={styles.actionText}>New Listing</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.actionBtn, { backgroundColor: '#F0F0F0' }]} onPress={() => navigation.navigate('Analytics', { token })}>
                <IconAnalytics size={18} color="#333" style={{ marginRight: 8 }} />
                <Text style={[styles.actionText, { color: '#333' }]}>Analytics</Text>
            </TouchableOpacity>
        </View>

        {/* Recent Activity */}
        <Text style={styles.sectionTitle}>Transactional Ledger</Text>
        <View style={{ paddingHorizontal: 24, paddingVertical: 12, alignItems: 'center' }}>
            <Text style={{ fontSize: 13, color: '#94a3b8', fontStyle: 'italic' }}>Real-time activities will appear as the market moves.</Text>
        </View>

        <View style={{ height: 120 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function MetricCard({ icon, label, value }) {
    return (
        <View style={styles.metricCard}>
            <View style={{ marginBottom: 8 }}>{icon}</View>
            <Text style={styles.metricValue}>{value}</Text>
            <Text style={styles.metricLabel}>{label}</Text>
        </View>
    );
}

function ActivityItem({ title, buyer, status, amount, color }) {
    return (
        <View style={styles.activityItem}>
            <View style={styles.rowSpaced}>
                <View>
                    <Text style={styles.activityTitle}>{title}</Text>
                    <Text style={styles.activitySub}>{buyer}</Text>
                </View>
                <Text style={[styles.activityAmount, { color: theme.colors.green }]}>{amount}</Text>
            </View>
            <View style={styles.statusRow}>
                <View style={[styles.statusDot, { backgroundColor: color }]} />
                <Text style={[styles.statusText, { color }]}>{status}</Text>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF' },
  header: { padding: 24, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  greetingText: { fontSize: 16, color: '#666' },
  nameText: { fontSize: 24, fontWeight: '900', color: theme.colors.black },
  headerIcons: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconBtn: { padding: 8 },
  redDot: { position: 'absolute', top: 8, right: 8, width: 8, height: 8, borderRadius: 4, backgroundColor: 'red' },
  walletBox: { backgroundColor: '#F9F9F9', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 12 },
  walletText: { fontSize: 12, fontWeight: '800', color: theme.colors.green },
  trustCard: { marginHorizontal: 24, padding: 24, backgroundColor: '#FFF', borderRadius: 24, borderWidth: 1, borderColor: '#EEE', shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.05, shadowRadius: 10, elevation: 4 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  rowCenter: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  trustLabel: { fontSize: 13, color: '#999', fontWeight: '700', textTransform: 'uppercase' },
  trustValue: { fontSize: 32, fontWeight: '900', color: theme.colors.black },
  trustStatus: { fontSize: 14, fontWeight: '700', color: theme.colors.green },
  progressBar: { height: 8, backgroundColor: '#EEE', borderRadius: 4, marginTop: 16, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: theme.colors.green },
  grid: { padding: 24, gap: 16 },
  gridRow: { flexDirection: 'row', gap: 16 },
  metricCard: { flex: 1, padding: 20, backgroundColor: '#F9F9F9', borderRadius: 20, alignItems: 'center' },
  metricValue: { fontSize: 20, fontWeight: '900', color: theme.colors.black },
  metricLabel: { fontSize: 12, color: '#666', marginTop: 4 },
  sectionTitle: { fontSize: 18, fontWeight: '800', marginHorizontal: 24, marginTop: 12, marginBottom: 16 },
  actionBtn: { flex: 1, backgroundColor: '#FFF', borderWidth: 1, borderColor: theme.colors.green, marginHorizontal: 24, height: 60, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  actionText: { fontWeight: '800', color: theme.colors.green, fontSize: 15 },
  activityItem: { marginHorizontal: 24, padding: 20, backgroundColor: '#FFF', borderRadius: 20, borderWidth: 1, borderColor: '#F0F0F0', marginBottom: 12 },
  rowSpaced: { flexDirection: 'row', justifyContent: 'space-between' },
  activityTitle: { fontSize: 16, fontWeight: '800', color: theme.colors.black },
  activitySub: { fontSize: 12, color: '#999', marginTop: 2 },
  activityAmount: { fontSize: 16, fontWeight: '800' },
  statusRow: { flexDirection: 'row', alignItems: 'center', marginTop: 12 },
  statusDot: { width: 8, height: 8, borderRadius: 4, marginRight: 8 },
  statusText: { fontSize: 12, fontWeight: '800' }
});
