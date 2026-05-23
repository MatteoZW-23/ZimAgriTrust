//
//  ContentView.swift
//  ZimAgriDriver
//
//  Main app entry point with authentication flow
//

import SwiftUI

struct ContentView: View {
    @StateObject private var driverService = DriverService.shared
    
    var body: some View {
        Group {
            if driverService.isAuthenticated {
                MainTabView()
            } else {
                OTPLoginView()
            }
        }
    }
}

struct MainTabView: View {
    @StateObject private var driverService = DriverService.shared
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            DeliveriesTabView()
                .tabItem {
                    Label("Deliveries", systemImage: "truck.box")
                }
                .tag(0)
            
            ProfileTabView()
                .tabItem {
                    Label("Profile", systemImage: "person.circle")
                }
                .tag(1)
        }
        .accentColor(.green)
    }
}

#Preview {
    ContentView()
}
