import React from "react";
import { SafeAreaView, StatusBar } from "react-native";
import AppShell from "./src/AppShell";

export default function App() {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: "#f6f0de" }}>
      <StatusBar barStyle="dark-content" />
      <AppShell />
    </SafeAreaView>
  );
}
