import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  SafeAreaView, Linking, LayoutAnimation, Platform, UIManager,
} from 'react-native';
import Animated, { FadeInDown, FadeInUp } from 'react-native-reanimated';
import {
  HelpCircle as IconHelpCircle, MessageCircle as IconMessageCircle, 
  Mail as IconMail, Phone as IconPhone,
  ChevronDown as IconChevronDown, ChevronUp as IconChevronUp, 
  MessageSquare as IconMessageSquare,
} from 'lucide-react-native';
import { theme } from '../styles';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

const FAQ = [
  {
    q: 'How long does verification take?',
    a: 'Verification usually takes 24–48 hours. Our team reviews your uploaded documents and background check. You will receive a notification once approved.',
  },
  {
    q: 'When do I get paid?',
    a: 'Payments are processed immediately after successful delivery. You can withdraw your available balance to EcoCash at any time from the Earnings screen.',
  },
  {
    q: 'What if a customer is not at the location?',
    a: 'If the customer is unavailable, try calling them through the app. If you still cannot reach them, report an issue in the delivery screen and follow admin instructions.',
  },
  {
    q: 'How are delivery fees calculated?',
    a: 'Fees are based on distance, cargo weight, and vehicle type. We use a transparent pricing model that ensures fair compensation for drivers.',
  },
];

export default function SupportScreen() {
  const [expanded, setExpanded] = useState(null);

  const toggleExpand = (i) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded(expanded === i ? null : i);
  };

  const handleContactWhatsApp = () => {
    Linking.openURL('whatsapp://send?phone=+263770000000&text=Hi ZimAgriTrust, I need help with my driver account.');
  };

  const handleContactEmail = () => {
    Linking.openURL('mailto:support@zimagritrust.org?subject=Driver Support Request');
  };

  const handleCallSupport = () => {
    Linking.openURL('tel:+263770000000');
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        <Animated.View entering={FadeInDown.duration(600).springify()} style={styles.header}>
          <View style={styles.headerIconWrap}>
            <IconHelpCircle size={32} color="#8B5CF6" />
          </View>
          <Text style={styles.title}>Help & Support</Text>
          <Text style={styles.subtitle}>We're always here for you</Text>
        </Animated.View>

        <Animated.View entering={FadeInUp.duration(600).delay(100).springify()} style={styles.contactSection}>
          <Text style={styles.sectionTitle}>Get in Touch</Text>
          <View style={styles.contactGrid}>
            <ContactCard
              icon={<IconMessageCircle size={26} color="#10B981" />}
              bg="#D1FAE5"
              label="WhatsApp"
              onPress={handleContactWhatsApp}
            />
            <ContactCard
              icon={<IconPhone size={26} color="#0EA5E9" />}
              bg="#E0F2FE"
              label="Call Us"
              onPress={handleCallSupport}
            />
            <ContactCard
              icon={<IconMail size={26} color="#EF4444" />}
              bg="#FEE2E2"
              label="Email"
              onPress={handleContactEmail}
            />
          </View>
        </Animated.View>

        <Animated.View entering={FadeInUp.duration(600).delay(200).springify()} style={styles.section}>
          <Text style={styles.sectionTitle}>Frequently Asked Questions</Text>
          <View style={styles.faqCard}>
            {FAQ.map((item, i) => (
              <View key={i}>
                <TouchableOpacity
                  style={styles.faqItem}
                  onPress={() => toggleExpand(i)}
                  activeOpacity={0.7}
                >
                  <View style={styles.faqHeader}>
                    <Text style={[styles.faqQuestion, expanded === i && styles.faqQuestionActive]}>
                      {item.q}
                    </Text>
                    <View style={[styles.faqIconBox, expanded === i && styles.faqIconBoxActive]}>
                      {expanded === i ? (
                        <IconChevronUp size={18} color="#0EA5E9" />
                      ) : (
                        <IconChevronDown size={18} color="#9CA3AF" />
                      )}
                    </View>
                  </View>
                  {expanded === i && (
                    <View style={styles.faqBody}>
                      <Text style={styles.faqAnswer}>{item.a}</Text>
                    </View>
                  )}
                </TouchableOpacity>
                {i < FAQ.length - 1 && <View style={styles.divider} />}
              </View>
            ))}
          </View>
        </Animated.View>

        <Animated.View entering={FadeInUp.duration(600).delay(300).springify()}>
          <TouchableOpacity style={styles.reportBtn} activeOpacity={0.8}>
            <View style={styles.reportIconWrap}>
              <IconMessageSquare size={20} color="#FFFFFF" />
            </View>
            <Text style={styles.reportBtnText}>Report a Technical Issue</Text>
          </TouchableOpacity>
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}

