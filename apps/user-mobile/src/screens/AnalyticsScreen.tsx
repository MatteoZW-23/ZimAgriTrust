import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, SafeAreaView, TouchableOpacity,
  ActivityIndicator, Dimensions, Alert
} from 'react-native';
import { LineChart, BarChart, PieChart } from 'react-native-chart-kit';
import { 
  TrendingUp as IconTrendingUp, TrendingDown as IconTrendingDown, 
  DollarSign as IconDollarSign, Package as IconPackage, 
  Users as IconUsers, Calendar as IconCalendar, 
  Filter as IconFilter, Download as IconDownload, 
  RefreshCw as IconRefreshCw, Eye as IconEye 
} from 'lucide-react-native';
import { theme } from '../styles';
import { getUserAnalytics, getMarketTrends } from '../api';

const { width: screenWidth } = Dimensions.get('window');

export default function AnalyticsScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [analytics, setAnalytics] = useState(null);
  const [marketTrends, setMarketTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [period, setPeriod] = useState('month');
  const [selectedMetric, setSelectedMetric] = useState('revenue');

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const [analyticsData, trendsData] = await Promise.all([
        getUserAnalytics(token, period),
        getMarketTrends(token)
      ]);
      
      setAnalytics(analyticsData);
      setMarketTrends(trendsData);
    } catch {
      setAnalytics({
        revenue: { current: 0, previous: 0, growth: 0 },
        orders: { current: 0, previous: 0, growth: 0 },
        listings: { current: 0, previous: 0, growth: 0 },
        customers: { current: 0, previous: 0, growth: 0 },
        performance: {
          avg_order_value: 0,
          conversion_rate: 0,
          fulfillment_rate: 0,
          customer_satisfaction: 0
        },
        revenue_chart: [{ month: 'Now', revenue: 0 }],
        category_breakdown: []
      });
      
      setMarketTrends({
        top_crops: [],
        market_insights: []
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token, period]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAnalytics();
  };

  const handleExport = () => {
    Alert.alert('Export Analytics', 'Choose export format:', [
      { text: 'PDF Report', onPress: () => Alert.alert('Export unavailable', 'Report export is not available for this account yet.') },
      { text: 'Excel Data', onPress: () => Alert.alert('Export unavailable', 'Data export is not available for this account yet.') },
      { text: 'Cancel', style: 'cancel' }
    ]);
  };

  const MetricCard = ({ title, value, previous, growth, icon: Icon, color }) => {
    const isPositive = growth >= 0;
    
    return (
      <TouchableOpacity style={styles.metricCard}>
        <View style={styles.metricHeader}>
          <View style={[styles.metricIcon, { backgroundColor: color + '20' }]}>
            <Icon size={20} color={color} />
          </View>
          <View style={styles.metricTrend}>
            {isPositive ? (
              <IconTrendingUp size={16} color="#4CAF50" />
            ) : (
              <IconTrendingDown size={16} color="#F44336" />
            )}
            <Text style={[styles.trendText, isPositive ? styles.positiveTrend : styles.negativeTrend]}>
              {Math.abs(growth)}%
            </Text>
          </View>
        </View>
        <Text style={styles.metricValue}>{value}</Text>
        <Text style={styles.metricTitle}>{title}</Text>
        <Text style={styles.metricPrevious}>Previous: {previous}</Text>
      </TouchableOpacity>
    );
  };

  const PerformanceIndicator = ({ label, value, unit, icon: Icon }) => (
    <View style={styles.performanceItem}>
      <View style={styles.performanceHeader}>
        <Icon size={16} color={theme.colors.sky} />
        <Text style={styles.performanceLabel}>{label}</Text>
      </View>
      <Text style={styles.performanceValue}>
        {value}
        <Text style={styles.performanceUnit}>{unit}</Text>
      </Text>
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.sky} />
          <Text style={styles.loadingText}>Loading analytics...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const data = analytics || {};

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Analytics</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.actionButton} onPress={handleRefresh}>
            <IconRefreshCw size={20} color={theme.colors.sky} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={handleExport}>
            <IconDownload size={20} color={theme.colors.sky} />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} style={styles.scrollView}>
        {/* Period Selector */}
        <View style={styles.periodSelector}>
          {['week', 'month', 'quarter', 'year'].map(p => (
            <TouchableOpacity
              key={p}
              style={[styles.periodChip, period === p && styles.periodActive]}
              onPress={() => setPeriod(p)}
            >
              <Text style={[styles.periodText, period === p && styles.periodTextActive]}>
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Key Metrics */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key Performance Metrics</Text>
          <View style={styles.metricsGrid}>
            <MetricCard
              title="Revenue"
              value={`$${data.revenue?.current.toLocaleString()}`}
              previous={`$${data.revenue?.previous.toLocaleString()}`}
              growth={data.revenue?.growth}
              icon={IconDollarSign}
              color="#4CAF50"
            />
            <MetricCard
              title="Orders"
              value={data.orders?.current}
              previous={data.orders?.previous}
              growth={data.orders?.growth}
              icon={IconPackage}
              color="#FF9800"
            />
            <MetricCard
              title="Listings"
              value={data.listings?.current}
              previous={data.listings?.previous}
              growth={data.listings?.growth}
              icon={IconEye}
              color="#2196F3"
            />
            <MetricCard
              title="Customers"
              value={data.customers?.current}
              previous={data.customers?.previous}
              growth={data.customers?.growth}
              icon={IconUsers}
              color="#9C27B0"
            />
          </View>
        </View>

        {/* Revenue Chart */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Revenue Trend</Text>
          <View style={styles.chartCard}>
            <LineChart
              data={{
                labels: data.revenue_chart?.map(d => d.month) || [],
                datasets: [{
                  data: data.revenue_chart?.map(d => d.revenue) || [],
                  color: (opacity = 1) => `rgba(33, 150, 243, ${opacity})`,
                  strokeWidth: 3
                }]
              }}
              width={screenWidth - 40}
              height={220}
              chartConfig={{
                backgroundColor: '#FFF',
                backgroundGradientFrom: '#FFF',
                backgroundGradientTo: '#FFF',
                decimalPlaces: 0,
                color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity * 0.6})`,
                style: { borderRadius: 16 },
                propsForDots: { r: '6', strokeWidth: '2', stroke: '#2196F3' }
              }}
              bezier
              style={styles.chart}
            />
          </View>
        </View>

        {/* Category Breakdown */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Sales by Category</Text>
          <View style={styles.chartCard}>
            <PieChart
              data={data.category_breakdown || []}
              width={screenWidth - 40}
              height={200}
              chartConfig={{
                color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              }}
              accessor="value"
              backgroundColor="transparent"
              paddingLeft="15"
              center={[10, 10]}
              absolute
            />
          </View>
        </View>

        {/* Performance Indicators */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Performance Indicators</Text>
          <View style={styles.performanceGrid}>
            <PerformanceIndicator
              label="Avg Order Value"
              value={data.performance?.avg_order_value}
              unit="USD"
              icon={IconDollarSign}
            />
            <PerformanceIndicator
              label="Conversion Rate"
              value={data.performance?.conversion_rate}
              unit="%"
              icon={IconTrendingUp}
            />
            <PerformanceIndicator
              label="Fulfillment Rate"
              value={data.performance?.fulfillment_rate}
              unit="%"
              icon={IconPackage}
            />
            <PerformanceIndicator
              label="Customer Satisfaction"
              value={data.performance?.customer_satisfaction}
              unit="/5"
              icon={IconUsers}
            />
          </View>
        </View>

        {/* Market Trends */}
        {marketTrends && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Market Trends</Text>
            <View style={styles.trendsCard}>
              {marketTrends.top_crops?.map((crop, index) => (
                <View key={index} style={styles.trendItem}>
                  <View style={styles.trendHeader}>
                    <Text style={styles.trendCrop}>{crop.crop}</Text>
                    <View style={[
                      styles.demandBadge,
                      crop.demand === 'high' ? styles.highDemand : styles.mediumDemand
                    ]}>
                      <Text style={styles.demandText}>{crop.demand}</Text>
                    </View>
                  </View>
                  <View style={styles.priceChange}>
                    <Text style={[
                      styles.priceText,
                      crop.price_change >= 0 ? styles.priceUp : styles.priceDown
                    ]}>
                      {crop.price_change >= 0 ? '+' : ''}{crop.price_change}%
                    </Text>
                  </View>
                </View>
              ))}
            </View>
            
            <View style={styles.insightsCard}>
              <Text style={styles.insightsTitle}>Market Insights</Text>
              {marketTrends.market_insights?.map((insight, index) => (
                <Text key={index} style={styles.insightText}>• {insight}</Text>
              ))}
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: { color: '#999', marginTop: 12, fontWeight: '600' },
  
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  title: { fontSize: 28, fontWeight: '900', color: theme.colors.dark },
  headerActions: { flexDirection: 'row', gap: 12 },
  actionButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
  },
  
  scrollView: { flex: 1 },
  section: { marginHorizontal: 20, marginTop: 24 },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: theme.colors.dark,
    marginBottom: 16,
  },
  
  periodSelector: {
    flexDirection: 'row',
    marginHorizontal: 20,
    gap: 8,
    marginTop: 16,
  },
  periodChip: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: '#FFF',
    borderWidth: 1,
    borderColor: '#F0F0F0',
    alignItems: 'center',
  },
  periodActive: { backgroundColor: theme.colors.sky, borderColor: theme.colors.sky },
  periodText: { fontSize: 13, fontWeight: '700', color: '#999' },
  periodTextActive: { color: '#FFF' },
  
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  metricCard: {
    width: '48%',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    ...theme.shadows.xs,
  },
  metricHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  metricIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  metricTrend: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  trendText: { fontSize: 12, fontWeight: '700' },
  positiveTrend: { color: '#4CAF50' },
  negativeTrend: { color: '#F44336' },
  metricValue: {
    fontSize: 24,
    fontWeight: '900',
    color: theme.colors.dark,
    marginBottom: 4,
  },
  metricTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
    marginBottom: 2,
  },
  metricPrevious: {
    fontSize: 11,
    color: '#999',
    fontWeight: '500',
  },
  
  chartCard: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    ...theme.shadows.xs,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  
  performanceGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  performanceItem: {
    width: '48%',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    ...theme.shadows.xs,
  },
  performanceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  performanceLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
  },
  performanceValue: {
    fontSize: 20,
    fontWeight: '900',
    color: theme.colors.dark,
  },
  performanceUnit: {
    fontSize: 14,
    fontWeight: '600',
    color: '#999',
    marginLeft: 4,
  },
  
  trendsCard: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    ...theme.shadows.xs,
    marginBottom: 16,
  },
  trendItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  trendHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  trendCrop: {
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.dark,
  },
  demandBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  highDemand: { backgroundColor: '#E8F5E9' },
  mediumDemand: { backgroundColor: '#FFF3E0' },
  demandText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#4CAF50',
  },
  priceChange: {},
  priceText: {
    fontSize: 14,
    fontWeight: '700',
  },
  priceUp: { color: '#4CAF50' },
  priceDown: { color: '#F44336' },
  
  insightsCard: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    ...theme.shadows.xs,
  },
  insightsTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.dark,
    marginBottom: 12,
  },
  insightText: {
    fontSize: 13,
    color: '#666',
    lineHeight: 20,
    marginBottom: 8,
  },
});
