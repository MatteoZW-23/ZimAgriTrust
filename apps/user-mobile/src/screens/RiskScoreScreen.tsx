import React, { useEffect, useState } from "react";
import { Text, View } from "react-native";

import { getProfile } from "../api";
import { appStyles } from "../styles";

export function RiskScoreScreen({ token, profile }) {
  const [latestProfile, setLatestProfile] = useState(profile);

  useEffect(() => {
    if (!token) {
      setLatestProfile(null);
      return;
    }
    getProfile(token).then(setLatestProfile).catch(() => setLatestProfile(null));
  }, [token, profile]);

  return (
    <View style={appStyles.panel}>
      <Text style={appStyles.panelTitle}>Trust Rating</Text>
      <Text style={appStyles.panelLead}>Your rating goes up when you complete sales and down if there are problems.</Text>
      {!latestProfile ? <View style={appStyles.emptyState}><Text style={appStyles.muted}>Log in to view trust and risk scores.</Text></View> : null}
      {latestProfile ? (
        <>
          <View style={appStyles.card}>
            <Text style={appStyles.cardTitle}>{latestProfile.name}</Text>
            <Text style={appStyles.cardMeta}>{latestProfile.role}</Text>
            <View style={appStyles.metricRow}>
              <View style={appStyles.metricBox}>
                <Text style={appStyles.metricLabel}>Trust Score</Text>
                <Text style={appStyles.metricValue}>{Math.round(latestProfile.trust_score)}</Text>
              </View>
              <View style={appStyles.metricBox}>
                <Text style={appStyles.metricLabel}>Risk Score</Text>
                <Text style={appStyles.metricValue}>{Math.round(latestProfile.risk_score)}</Text>
              </View>
            </View>
            <View style={appStyles.metricRow}>
              <View style={appStyles.metricBox}>
                <Text style={appStyles.metricLabel}>Suspended</Text>
                <Text style={appStyles.metricValue}>{latestProfile.is_suspended ? "Yes" : "No"}</Text>
              </View>
              <View style={appStyles.metricBox}>
                <Text style={appStyles.metricLabel}>Max Products</Text>
                <Text style={appStyles.metricValue}>{latestProfile.listing_limit}</Text>
              </View>
            </View>
          </View>
        </>
      ) : null}
    </View>
  );
}
