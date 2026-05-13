import React from 'react';
import { Linking, SafeAreaView, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { HelpCircle, Mail, MessageCircle } from 'lucide-react-native';
import { theme } from '../styles';

const FAQS = [
  ['How does escrow work?', 'Buyer funds are held until delivery is confirmed or a dispute is resolved.'],
  ['Can I use the same PIN on USSD?', 'Yes. Farmers and buyers use the same 4-6 digit PIN on app and USSD.'],
  ['When do drivers start working?', 'Drivers can only accept jobs after admin approval.'],
];

export default function SupportScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <HelpCircle size={34} color={theme.colors.green} />
        <Text style={styles.title}>Support</Text>
        <Text style={styles.subtitle}>Fast help for marketplace, payment, delivery, and account issues.</Text>

        <View style={styles.card}>
          {FAQS.map(([question, answer]) => (
            <View key={question} style={styles.faq}>
              <Text style={styles.question}>{question}</Text>
              <Text style={styles.answer}>{answer}</Text>
            </View>
          ))}
        </View>

        <TouchableOpacity style={styles.button} onPress={() => Linking.openURL('https://wa.me/263000000000')}>
          <MessageCircle size={18} color="#fff" />
          <Text style={styles.buttonText}>Contact Support on WhatsApp</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.button, styles.secondary]} onPress={() => Linking.openURL('mailto:support@zimagritrust.co.zw?subject=Mobile%20App%20Support')}>
          <Mail size={18} color={theme.colors.green} />
          <Text style={styles.secondaryText}>Report Issue by Email</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6F0DE' },
  content: { padding: 20, paddingTop: 56, paddingBottom: 120 },
  title: { color: '#111827', fontSize: 32, fontWeight: '900', marginTop: 12 },
  subtitle: { color: '#64748b', fontSize: 14, lineHeight: 21, marginTop: 8, marginBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#e5e7eb', marginBottom: 16 },
  faq: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#f1f5f9' },
  question: { color: '#111827', fontSize: 16, fontWeight: '900' },
  answer: { color: '#64748b', fontSize: 14, lineHeight: 21, marginTop: 6, fontWeight: '600' },
  button: { backgroundColor: theme.colors.green, borderRadius: 16, paddingVertical: 15, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8, marginBottom: 12 },
  buttonText: { color: '#fff', fontWeight: '900', fontSize: 15 },
  secondary: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#bbf7d0' },
  secondaryText: { color: theme.colors.green, fontWeight: '900', fontSize: 15 },
});
