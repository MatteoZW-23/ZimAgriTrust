import React, { useEffect, useState } from "react";
import { Text, TextInput, TouchableOpacity, View } from "react-native";
import { 
  Lock as IconLock, 
  CheckCircle2 as IconCheckCircle, 
  ChevronUp as IconChevronUp, 
  ChevronDown as IconChevronDown,
  DollarSign as IconDollar
} from 'lucide-react-native';

import { confirmDelivery, getTransactions, submitReview, getOrderReviews } from "../api";
import { appStyles, theme } from "../styles";

export function TransactionsScreen({ token, profile }) {
  const [transactions, setTransactions] = useState([]);
  const [codes, setCodes] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [reviewInputs, setReviewInputs] = useState({});
  const [reviewsByOrder, setReviewsByOrder] = useState({});

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

  async function loadReviews(orderId) {
    try {
      const reviews = await getOrderReviews(token, orderId);
      setReviewsByOrder((prev) => ({ ...prev, [orderId]: reviews || [] }));
    } catch {
      setReviewsByOrder((prev) => ({ ...prev, [orderId]: [] }));
    }
  }

  async function handleReview(orderId) {
    const input = reviewInputs[orderId] || { rating: "5", comment: "" };
    try {
      await submitReview(token, orderId, {
        rating: Number(input.rating || 5),
        comment: input.comment || null,
      });
      setNotice("Review submitted successfully.");
      await loadReviews(orderId);
    } catch (error) {
      setNotice(error.message || "Failed to submit review");
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
        const orderId = transaction.id;
        const statusColor = transaction.escrow_state === "DISPUTED" ? "red" : "#2f6f42";
        
        return (
          <TouchableOpacity key={transaction.id} style={appStyles.card} onPress={async () => {
            const nextId = isExpanded ? null : transaction.id;
            setExpandedId(nextId);
            if (nextId) await loadReviews(nextId);
          }}>
            <View style={appStyles.row}>
              <Text style={appStyles.cardTitle}>{isFarmer ? "Outgoing Supply" : "Order"} #{transaction.listing_id}</Text>
              <View style={appStyles.row}>
                <View style={[appStyles.badge, { backgroundColor: statusColor, flexDirection: 'row', alignItems: 'center', gap: 4 }]}>
                  {transaction.escrow_state === "ESCROW" ? (
                    <>
                      <IconLock size={12} color="#FFF" />
                      <Text style={{ color: '#FFF', fontSize: 11, fontWeight: '700' }}>Escrow</Text>
                    </>
                  ) : transaction.escrow_state === "COMPLETED" ? (
                    <>
                      <IconCheckCircle size={12} color="#FFF" />
                      <Text style={{ color: '#FFF', fontSize: 11, fontWeight: '700' }}>Payout Released</Text>
                    </>
                  ) : (
                    <Text style={{ color: '#FFF', fontSize: 11, fontWeight: '700' }}>{transaction.escrow_state}</Text>
                  )}
                </View>
                <View style={{ marginLeft: 8, opacity: 0.5 }}>
                  {isExpanded ? <IconChevronUp size={18} color="#000" /> : <IconChevronDown size={18} color="#000" />}
                </View>
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

                <View style={{ marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: "#f0f0f0" }}>
                  <Text style={[appStyles.metricLabel, { marginBottom: 8 }]}>Fee Breakdown</Text>
                  <View style={appStyles.metricRow}>
                    <View style={appStyles.metricBox}>
                      <Text style={appStyles.metricLabel}>Gross Amount</Text>
                      <Text style={appStyles.metricValue}>${transaction.total_amount ?? transaction.amount}</Text>
                    </View>
                    <View style={appStyles.metricBox}>
                      <Text style={appStyles.metricLabel}>Platform Fee</Text>
                      <Text style={[appStyles.metricValue, { color: '#dc2626' }]}>-${transaction.platform_fee ?? 0}</Text>
                    </View>
                  </View>
                  <View style={appStyles.metricRow}>
                    <View style={appStyles.metricBox}>
                      <Text style={appStyles.metricLabel}>Seller Payout</Text>
                      <Text style={[appStyles.metricValue, { color: '#16a34a' }]}>${transaction.seller_payout ?? 0}</Text>
                    </View>
                    <View style={appStyles.metricBox}>
                      <Text style={appStyles.metricLabel}>Transport Fee</Text>
                      <Text style={appStyles.metricValue}>${transaction.transport_fee ?? 0}</Text>
                    </View>
                  </View>
                </View>

                {isFarmer && transaction.escrow_state === "ESCROW" && (
                  <View style={[appStyles.emptyState, { marginTop: 12, padding: 12, backgroundColor: "rgba(47,111,66,0.1)", flexDirection: 'row', alignItems: 'flex-start', gap: 10 }]}>
                    <IconDollar size={20} color="#214027" />
                    <Text style={{ flex: 1, fontSize: 13, color: "#214027", lineHeight: 18 }}>Your payment is currently held by ZimAgritrust. Once the buyer confirms delivery, funds will reflect in your balance.</Text>
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

                {transaction.status === "COMPLETED" && (
                  <View style={{ marginTop: 16, borderTopWidth: 1, borderTopColor: "#eee", paddingTop: 16 }}>
                    <Text style={appStyles.metricLabel}>Rate Counterparty (1-5)</Text>
                    <View style={appStyles.rowSpaced}>
                      <TextInput
                        style={[appStyles.inputSmall, { width: 70 }]}
                        keyboardType="numeric"
                        value={reviewInputs[orderId]?.rating || "5"}
                        onChangeText={(v) =>
                          setReviewInputs((prev) => ({
                            ...prev,
                            [orderId]: { ...(prev[orderId] || {}), rating: v },
                          }))
                        }
                      />
                      <TouchableOpacity
                        style={[appStyles.button, { marginBottom: 0, paddingVertical: 10, marginLeft: 8 }]}
                        onPress={() => handleReview(orderId)}
                      >
                        <Text style={appStyles.buttonText}>Submit Review</Text>
                      </TouchableOpacity>
                    </View>
                    <TextInput
                      style={[appStyles.input, { marginTop: 8 }]}
                      placeholder="Write optional review comment"
                      value={reviewInputs[orderId]?.comment || ""}
                      onChangeText={(v) =>
                        setReviewInputs((prev) => ({
                          ...prev,
                          [orderId]: { ...(prev[orderId] || {}), comment: v },
                        }))
                      }
                    />
                    {(reviewsByOrder[orderId] || []).map((r) => (
                      <View key={r.id} style={[appStyles.emptyState, { marginTop: 8, padding: 10 }]}>
                        <Text style={{ fontWeight: "700" }}>Rating: {r.rating}/5</Text>
                        <Text style={appStyles.muted}>{r.comment || "No comment"}</Text>
                      </View>
                    ))}
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
