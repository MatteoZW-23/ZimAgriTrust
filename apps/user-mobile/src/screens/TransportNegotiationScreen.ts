import React, { useState, useEffect } from "react";
import { Text, TextInput, TouchableOpacity, View, ScrollView, StyleSheet, Alert, ActivityIndicator } from "react-native";

export default function TransportNegotiationScreen({ navigation, route }) {
  const { token, negotiationId, orderId, role = 'buyer', counterpartyName } = route.params || {};
  
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [currentOffer, setCurrentOffer] = useState(null);
  const [showOfferModal, setShowOfferModal] = useState(false);
  const [offerAmount, setOfferAmount] = useState('');
  const [offerPayer, setOfferPayer] = useState('BUYER');
  const [splitBuyer, setSplitBuyer] = useState('50');
  const [splitFarmer, setSplitFarmer] = useState('50');

  useEffect(() => {
    loadNegotiation();
  }, []);

  const loadNegotiation = async () => {
    setLoading(true);
    try {
      // TODO: Call API to load negotiation details and messages
      // For now, simulate data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setMessages([
        {
          id: 1,
          sender: 'SYSTEM',
          type: 'SYSTEM',
          content: 'Negotiation started. Initial quote: $15.00',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: 2,
          sender: 'BUYER',
          type: 'OFFER',
          content: 'I propose $12.00 paid by me',
          structuredOffer: { payer: 'BUYER', amount: 12.00 },
          timestamp: new Date(Date.now() - 1800000).toISOString(),
        },
        {
          id: 3,
          sender: 'FARMER',
          type: 'COUNTER_OFFER',
          content: 'I can do $14.00 split 50/50',
          structuredOffer: { payer: 'SPLIT', amount: 14.00, splitRatio: { buyer: 0.5, farmer: 0.5 } },
          timestamp: new Date(Date.now() - 900000).toISOString(),
        },
      ]);
      
      setCurrentOffer({
        payer: 'SPLIT',
        amount: 14.00,
        splitRatio: { buyer: 0.5, farmer: 0.5 },
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to load negotiation.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    setSending(true);
    try {
      // TODO: Call API to send message
      const message = {
        id: messages.length + 1,
        sender: role.toUpperCase(),
        type: 'TEXT',
        content: newMessage,
        timestamp: new Date().toISOString(),
      };
      
      setMessages([...messages, message]);
      setNewMessage('');
    } catch (error) {
      Alert.alert('Error', 'Failed to send message.');
    } finally {
      setSending(false);
    }
  };

  const handleSendOffer = async () => {
    if (!offerAmount || parseFloat(offerAmount) <= 0) {
      Alert.alert('Invalid Amount', 'Please enter a valid amount.');
      return;
    }

    setSending(true);
    try {
      const structuredOffer = {
        payer: offerPayer,
        amount: parseFloat(offerAmount),
      };

      if (offerPayer === 'SPLIT') {
        structuredOffer.splitRatio = {
          buyer: parseInt(splitBuyer) / 100,
          farmer: parseInt(splitFarmer) / 100,
        };
      }

      const message = {
        id: messages.length + 1,
        sender: role.toUpperCase(),
        type: 'COUNTER_OFFER',
        content: `Offer: $${parseFloat(offerAmount).toFixed(2)} paid by ${offerPayer === 'SPLIT' ? 'split' : offerPayer}`,
        structuredOffer,
        timestamp: new Date().toISOString(),
      };

      setMessages([...messages, message]);
      setCurrentOffer(structuredOffer);
      setShowOfferModal(false);
      setOfferAmount('');
    } catch (error) {
      Alert.alert('Error', 'Failed to send offer.');
    } finally {
      setSending(false);
    }
  };

  const handleAcceptOffer = async () => {
    Alert.alert(
      'Accept Offer',
      `Are you sure you want to accept this offer?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Accept',
          onPress: async () => {
            setSending(true);
            try {
              // TODO: Call API to accept offer
              const message = {
                id: messages.length + 1,
                sender: role.toUpperCase(),
                type: 'ACCEPTANCE',
                content: 'I accept this offer',
                timestamp: new Date().toISOString(),
              };
              
              setMessages([...messages, message]);
              
              Alert.alert(
                'Offer Accepted',
                'Transport fee agreement reached. Driver will be assigned shortly.',
                [
                  { text: 'OK', onPress: () => navigation.navigate('OrderDetails', { orderId, role, token }) }
                ]
              );
            } catch (error) {
              Alert.alert('Error', 'Failed to accept offer.');
            } finally {
              setSending(false);
            }
          }
        }
      ]
    );
  };

  const handleRejectOffer = async () => {
    setSending(true);
    try {
      const message = {
        id: messages.length + 1,
        sender: role.toUpperCase(),
        type: 'REJECTION',
        content: 'I cannot accept this offer',
        timestamp: new Date().toISOString(),
      };
      
      setMessages([...messages, message]);
    } catch (error) {
      Alert.alert('Error', 'Failed to reject offer.');
    } finally {
      setSending(false);
    }
  };

  const renderMessage = (message) => {
    const isOwnMessage = message.sender === role.toUpperCase();
    const isSystem = message.type === 'SYSTEM';

    if (isSystem) {
      return (
        <View key={message.id} style={styles.systemMessageContainer}>
          <Text style={styles.systemMessage}>{message.content}</Text>
        </View>
      );
    }

    if (message.type === 'OFFER' || message.type === 'COUNTER_OFFER') {
      const offer = message.structuredOffer;
      return (
        <View key={message.id} style={[
          styles.messageContainer,
          isOwnMessage ? styles.ownMessage : styles.otherMessage,
        ]}>
          <View style={styles.messageHeader}>
            <Text style={styles.messageSender}>
              {isOwnMessage ? 'You' : counterpartyName || 'Counterparty'}
            </Text>
            <Text style={styles.messageTime}>
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </Text>
          </View>
          <View style={styles.offerCard}>
            <Text style={styles.offerLabel}>Transport Fee Offer</Text>
            <Text style={styles.offerAmount}>${offer.amount.toFixed(2)}</Text>
            <Text style={styles.offerPayer}>
              Paid by: {offer.payer === 'SPLIT' ? 'Split' : offer.payer}
            </Text>
            {offer.splitRatio && (
              <Text style={styles.offerSplit}>
                Split: Buyer {Math.round(offer.splitRatio.buyer * 100)}% / Farmer {Math.round(offer.splitRatio.farmer * 100)}%
              </Text>
            )}
          </View>
          <Text style={styles.messageContent}>{message.content}</Text>
        </View>
      );
    }

    return (
      <View key={message.id} style={[
        styles.messageContainer,
        isOwnMessage ? styles.ownMessage : styles.otherMessage,
      ]}>
        <View style={styles.messageHeader}>
          <Text style={styles.messageSender}>
            {isOwnMessage ? 'You' : counterpartyName || 'Counterparty'}
          </Text>
          <Text style={styles.messageTime}>
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Text>
        </View>
        <Text style={styles.messageContent}>{message.content}</Text>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Loading negotiation...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Transport Negotiation</Text>
        <Text style={styles.headerSubtitle}>
          {counterpartyName || 'Counterparty'}
        </Text>
      </View>

      {currentOffer && (
        <View style={styles.currentOfferBanner}>
          <Text style={styles.currentOfferLabel}>Current Offer</Text>
          <Text style={styles.currentOfferAmount}>${currentOffer.amount.toFixed(2)}</Text>
          <Text style={styles.currentOfferPayer}>
            {currentOffer.payer === 'SPLIT' ? 'Split Payment' : `Paid by ${currentOffer.payer}`}
          </Text>
          <View style={styles.currentOfferActions}>
            <TouchableOpacity
              style={styles.acceptButton}
              onPress={handleAcceptOffer}
              disabled={sending}
            >
              <Text style={styles.acceptButtonText}>Accept</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.rejectButton}
              onPress={handleRejectOffer}
              disabled={sending}
            >
              <Text style={styles.rejectButtonText}>Reject</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <ScrollView style={styles.messagesContainer}>
        {messages.map(renderMessage)}
      </ScrollView>

      <View style={styles.inputContainer}>
        <TouchableOpacity
          style={styles.offerButton}
          onPress={() => setShowOfferModal(true)}
        >
          <Text style={styles.offerButtonText}>Make Offer</Text>
        </TouchableOpacity>
        
        <TextInput
          style={styles.messageInput}
          placeholder="Type a message..."
          value={newMessage}
          onChangeText={setNewMessage}
          multiline
        />
        
        <TouchableOpacity
          style={styles.sendButton}
          onPress={handleSendMessage}
          disabled={!newMessage.trim() || sending}
        >
          {sending ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.sendButtonText}>Send</Text>
          )}
        </TouchableOpacity>
      </View>

      {showOfferModal && (
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>Make an Offer</Text>
            
            <Text style={styles.modalLabel}>Amount (USD)</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="0.00"
              value={offerAmount}
              onChangeText={setOfferAmount}
              keyboardType="decimal-pad"
            />

            <Text style={styles.modalLabel}>Who Pays?</Text>
            <View style={styles.payerOptions}>
              {['BUYER', 'FARMER', 'SPLIT'].map((payer) => (
                <TouchableOpacity
                  key={payer}
                  style={[
                    styles.payerOption,
                    offerPayer === payer && styles.payerOptionSelected,
                  ]}
                  onPress={() => setOfferPayer(payer)}
                >
                  <Text style={[
                    styles.payerOptionText,
                    offerPayer === payer && styles.payerOptionTextSelected,
                  ]}>
                    {payer}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {offerPayer === 'SPLIT' && (
              <>
                <Text style={styles.modalLabel}>Split Ratio</Text>
                <View style={styles.splitContainer}>
                  <View style={styles.splitInput}>
                    <Text style={styles.splitLabel}>Buyer %</Text>
                    <TextInput
                      style={styles.splitInputField}
                      value={splitBuyer}
                      onChangeText={setSplitBuyer}
                      keyboardType="number-pad"
                    />
                  </View>
                  <View style={styles.splitInput}>
                    <Text style={styles.splitLabel}>Farmer %</Text>
                    <TextInput
                      style={styles.splitInputField}
                      value={splitFarmer}
                      onChangeText={setSplitFarmer}
                      keyboardType="number-pad"
                    />
                  </View>
                </View>
              </>
            )}

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalCancelButton}
                onPress={() => setShowOfferModal(false)}
              >
                <Text style={styles.modalCancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalSubmitButton}
                onPress={handleSendOffer}
                disabled={!offerAmount || sending}
              >
                {sending ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.modalSubmitButtonText}>Submit Offer</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#6B7280',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  currentOfferBanner: {
    backgroundColor: '#EFF6FF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#DBEAFE',
  },
  currentOfferLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#3B82F6',
    marginBottom: 4,
  },
  currentOfferAmount: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  currentOfferPayer: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 12,
  },
  currentOfferActions: {
    flexDirection: 'row',
  },
  acceptButton: {
    flex: 1,
    backgroundColor: '#10B981',
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
    marginRight: 8,
  },
  acceptButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  rejectButton: {
    flex: 1,
    backgroundColor: '#EF4444',
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
  },
  rejectButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  messagesContainer: {
    flex: 1,
    padding: 16,
  },
  systemMessageContainer: {
    alignItems: 'center',
    marginVertical: 8,
  },
  systemMessage: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    fontSize: 12,
    color: '#6B7280',
  },
  messageContainer: {
    maxWidth: '80%',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  ownMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#3B82F6',
  },
  otherMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  messageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  messageSender: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1F2937',
  },
  messageTime: {
    fontSize: 10,
    color: '#6B7280',
  },
  messageContent: {
    fontSize: 14,
    color: '#1F2937',
  },
  offerCard: {
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#FCD34D',
  },
  offerLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#92400E',
    marginBottom: 4,
  },
  offerAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 4,
  },
  offerPayer: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 2,
  },
  offerSplit: {
    fontSize: 12,
    color: '#6B7280',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    alignItems: 'flex-end',
  },
  offerButton: {
    backgroundColor: '#8B5CF6',
    borderRadius: 8,
    padding: 10,
    marginRight: 8,
    marginBottom: 4,
  },
  offerButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  messageInput: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginRight: 8,
    maxHeight: 80,
    fontSize: 14,
  },
  sendButton: {
    backgroundColor: '#3B82F6',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginBottom: 4,
  },
  sendButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContainer: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 20,
  },
  modalLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
  },
  modalInput: {
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  payerOptions: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  payerOption: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginRight: 8,
  },
  payerOptionSelected: {
    backgroundColor: '#3B82F6',
  },
  payerOptionText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  payerOptionTextSelected: {
    color: '#fff',
  },
  splitContainer: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  splitInput: {
    flex: 1,
    marginRight: 8,
  },
  splitLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  splitInputField: {
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  modalActions: {
    flexDirection: 'row',
    marginTop: 8,
  },
  modalCancelButton: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginRight: 8,
  },
  modalCancelButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  modalSubmitButton: {
    flex: 1,
    backgroundColor: '#3B82F6',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  modalSubmitButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
});
