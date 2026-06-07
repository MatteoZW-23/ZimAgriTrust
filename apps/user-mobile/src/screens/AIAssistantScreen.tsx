import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Bot, Send, Sparkles, TrendingUp } from 'lucide-react-native';
import { chatWithAiAssistant, getAiMarketIntelligence, getAiPriceDemandPrediction, getAiRecommendations } from '../api';
import { theme } from '../styles';

type AssistantRole = 'farmer' | 'buyer' | 'supplier' | 'agent' | 'admin';

const ROLE_LABELS = {
  farmer: 'Farmer AI',
  buyer: 'Buyer AI',
  supplier: 'Supplier AI',
  agent: 'Agent AI',
  admin: 'Admin AI',
} as const;

function normalizeRole(role: any): AssistantRole {
  const raw = String(role || 'buyer').toLowerCase();
  if (raw.includes('farmer')) return 'farmer';
  if (raw.includes('supplier')) return 'supplier';
  if (raw.includes('agent')) return 'agent';
  if (raw.includes('admin')) return 'admin';
  return 'buyer';
}

export default function AIAssistantScreen({ route }: any) {
  const { token, role = 'buyer', profile = {} } = route.params || {};
  const assistantRole = useMemo(() => normalizeRole(role || profile?.role), [role, profile]);
  const accent = assistantRole === 'farmer' ? theme.colors.green : theme.colors.sky;
  const [message, setMessage] = useState('What should I focus on today?');
  const [product, setProduct] = useState('Horticulture');
  const [loading, setLoading] = useState(false);
  const [assistant, setAssistant] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [market, setMarket] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);

  const load = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const [recData, marketData, predictionData] = await Promise.all([
        getAiRecommendations(token, assistantRole, { product }),
        getAiMarketIntelligence(token, product || null, profile?.province || null),
        getAiPriceDemandPrediction(token, product || 'Horticulture', profile?.province || null, 30),
      ]);
      setRecommendations(recData);
      setMarket(marketData);
      setPrediction(predictionData);
    } catch (err: any) {
      Alert.alert('AI unavailable', err.message || 'Could not load assistant insights.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [token, assistantRole]);

  const sendMessage = async () => {
    if (!message.trim()) return;
    try {
      setLoading(true);
      const data = await chatWithAiAssistant(token, assistantRole, message.trim(), {
        product,
        province: profile?.province,
      });
      setAssistant(data);
    } catch (err: any) {
      Alert.alert('Assistant failed', err.message || 'Could not get AI guidance.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={[styles.hero, { borderColor: `${accent}33` }]}>
          <View style={[styles.iconWrap, { backgroundColor: `${accent}18` }]}>
            <Bot size={30} color={accent} />
          </View>
          <Text style={styles.kicker}>AI ASSISTANT</Text>
          <Text style={styles.title}>{ROLE_LABELS[assistantRole] || 'Agric AI'}</Text>
          <Text style={styles.subtitle}>Role-specific guidance, market signals, and next-best actions from platform data.</Text>
        </View>

        <View style={styles.inputCard}>
          <Text style={styles.label}>Agriculture product or sector</Text>
          <TextInput value={product} onChangeText={setProduct} style={styles.input} placeholder="Honey, goats, flowers, fish, maize..." placeholderTextColor="#94a3b8" />
          <Text style={styles.label}>Ask the assistant</Text>
          <TextInput value={message} onChangeText={setMessage} style={[styles.input, styles.messageInput]} multiline placeholder="Ask about pricing, transport, disputes, selling, buying..." placeholderTextColor="#94a3b8" />
          <View style={styles.actions}>
            <TouchableOpacity style={[styles.secondaryBtn, { borderColor: accent }]} onPress={load} disabled={loading}>
              <TrendingUp size={17} color={accent} />
              <Text style={[styles.secondaryText, { color: accent }]}>Refresh Insights</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.primaryBtn, { backgroundColor: accent }]} onPress={sendMessage} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Send size={17} color="#fff" />}
              <Text style={styles.primaryText}>Ask</Text>
            </TouchableOpacity>
          </View>
        </View>

        {assistant ? (
          <InsightCard icon={Sparkles} title="Assistant Answer" color={accent}>
            <Text style={styles.answer}>{assistant.answer}</Text>
            {(assistant.recommended_actions || []).slice(0, 3).map((item: string, index: number) => (
              <Text key={index} style={styles.bullet}>- {item}</Text>
            ))}
          </InsightCard>
        ) : null}

        {recommendations ? (
          <InsightCard icon={Sparkles} title="Recommended Actions" color={accent}>
            {(recommendations.actions || []).slice(0, 4).map((item: string, index: number) => (
              <Text key={index} style={styles.bullet}>- {item}</Text>
            ))}
          </InsightCard>
        ) : null}

        {market ? (
          <InsightCard icon={TrendingUp} title="Market Intelligence" color={theme.colors.gold}>
            <View style={styles.metricGrid}>
              <Metric label="Demand" value={market.status} />
              <Metric label="Index" value={market.demand_index} />
              <Metric label="Supply" value={market.total_supply} />
              <Metric label="Avg price" value={`$${market.average_price}`} />
            </View>
            <Text style={styles.answer}>{market.recommendation}</Text>
          </InsightCard>
        ) : null}

        {prediction ? (
          <InsightCard icon={TrendingUp} title="Price and Demand Prediction" color={theme.colors.orange}>
            <Text style={styles.answer}>{prediction.recommended_action}</Text>
            <Text style={styles.bullet}>- Demand confidence: {prediction.demand_prediction?.confidence || 'low'}</Text>
            <Text style={styles.bullet}>- Price trend: {prediction.price_prediction?.trend || 'STABLE'}</Text>
          </InsightCard>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

function InsightCard({ icon: Icon, title, color, children }: any) {
  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={[styles.smallIcon, { backgroundColor: `${color}18` }]}>
          <Icon size={18} color={color} />
        </View>
        <Text style={styles.cardTitle}>{title}</Text>
      </View>
      {children}
    </View>
  );
}

function Metric({ label, value }: any) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue}>{String(value ?? '-')}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.gray[100] },
  content: { padding: 20, paddingTop: 54, paddingBottom: 120 },
  hero: { backgroundColor: '#fff', borderRadius: 26, borderWidth: 1, padding: 22, marginBottom: 16, ...theme.shadows.sm },
  iconWrap: { width: 58, height: 58, borderRadius: 18, alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
  kicker: { fontSize: 11, color: '#64748b', fontWeight: '900', letterSpacing: 1 },
  title: { fontSize: 32, color: theme.colors.ink, fontWeight: '900', marginTop: 5 },
  subtitle: { fontSize: 14, color: '#64748b', lineHeight: 21, marginTop: 8 },
  inputCard: { backgroundColor: '#fff', borderRadius: 24, borderWidth: 1, borderColor: '#e2e8f0', padding: 18, marginBottom: 16, ...theme.shadows.sm },
  label: { fontSize: 12, color: '#64748b', fontWeight: '900', marginBottom: 8, textTransform: 'uppercase' },
  input: { borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 16, padding: 14, color: theme.colors.ink, fontWeight: '800', marginBottom: 14, backgroundColor: '#fff' },
  messageInput: { minHeight: 92, textAlignVertical: 'top' },
  actions: { flexDirection: 'row', gap: 10 },
  primaryBtn: { flex: 1, borderRadius: 16, paddingVertical: 14, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8 },
  primaryText: { color: '#fff', fontWeight: '900' },
  secondaryBtn: { flex: 1, borderRadius: 16, paddingVertical: 14, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8, borderWidth: 1 },
  secondaryText: { fontWeight: '900' },
  card: { backgroundColor: '#fff', borderRadius: 24, borderWidth: 1, borderColor: '#e2e8f0', padding: 18, marginBottom: 14, ...theme.shadows.sm },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 12 },
  smallIcon: { width: 36, height: 36, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  cardTitle: { color: theme.colors.ink, fontWeight: '900', fontSize: 16 },
  answer: { color: '#334155', fontSize: 14, lineHeight: 21, fontWeight: '700', marginBottom: 8 },
  bullet: { color: '#475569', fontSize: 13, lineHeight: 20, fontWeight: '700', marginTop: 5 },
  metricGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 12 },
  metric: { flexBasis: '47%', backgroundColor: '#f8fafc', borderRadius: 16, padding: 12, borderWidth: 1, borderColor: '#e2e8f0' },
  metricValue: { color: theme.colors.ink, fontWeight: '900', fontSize: 16 },
  metricLabel: { color: '#64748b', fontSize: 11, fontWeight: '800', marginTop: 4 },
});
