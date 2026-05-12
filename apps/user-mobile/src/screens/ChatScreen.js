import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity, SafeAreaView,
  TextInput, ActivityIndicator, Alert, Image, KeyboardAvoidingView,
  Platform, ScrollView
} from 'react-native';
import { Send, Paperclip, Phone, Video, Info, ChevronLeft } from 'lucide-react-native';
import { theme } from '../styles';
import { getConversations, getMessages, sendMessage } from '../api';
import * as ImagePicker from 'expo-image-picker';

export default function ChatScreen({ route, navigation }) {
  const { token, conversationId, otherUser } = route.params || {};
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [otherUserInfo, setOtherUserInfo] = useState(otherUser || { full_name: 'User' });
  const [isTyping, setIsTyping] = useState(false);
  const flatListRef = useRef(null);

  const fetchMessages = useCallback(async () => {
    if (!conversationId) return;
    
    try {
      setLoading(true);
      const data = await getMessages(token, conversationId);
      setMessages(Array.isArray(data) ? data : data?.messages || []);
    } catch (error) {
      console.warn('Failed to fetch messages:', error);
      // Show demo messages for development
      setMessages([
        {
          id: '1',
          sender_id: 'other',
          message: 'Hi! Is the maize still available?',
          timestamp: '2026-05-03T10:00:00Z',
          sender_name: otherUserInfo.full_name
        },
        {
          id: '2',
          sender_id: 'me',
          message: 'Yes, I have 500kg available. When can you pick up?',
          timestamp: '2026-05-03T10:05:00Z',
          sender_name: 'You'
        },
        {
          id: '3',
          sender_id: 'other',
          message: 'Great! I can come tomorrow morning. What\'s your location?',
          timestamp: '2026-05-03T10:10:00Z',
          sender_name: otherUserInfo.full_name
        }
      ]);
    } finally {
      setLoading(false);
    }
  }, [conversationId, token, otherUserInfo.full_name]);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  const handleSend = async () => {
    if (!newMessage.trim() && attachments.length === 0) return;

    try {
      setSending(true);
      
      // Add message optimistically
      const optimisticMessage = {
        id: 'temp_' + Date.now(),
        sender_id: 'me',
        message: newMessage.trim(),
        timestamp: new Date().toISOString(),
        sender_name: 'You',
        attachments: attachments.map(att => ({ uri: att.uri, type: att.type })),
        status: 'sending'
      };
      
      setMessages(prev => [...prev, optimisticMessage]);
      
      // Send to server
      const response = await sendMessage(token, conversationId, newMessage.trim(), attachments);
      
      // Update with server response
      setMessages(prev => prev.map(msg => 
        msg.id === optimisticMessage.id 
          ? { ...msg, id: response.id, status: 'sent' }
          : msg
      ));
      
      setNewMessage('');
      setAttachments([]);
      
      // Scroll to bottom
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
      
    } catch (error) {
      console.error('Failed to send message:', error);
      Alert.alert('Error', 'Failed to send message. Please try again.');
      
      // Remove optimistic message or mark as failed
      setMessages(prev => prev.map(msg => 
        msg.id?.startsWith('temp_') 
          ? { ...msg, status: 'failed' }
          : msg
      ));
    } finally {
      setSending(false);
    }
  };

  const handleAttachPhoto = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (!result.canceled) {
        setAttachments(prev => [...prev, result.assets[0]]);
      }
    } catch (error) {
      console.error('Failed to pick image:', error);
      Alert.alert('Error', 'Failed to select image');
    }
  };

  const handleTakePhoto = async () => {
    try {
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (!result.canceled) {
        setAttachments(prev => [...prev, result.assets[0]]);
      }
    } catch (error) {
      console.error('Failed to take photo:', error);
      Alert.alert('Error', 'Failed to take photo');
    }
  };

  const removeAttachment = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const renderMessage = ({ item }) => {
    const isMe = item.sender_id === 'me';
    
    return (
      <View style={[styles.messageContainer, isMe && styles.myMessage]}>
        <View style={[styles.messageBubble, isMe ? styles.myBubble : styles.otherBubble]}>
          {item.attachments && item.attachments.length > 0 && (
            <View style={styles.attachmentsContainer}>
              {item.attachments.map((attachment, index) => (
                <Image
                  key={index}
                  source={{ uri: attachment.uri }}
                  style={styles.attachmentImage}
                  resizeMode="cover"
                />
              ))}
            </View>
          )}
          {item.message && (
            <Text style={[styles.messageText, isMe && styles.myMessageText]}>
              {item.message}
            </Text>
          )}
          <View style={styles.messageFooter}>
            <Text style={[styles.messageTime, isMe && styles.myMessageTime]}>
              {formatTime(item.timestamp)}
            </Text>
            {item.status && (
              <Text style={[styles.messageStatus, isMe && styles.myMessageStatus]}>
                {item.status === 'sent' ? '✓' : item.status === 'failed' ? '✗' : '⏳'}
              </Text>
            )}
          </View>
        </View>
      </View>
    );
  };

  const renderAttachment = (attachment, index) => (
    <View key={index} style={styles.attachmentPreview}>
      <Image source={{ uri: attachment.uri }} style={styles.attachmentThumb} />
      <TouchableOpacity
        style={styles.removeAttachment}
        onPress={() => removeAttachment(index)}
      >
        <Text style={styles.removeText}>×</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <ChevronLeft size={24} color={theme.colors.dark} />
        </TouchableOpacity>
        <View style={styles.headerInfo}>
          <Text style={styles.headerName}>{otherUserInfo.full_name}</Text>
          <Text style={styles.headerStatus}>{isTyping ? 'Typing...' : 'Active now'}</Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.actionButton}>
            <Phone size={20} color={theme.colors.sky} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Video size={20} color={theme.colors.sky} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Info size={20} color={theme.colors.sky} />
          </TouchableOpacity>
        </View>
      </View>

      <KeyboardAvoidingView 
        style={styles.flex} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.colors.sky} />
            <Text style={styles.loadingText}>Loading messages...</Text>
          </View>
        ) : (
          <FlatList
            ref={flatListRef}
            data={messages}
            renderItem={renderMessage}
            keyExtractor={(item) => item.id}
            style={styles.messagesList}
            contentContainerStyle={styles.messagesContainer}
            showsVerticalScrollIndicator={false}
            onContentSizeChange={() => {
              flatListRef.current?.scrollToEnd({ animated: true });
            }}
          />
        )}

        {/* Attachments Preview */}
        {attachments.length > 0 && (
          <ScrollView horizontal style={styles.attachmentsPreview}>
            {attachments.map((attachment, index) => renderAttachment(attachment, index))}
          </ScrollView>
        )}

        <View style={styles.inputContainer}>
          <TouchableOpacity 
            style={styles.attachButton} 
            onPress={handleAttachPhoto}
            disabled={sending}
          >
            <Paperclip size={20} color="#666" />
          </TouchableOpacity>
          
          <TextInput
            style={styles.textInput}
            value={newMessage}
            onChangeText={setNewMessage}
            placeholder="Type a message..."
            placeholderTextColor="#999"
            multiline
            maxLength={1000}
            editable={!sending}
          />

          <TouchableOpacity 
            style={[styles.sendButton, sending && styles.sendButtonDisabled]}
            onPress={handleSend}
            disabled={!newMessage.trim() && attachments.length === 0 || sending}
          >
            {sending ? (
              <ActivityIndicator size="small" color="#FFF" />
            ) : (
              <Send size={18} color="#FFF" />
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  flex: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  backButton: { padding: 4 },
  headerInfo: { flex: 1, marginLeft: 12 },
  headerName: { fontSize: 16, fontWeight: '700', color: theme.colors.dark },
  headerStatus: { fontSize: 12, color: '#4CAF50', marginTop: 2 },
  headerActions: { flexDirection: 'row', gap: 12 },
  actionButton: { padding: 8 },
  
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: { color: '#999', marginTop: 12, fontWeight: '600' },
  
  messagesList: { flex: 1 },
  messagesContainer: { padding: 16 },
  
  messageContainer: {
    marginBottom: 16,
    flexDirection: 'row',
  },
  myMessage: {
    justifyContent: 'flex-end',
  },
  messageBubble: {
    maxWidth: '75%',
    borderRadius: 20,
    padding: 12,
    ...theme.shadows.xs,
  },
  myBubble: {
    backgroundColor: theme.colors.sky,
    borderBottomRightRadius: 4,
  },
  otherBubble: {
    backgroundColor: '#FFF',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  
  attachmentsContainer: { marginBottom: 8 },
  attachmentImage: {
    width: 200,
    height: 150,
    borderRadius: 12,
  },
  
  messageText: {
    fontSize: 15,
    lineHeight: 20,
    color: theme.colors.dark,
  },
  myMessageText: { color: '#FFF' },
  
  messageFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginTop: 4,
    gap: 4,
  },
  messageTime: {
    fontSize: 11,
    color: '#999',
    fontWeight: '500',
  },
  myMessageTime: { color: 'rgba(255,255,255,0.7)' },
  messageStatus: {
    fontSize: 12,
    fontWeight: '600',
  },
  myMessageStatus: { color: 'rgba(255,255,255,0.7)' },
  
  attachmentsPreview: {
    backgroundColor: '#FFF',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  attachmentPreview: {
    marginRight: 8,
    position: 'relative',
  },
  attachmentThumb: {
    width: 60,
    height: 60,
    borderRadius: 8,
  },
  removeAttachment: {
    position: 'absolute',
    top: -4,
    right: -4,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#FF5252',
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeText: { color: '#FFF', fontSize: 14, fontWeight: 'bold' },
  
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#FFF',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
    gap: 12,
  },
  attachButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
  },
  textInput: {
    flex: 1,
    fontSize: 15,
    lineHeight: 20,
    maxHeight: 100,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#F8F9FA',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  sendButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: theme.colors.sky,
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 40,
    height: 40,
  },
  sendButtonDisabled: {
    backgroundColor: '#CCC',
  },
});
