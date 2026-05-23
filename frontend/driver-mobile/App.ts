import React from "react";
import { Platform, SafeAreaView, StatusBar, Text, View } from "react-native";
import AppShell from "./src/AppShell";

class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  componentDidCatch(error, info) { console.error("App crash:", error, info); }
  render() {
    if (this.state.hasError) {
      return (
        <View style={{ flex: 1, justifyContent: "center", alignItems: "center", padding: 20, backgroundColor: "#FFF", minHeight: Platform.OS === "web" ? "100vh" : undefined }}>
          <Text style={{ fontSize: 18, fontWeight: "bold", color: "red", marginBottom: 10 }}>Something went wrong</Text>
          <Text style={{ fontSize: 14, color: "#666", textAlign: "center" }}>{String(this.state.error?.message || this.state.error)}</Text>
        </View>
      );
    }
    return this.props.children;
  }
}

function AppWrapper() {
  if (Platform.OS === "web") {
    return (
      <View style={{ flex: 1, minHeight: "100vh" }}>
        <AppShell />
      </View>
    );
  }

  const { GestureHandlerRootView } = require("react-native-gesture-handler");
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaView style={{ flex: 1, backgroundColor: "#f6f0de" }}>
        <StatusBar barStyle="dark-content" />
        <AppShell />
      </SafeAreaView>
    </GestureHandlerRootView>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppWrapper />
    </ErrorBoundary>
  );
}