function ContactCard({ icon, bg, label, onPress }) {
  return (
    <TouchableOpacity style={styles.contactCard} onPress={onPress} activeOpacity={0.7}>
      <View style={[styles.contactIcon, { backgroundColor: bg }]}>{icon}</View>
      <Text style={styles.contactLabel}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAFAFA' },
  scrollContent: { padding: 24, paddingBottom: 60 },
  
  header: { marginBottom: 40, alignItems: 'center', paddingTop: 10 },
  headerIconWrap: { 
    width: 72, height: 72, borderRadius: 36, backgroundColor: '#EDE9FE', 
    justifyContent: 'center', alignItems: 'center', marginBottom: 16,
    shadowColor: '#8B5CF6', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.15, shadowRadius: 12, elevation: 8
  },
  title: { fontSize: 28, fontWeight: '900', color: '#111827', letterSpacing: -0.5 },
  subtitle: { fontSize: 15, color: '#6B7280', marginTop: 6, fontWeight: '500' },

  section: { marginBottom: 36 },
  contactSection: { marginBottom: 40 },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 16, marginLeft: 8 },
  
  contactGrid: { flexDirection: 'row', gap: 16 },
  contactCard: {
    flex: 1, backgroundColor: '#FFFFFF', borderRadius: 24,
    paddingVertical: 20, paddingHorizontal: 10, alignItems: 'center', 
    borderWidth: 1, borderColor: '#F3F4F6',
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.04, shadowRadius: 12, elevation: 2,
  },
  contactIcon: { width: 52, height: 52, borderRadius: 26, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  contactLabel: { fontSize: 14, fontWeight: '700', color: '#111827' },

  faqCard: {
    backgroundColor: '#FFFFFF', borderRadius: 24,
    borderWidth: 1, borderColor: '#F3F4F6',
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.04, shadowRadius: 16, elevation: 2,
    overflow: 'hidden'
  },
  faqItem: { backgroundColor: '#FFFFFF' },
  faqHeader: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', padding: 20,
  },
  faqQuestion: { flex: 1, fontSize: 15, fontWeight: '700', color: '#111827', paddingRight: 16, lineHeight: 22 },
  faqQuestionActive: { color: '#0EA5E9' },
  faqIconBox: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#F3F4F6', justifyContent: 'center', alignItems: 'center' },
  faqIconBoxActive: { backgroundColor: '#E0F2FE' },
  faqBody: { paddingHorizontal: 20, paddingBottom: 24, paddingTop: 4 },
  faqAnswer: { fontSize: 14, color: '#6B7280', lineHeight: 22 },
  
  divider: { height: 1, backgroundColor: '#F3F4F6', marginHorizontal: 20 },

  reportBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    padding: 16, borderRadius: 20, backgroundColor: '#111827', gap: 12,
    shadowColor: '#000', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.15, shadowRadius: 12, elevation: 6,
  },
  reportIconWrap: { width: 36, height: 36, borderRadius: 18, backgroundColor: 'rgba(255,255,255,0.1)', justifyContent: 'center', alignItems: 'center' },
  reportBtnText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700', letterSpacing: 0.5 },
});
