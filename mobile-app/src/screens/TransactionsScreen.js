import React, { useEffect, useState } from "react";
import { Text, TextInput, TouchableOpacity, View } from "react-native";

import { confirmDelivery, getTransactions } from "../api";
import { appStyles } from "../styles";

export function TransactionsScreen({ token, profile }) {
  const [transactions, setTransactions] = useState([]);
  const [codes, setCodes] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    setExpandedId(null);
    refresh();
  }, [token]);

  function refresh() {
    if (!token) {
      setTransactions([]);
      return;
    }
    getTransactions(token)
      .then(setTransactions)
      .catch(() => setTransactions([]));
  }

  async function handleConfirm(txId) {
    const code = codes[txId];
    if (!code) return setNotice("Enter completion code first.");
    
    setSubmitting(true);
    try {
      await confirmDelivery(token, txId, code);
      setNotice(`Transaction #${txId} completed.`);
      refresh();
    } catch (error) {
      setNotice(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <View style={appStyles.panel}>
      <Text style={appStyles.panelTitle}>Transactions</Text>
      <Text style={appStyles.panelLead}>Watch escrow state as deals move from accepted offers to delivery confirmation.</Text>
      
      {notice ? (
        <View style={[appStyles.card, { backgroundColor: "#fef8e7" }]}>
          <Text style={[appStyles.cardTitle, { fontSize: 14 }]}>{notice}</Text>
          <TouchableOpacity onPress={() => setNotice(null)} style={{ marginTop: 8 }}>
            <Text style={{ color: "#2f6f42", fontWeight: "700" }}>Dismiss</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {!token ? <View style={appStyles.emptyState}><Text style={appStyles.muted}>Log in to load transactions.</Text></View> : null}
      
      {transactions.map((transaction) => {
        const canConfirm = transaction.escrow_state === "ESCROW" || transaction.escrow_state === "DELIVERED";
        const isFarmer = profile?.role === "FARMER";
        const isExpanded = expandedId === transaction.id;
        const statusColor = transaction.escrow_state === "DISPUTED" ? "red" : "#2f6f42";
        
        return (
          <TouchableOpacity key={transaction.id} style={appStyles.card} onPress={() => setExpandedId(isExpanded ? null : transaction.id)}>
            <View style={appStyles.row}>
              <Text style={appStyles.cardTitle}>{isFarmer ? "Outgoing Supply" : "Order"} #{transaction.listing_id}</Text>
              <View style={appStyles.row}>
                <Text style={[appStyles.badge, { backgroundColor: statusColor }]}>
                  {transaction.escrow_state === "ESCROW" ? "🔒 Escrow" : 
                   transaction.escrow_state === "COMPLETED" ? "✅ Payout Released" :
                   transaction.escrow_state}
                </Text>
                <Text style={{ marginLeft: 8, fontSize: 16, opacity: 0.5 }}>{isExpanded ? "▲" : "▼"}</Text>
              </View>
            </View>

            {isExpanded && (
              <View style={{ marginTop: 12 }}>
                <View style={[appStyles.metricRow, { borderTopWidth: 1, borderTopColor: "#f0f0f0", paddingTop: 12 }]}>
                  <View style={appStyles.metricBox}>
                    <Text style={appStyles.metricLabel}>{isFarmer ? "Your Payout" : "Total Cost"}</Text>
                    <Text style={appStyles.metricValue}>${transaction.amount}</Text>
                  </View>
                  <View style={appStyles.metricBox}>
                    <Text style={appStyles.metricLabel}>Platform Status</Text>
                    <Text style={appStyles.metricValue}>{transaction.status}</Text>
                  </View>
                </View>

                {isFarmer && transaction.escrow_state === "ESCROW" && (
                  <View style={[appStyles.emptyState, { marginTop: 12, padding: 12, backgroundColor: "rgba(47,111,66,0.1)" }]}>
                    <Text style={{ fontSize: 13, color: "#214027", lineHeight: 18 }}>💰 Your payment is currently held by AgriTrust. Once the buyer confirms delivery, funds will reflect in your balance.</Text>
                  </View>
                )}

                {!isFarmer && canConfirm && (
                  <View style={{ marginTop: 16, borderTopWidth: 1, borderTopColor: "#eee", paddingTop: 16 }}>
                    <Text style={appStyles.metricLabel}>Enter Code to Release Funds to Farmer</Text>
                    <View style={appStyles.rowSpaced}>
                      <TextInput 
                        style={[appStyles.inputSmall, { flex: 1 }]} 
                        placeholder="Security Code"
                        value={codes[transaction.id] || ""}
                        onChangeText={(v) => setCodes(c => ({ ...c, [transaction.id]: v }))}
                      />
                      <TouchableOpacity 
                        style={[appStyles.button, { marginBottom: 0, paddingVertical: 10, marginLeft: 8 }]} 
                        onPress={() => handleConfirm(transaction.id)}
                        disabled={submitting}
                      >
                        <Text style={appStyles.buttonText}>{submitting ? "..." : "Release Payout"}</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}
              </View>
            )}
          </TouchableOpacity>
        );
      })}
      
      {token && transactions.length === 0 ? <View style={appStyles.emptyState}><Text style={appStyles.muted}>No transactions found for this account.</Text></View> : null}
    </View>
  );
}
