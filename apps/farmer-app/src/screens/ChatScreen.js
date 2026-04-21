import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { theme } from '../styles';

export default function ChatScreen({ navigation, route }) {
  const { contact = 'Tendai M.' } = route.params || {};
  const [msg, setMsg] = useState('');
  const [messages, setMessages] = useState([
    { id: 1, text: 'Hi Tendai, interested in your maize. Can we discuss pricing?', sender: 'buyer', time: '10:32 AM' },
    { id: 2, text: 'Hi! Yes, I have Grade A maize available. $0.43/kg for bulk.', sender: 'farmer', time: '10:34 AM' },
    { id: 3, text: 'Perfect. We need 5,000kg per month.', sender: 'buyer', time: '10:35 AM' },
  ]);

  const send = () => {
    if (!msg) return;
    setMessages([...messages, { id: Date.now(), text: msg, sender: 'buyer', time: 'Just now' }]);
    setMsg('');
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}><Text style={styles.backBtn}>←</Text></TouchableOpacity>
        <View style={styles.headerTitleBox}>
          <Text style={styles.headerTitle}>{contact}</Text>
          <Text style={styles.headerSub}>🟢 Online • ⭐ 4.9 Farmer</Text>
        </View>
        <TouchableOpacity><Text style={{ fontSize: 24 }}>⚙️</Text></TouchableOpacity>
      </View>

      <ScrollView style={styles.chatArea} contentContainerStyle={{ padding: 20 }}>
          <Text style={styles.dateDivider}>Today</Text>
          {messages.map((m) => (
            <View key={m.id} style={[styles.bubbleWrap, m.sender === 'buyer' ? styles.bubbleRight : styles.bubbleLeft]}>
                 <View style={[styles.bubble, m.sender === 'buyer' ? styles.bubbleBuyer : styles.bubbleFarmer]}>
                    <Text style={[styles.msgText, m.sender === 'buyer' && { color: '#FFF' }]}>{m.text}</Text>
                 </View>
                 <Text style={styles.msgTime}>{m.time}</Text>
            </View>
          ))}
      </ScrollView>

      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <View style={styles.inputRow}>
            <TouchableOpacity style={styles.attachBtn}><Text style={{ fontSize: 20 }}>📎</Text></TouchableOpacity>
            <TouchableOpacity style={styles.attachBtn}><Text style={{ fontSize: 20 }}>📷</Text></TouchableOpacity>
            <View style={styles.inputBox}>
                <TextInput
                  style={styles.input}
                  placeholder="Type a message..."
                  value={msg}
                  onChangeText={setMsg}
                />
            </View>
            <TouchableOpacity style={styles.sendBtn} onPress={send}>
                <Text style={styles.sendIcon}>🚀</Text>
            </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF' },
  header: { padding: 20, paddingTop: 60, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: '#F5F5F5' },
  backBtn: { fontSize: 24, fontWeight: '700', color: theme.colors.sky, width: 40 },
  headerTitleBox: { flex: 1 },
  headerTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.black },
  headerSub: { fontSize: 12, color: theme.colors.green, fontWeight: '700', marginTop: 2 },
  chatArea: { flex: 1, backgroundColor: '#FAFAFA' },
  dateDivider: { textAlign: 'center', fontSize: 12, fontWeight: '800', color: '#999', marginVertical: 24, textTransform: 'uppercase' },
  bubbleWrap: { marginBottom: 20, maxWidth: '85%' },
  bubbleLeft: { alignSelf: 'flex-start' },
  bubbleRight: { alignSelf: 'flex-end' },
  bubble: { padding: 16, borderRadius: 20 },
  bubbleFarmer: { backgroundColor: '#FFF', borderBottomLeftRadius: 4, elevation: 1 },
  bubbleBuyer: { backgroundColor: theme.colors.sky, borderBottomRightRadius: 4, elevation: 1 },
  msgText: { fontSize: 15, fontWeight: '500', lineHeight: 22, color: theme.colors.black },
  msgTime: { fontSize: 11, color: '#999', marginTop: 4, alignSelf: 'flex-end', fontWeight: '700' },
  inputRow: { padding: 16, backgroundColor: '#FFF', flexDirection: 'row', alignItems: 'center', gap: 8, borderTopWidth: 1, borderTopColor: '#EEE' },
  attachBtn: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center' },
  inputBox: { flex: 1, backgroundColor: '#F5F5F5', borderRadius: 22, paddingHorizontal: 20, height: 44, justifyContent: 'center' },
  input: { fontSize: 15, color: theme.colors.black },
  sendBtn: { width: 44, height: 44, backgroundColor: theme.colors.green, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  sendIcon: { fontSize: 18 }
});
