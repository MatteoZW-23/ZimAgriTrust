//
//  ZimAgriTrustApp.swift
//  ZimAgriTrust
//
//  Main app entry point with notification setup
//

import SwiftUI
import UserNotifications

@main
struct ZimAgriTrustApp: App {
    @StateObject private var authService = AuthService.shared
    @StateObject private var notificationService = NotificationService.shared
    
    init() {
        setupNotifications()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authService)
                .environmentObject(notificationService)
                .onAppear {
                    requestNotificationPermission()
                }
        }
    }
    
    private func setupNotifications() {
        UNUserNotificationCenter.current().delegate = notificationService
    }
    
    private func requestNotificationPermission() {
        Task {
            let granted = await notificationService.requestAuthorization()
            print("Notification permission granted: \(granted)")
        }
    }
}
