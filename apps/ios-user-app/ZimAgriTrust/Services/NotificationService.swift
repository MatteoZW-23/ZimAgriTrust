//
//  NotificationService.swift
//  ZimAgriTrust
//
//  Push notification handling with APNs
//

import Foundation
import UserNotifications
import UIKit

class NotificationService: NSObject, ObservableObject {
    static let shared = NotificationService()
    
    @Published var isAuthorized = false
    @Published var deviceToken: String?
    
    private let apiClient = APIClient.shared
    
    private override init() {
        super.init()
        setupNotificationDelegate()
    }
    
    // MARK: - Setup
    
    private func setupNotificationDelegate() {
        UNUserNotificationCenter.current().delegate = self
    }
    
    // MARK: - Request Authorization
    
    func requestAuthorization() async -> Bool {
        let options: UNAuthorizationOptions = [.alert, .sound, .badge]
        
        do {
            let granted = try await UNUserNotificationCenter.current()
                .requestAuthorization(options: options)
            
            await MainActor.run {
                self.isAuthorized = granted
            }
            
            if granted {
                await registerForRemoteNotifications()
            }
            
            return granted
        } catch {
            print("Failed to request notification authorization: \(error)")
            return false
        }
    }
    
    // MARK: - Register for Remote Notifications
    
    private func registerForRemoteNotifications() async {
        await MainActor.run {
            UIApplication.shared.registerForRemoteNotifications()
        }
    }
    
    // MARK: - Handle Device Token
    
    func didRegisterForRemoteNotifications(withDeviceToken deviceToken: Data) {
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        
        Task {
            await MainActor.run {
                self.deviceToken = tokenString
            }
            
            // Send device token to backend
            await sendDeviceTokenToBackend(tokenString)
        }
    }
    
    func didFailToRegisterForRemoteNotifications(error: Error) {
        print("Failed to register for remote notifications: \(error)")
    }
    
    // MARK: - Send Token to Backend
    
    private func sendDeviceTokenToBackend(_ token: String) async {
        do {
            let _: [String: String] = try await apiClient.request(
                endpoint: "/notifications/device-token",
                method: .post,
                body: [
                    "device_token": token,
                    "platform": "ios"
                ]
            )
            print("Device token registered successfully")
        } catch {
            print("Failed to register device token: \(error)")
        }
    }
    
    // MARK: - Create Local Notification
    
    func scheduleLocalNotification(title: String, body: String, delay: TimeInterval = 0) {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        
        let trigger: UNNotificationTrigger
        if delay > 0 {
            trigger = UNTimeIntervalNotificationTrigger(timeInterval: delay, repeats: false)
        } else {
            trigger = UNTimeIntervalNotificationTrigger(timeInterval: 1, repeats: false)
        }
        
        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: content,
            trigger: trigger
        )
        
        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                print("Failed to schedule local notification: \(error)")
            }
        }
    }
    
    // MARK: - Remove All Notifications
    
    func removeAllPendingNotifications() {
        UNUserNotificationCenter.current().removeAllPendingNotificationRequests()
        UNUserNotificationCenter.current().removeAllDeliveredNotifications()
    }
    
    // MARK: - Get Notification Settings
    
    func getNotificationSettings() async -> UNNotificationSettings {
        return await UNUserNotificationCenter.current().notificationSettings()
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension NotificationService: UNUserNotificationCenterDelegate {
    // Called when app is in foreground and a notification arrives
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        // Show notification even when app is in foreground
        completionHandler([.banner, .sound, .badge])
    }
    
    // Called when user taps on notification
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo
        
        // Handle notification tap
        handleNotificationTap(userInfo: userInfo)
        
        completionHandler()
    }
    
    private func handleNotificationTap(userInfo: [AnyHashable: Any]) {
        // Parse notification data and navigate to appropriate screen
        if let type = userInfo["type"] as? String {
            switch type {
            case "offer_received":
                // Navigate to offers
                NotificationCenter.default.post(name: .navigateToOffers, object: nil)
            case "transaction_update":
                // Navigate to transactions
                NotificationCenter.default.post(name: .navigateToTransactions, object: nil)
            case "listing_approved":
                // Navigate to my listings
                NotificationCenter.default.post(name: .navigateToListings, object: nil)
            default:
                break
            }
        }
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let navigateToOffers = Notification.Name("navigateToOffers")
    static let navigateToTransactions = Notification.Name("navigateToTransactions")
    static let navigateToListings = Notification.Name("navigateToListings")
}
