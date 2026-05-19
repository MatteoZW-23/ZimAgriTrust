//
//  ContentView.swift
//  ZimAgriTrust
//
//  Main app entry point with authentication flow
//

import SwiftUI

struct ContentView: View {
    @StateObject private var authService = AuthService.shared
    @StateObject private var notificationService = NotificationService.shared
    
    var body: some View {
        Group {
            if authService.isAuthenticated {
                MainTabView()
                    .environmentObject(notificationService)
            } else {
                LoginView()
            }
        }
        .onAppear {
            Task {
                let granted = await notificationService.requestAuthorization()
                print("Notification permission granted: \(granted)")
            }
        }
    }
}

struct MainTabView: View {
    @StateObject private var authService = AuthService.shared
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            ListingsTabView()
                .tabItem {
                    Label("Listings", systemImage: "list.bullet")
                }
                .tag(0)
            
            MarketTabView()
                .tabItem {
                    Label("Market", systemImage: "chart.line.uptrend.xyaxis")
                }
                .tag(1)
            
            WalletTabView()
                .tabItem {
                    Label("Wallet", systemImage: "wallet.pass")
                }
                .tag(2)
            
            TransactionsTabView()
                .tabItem {
                    Label("Transactions", systemImage: "arrow.left.arrow.right")
                }
                .tag(3)
            
            ProfileTabView()
                .tabItem {
                    Label("Profile", systemImage: "person.circle")
                }
                .tag(4)
        }
        .accentColor(.green)
    }
}

#Preview {
    ContentView()
}
