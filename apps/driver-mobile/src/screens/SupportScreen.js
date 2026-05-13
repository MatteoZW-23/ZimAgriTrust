import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  SafeAreaView, Linking, LayoutAnimation, Platform, UIManager,
} from 'react-native';
import {
  HelpCircle as IconHelpCircle, MessageCircle as IconMessageCircle, 
  Mail as IconMail, Phone as IconPhone,
  ChevronDown as IconChevronDown, ChevronUp as IconChevronUp, 
  ExternalLink as IconExternalLink, MessageSquare as IconMessageSquare,
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
        <View style={styles.header}>
          <Text style={styles.title}>Help & Support</Text>
          <Text style={styles.subtitle}>We're here to help you succeed</Text>
        </View>

        <View style={styles.contactSection}>
          <Text style={styles.sectionTitle}>Get in Touch</Text>
          <View style={styles.contactGrid}>
            <ContactCard
              icon={<IconMessageCircle size={24} color="#25D366" />}
              label="WhatsApp"
              onPress={handleContactWhatsApp}
            />
            <ContactCard
              icon={<IconPhone size={24} color="#0EA5E9" />}
              label="Call Us"
              onPress={handleCallSupport}
            />
            <ContactCard
              icon={<IconMail size={24} color="#EF4444" />}
              label="Email"
              onPress={handleContactEmail}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Frequently Asked Questions</Text>
          {FAQ.map((item, i) => (
            <TouchableOpacity
              key={i}
              style={styles.faqItem}
              onPress={() => toggleExpand(i)}
              activeOpacity={0.7}
            >
              <View style={styles.faqHeader}>
                <Text style={styles.faqQuestion}>{item.q}</Text>
                {expanded === i ? (
                  <IconChevronUp size={18} color={theme.colors.sky} />
                ) : (
                  <IconChevronDown size={18} color="#999" />
                )}
              </View>
              {expanded === i && (
                <View style={styles.faqBody}>
                  <Text style={styles.faqAnswer}>{item.a}</Text>
                </View>
              )}
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={styles.reportBtn}>
          <IconMessageSquare size={20} color={theme.colors.sky} />
          <Text style={styles.reportBtnText}>Report a Technical Issue</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

function ContactCard({ icon, label, onPress }) {
  return (
    <TouchableOpacity style={styles.contactCard} onPress={onPress}>
      <View style={styles.contactIcon}>{icon}</View>
      <Text style={styles.contactLabel}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  scrollContent: { padding: 20 },
  
  header: { marginBottom: 32 },
  title: { fontSize: 24, fontWeight: '900', color: theme.colors.dark },
  subtitle: { fontSize: 14, color: '#666', marginTop: 4 },

  section: { marginBottom: 32 },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: '#BBB', textTransform: 'uppercase', marginBottom: 16, marginLeft: 4 },
  
  contactSection: { marginBottom: 40 },
  contactGrid: { flexDirection: 'row', gap: 12 },
  contactCard: {
    flex: 1, backgroundColor: '#FFF', borderRadius: 20,
    padding: 16, alignItems: 'center', borderWidth: 1, borderColor: '#F0F0F0',
    ...theme.shadows.xs,
  },
  contactIcon: { marginBottom: 8 },
  contactLabel: { fontSize: 12, fontWeight: '700', color: theme.colors.dark },

  faqItem: {
    backgroundColor: '#FFF', borderRadius: 16, marginBottom: 10,
    borderWidth: 1, borderColor: '#F0F0F0', overflow: 'hidden',
  },
  faqHeader: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', padding: 16,
  },
  faqQuestion: { flex: 1, fontSize: 14, fontWeight: '700', color: theme.colors.dark, paddingRight: 10 },
  faqBody: { paddingHorizontal: 16, paddingBottom: 16 },
  faqAnswer: { fontSize: 13, color: '#666', lineHeight: 20 },

  reportBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    padding: 18, borderRadius: 18, backgroundColor: '#E0F2FE', gap: 10,
    marginBottom: 40,
  },
  reportBtnText: { color: '#0EA5E9', fontSize: 15, fontWeight: '800' },
});
