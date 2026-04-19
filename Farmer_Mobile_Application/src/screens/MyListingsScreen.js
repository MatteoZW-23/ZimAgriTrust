import React, { useEffect, useState } from "react";
import { Text, View, TouchableOpacity, ScrollView, Alert } from "react-native";

import { getMyListings, acceptOffer } from "../api";
import { appStyles } from "../styles";

export function MyListingsScreen({ token, profile }) {
  const [listings, setListings] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [loading, setLoading] = useState(false);

  async function loadListings() {
    if (!token) return;
    try {
      const data = await getMyListings(token);
      setListings(data);
    } catch (e) {
      console.log(e);
    }
  }

  useEffect(() => {
    loadListings();
  }, [token]);

  async function handleAccept(listingId, offerId) {
    Alert.alert(
      "Confirm Acceptance",
      "By accepting this offer, an escrow transaction will be created. Proceed?",
      [
        { text: "Cancel", style: "cancel" },
        { 
          text: "Accept Offer", 
          onPress: async () => {
            setLoading(true);
            try {
              await acceptOffer(token, listingId, offerId);
              loadListings();
              Alert.alert("Success", "Offer accepted! Transaction initiated.");
            } catch (error) {
              Alert.alert("Error", error.message);
            } finally {
              setLoading(false);
            }
          } 
        }
      ]
    );
  }

  return (
    <View style={appStyles.panel}>
      <View style={appStyles.rowSpaced}>
        <View>
          <Text style={appStyles.panelTitle}>Active Proposals</Text>
          <Text style={appStyles.panelLead}>Manage your market presence and pending offers.</Text>
        </View>
        <TouchableOpacity onPress={loadListings}>
           <Text style={{ color: 'blue' }}>Refresh</Text>
        </TouchableOpacity>
      </View>

      {!token ? (
        <View style={appStyles.emptyState}>
          <Text style={appStyles.muted}>Please log in to manage your listings.</Text>
        </View>
      ) : (
        <ScrollView>
          {listings.map((listing) => {
            const isExpanded = expandedId === listing.id;
            const isDemand = listing.type === "DEMAND";
            const pendingOffers = listing.offers.filter(o => o.status === 'pending');

            return (
              <View key={listing.id} style={[appStyles.card, isExpanded && { borderColor: '#2f6f42', borderWidth: 1 }]}>
                <TouchableOpacity 
                  onPress={() => setExpandedId(isExpanded ? null : listing.id)}
                  style={{ width: '100%' }}
                >
                  <View style={appStyles.rowSpaced}>
                    <View style={{ flex: 1 }}>
                        <Text style={appStyles.cardTitle}>{isDemand ? '🛒 ' : '🌽 '}{listing.crop}</Text>
                        <Text style={appStyles.cardMeta}>{listing.location} • ID #{listing.id}</Text>
                    </View>
                    <View style={{ alignItems: 'flex-end' }}>
                        <Text style={[appStyles.badge, listing.verification_status !== "APPROVED" && appStyles.badgeWarn]}>
                            {listing.verification_status}
                        </Text>
                        <Text style={{ marginTop: 4, fontWeight: '700', color: '#2f6f42' }}>
                            {pendingOffers.length} {pendingOffers.length === 1 ? 'offer' : 'offers'}
                        </Text>
                    </View>
                  </View>
                </TouchableOpacity>

                {isExpanded && (
                  <View style={{ marginTop: 12, borderTopWidth: 1, borderTopColor: '#eee', paddingTop: 12 }}>
                    <View style={appStyles.rowSpaced}>
                        <View style={appStyles.metricBox}>
                            <Text style={appStyles.metricLabel}>Total Volume</Text>
                            <Text style={appStyles.metricValue}>{listing.quantity} kg</Text>
                        </View>
                        <View style={appStyles.metricBox}>
                            <Text style={appStyles.metricLabel}>{isDemand ? 'Target Total' : 'Asking Price'}</Text>
                            <Text style={appStyles.metricValue}>${(listing.price_per_unit * listing.quantity).toFixed(0)}</Text>
                        </View>
                    </View>

                    <Text style={[appStyles.metricLabel, { marginTop: 16, marginBottom: 8 }]}>OFFERS & BIDS</Text>
                    {pendingOffers.length === 0 ? (
                        <Text style={[appStyles.muted, { fontStyle: 'italic' }]}>No active offers yet. Market seekers are still viewing your listing.</Text>
                    ) : (
                        pendingOffers.map(offer => (
                            <View key={offer.id} style={{ backgroundColor: '#f9f9f9', padding: 12, borderRadius: 8, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: '#2f6f42' }}>
                                <View style={appStyles.rowSpaced}>
                                    <View>
                                        <Text style={{ fontWeight: '700', fontSize: 16, color: '#333' }}>${offer.amount.toFixed(2)}</Text>
                                        <Text style={appStyles.cardMeta}>for {offer.quantity} kg</Text>
                                    </View>
                                    <TouchableOpacity 
                                      style={[appStyles.button, { paddingVertical: 6, paddingHorizontal: 16 }]} 
                                      onPress={() => handleAccept(listing.id, offer.id)}
                                      disabled={loading}
                                    >
                                        <Text style={[appStyles.buttonText, { fontSize: 13 }]}>Accept</Text>
                                    </TouchableOpacity>
                                </View>
                                {offer.message ? <Text style={[appStyles.muted, { marginTop: 4, fontStyle: 'italic' }]}>"{offer.message}"</Text> : null}
                            </View>
                        ))
                    )}
                  </View>
                )}
              </View>
            );
          })}
          {listings.length === 0 && (
            <View style={appStyles.emptyState}>
                <Text style={appStyles.muted}>You haven't posted any active supply or demand yet.</Text>
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
}
