import SwiftUI
import WatchKit
import Combine

@main
struct ZimAgriWatchApp: App {
    @StateObject private var watchViewModel = WatchViewModel()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(watchViewModel)
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var viewModel: WatchViewModel
    @State private var selectedTab: WatchTab = .listings
    
    enum WatchTab: String, CaseIterable {
        case listings = "Listings"
        case wallet = "Wallet"
        case notifications = "Alerts"
    }
    
    var body: some View {
        TabView(selection: $selectedTab) {
            ListingsTabView()
                .tag(WatchTab.listings)
                .tabItem {
                    Image(systemName: "list.bullet")
                    Text("Listings")
                }
            
            WalletTabView()
                .tag(WatchTab.wallet)
                .tabItem {
                    Image(systemName: "dollarsign.circle")
                    Text("Wallet")
                }
            
            NotificationsTabView()
                .tag(WatchTab.notifications)
                .tabItem {
                    Image(systemName: "bell")
                    Text("Alerts")
                }
        }
        .task {
            await viewModel.loadData()
        }
    }
}

struct ListingsTabView: View {
    @EnvironmentObject var viewModel: WatchViewModel
    @State private var searchText = ""
    
    var body: some View {
        List {
            ForEach(filteredListings) { listing in
                ListingRowView(listing: listing)
            }
        }
        .searchable(text: $searchText)
        .navigationTitle("Listings")
    }
    
    var filteredListings: [Listing] {
        if searchText.isEmpty {
            return viewModel.listings
        }
        return viewModel.listings.filter { listing in
            listing.crop_name.localizedCaseInsensitiveContains(searchText) ||
            listing.location.localizedCaseInsensitiveContains(searchText)
        }
    }
}

struct ListingRowView: View {
    let listing: Listing
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(listing.crop_name)
                .font(.headline)
            
            HStack {
                Text("\(Int(listing.quantity_kg)) kg")
                    .font(.caption)
                
                Spacer()
                
                Text("$\(String(format: "%.2f", listing.price_per_kg))/kg")
                    .font(.caption)
                    .foregroundColor(.green)
            }
            
            Text(listing.location)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}

struct WalletTabView: View {
    @EnvironmentObject var viewModel: WatchViewModel
    
    var body: some View {
        VStack(spacing: 16) {
            VStack(spacing: 8) {
                Text("Available Balance")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text("$\(String(format: "%.2f", viewModel.walletBalance?.available ?? 0))")
                    .font(.title)
                    .fontWeight(.bold)
            }
            .padding()
            .background(Color.green.opacity(0.1))
            .cornerRadius(12)
            
            VStack(spacing: 8) {
                Text("Pending")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text("$\(String(format: "%.2f", viewModel.walletBalance?.pending ?? 0))")
                    .font(.title2)
                    .fontWeight(.semibold)
            }
            .padding()
            .background(Color.orange.opacity(0.1))
            .cornerRadius(12)
            
            Spacer()
        }
        .padding()
        .navigationTitle("Wallet")
    }
}

struct NotificationsTabView: View {
    @EnvironmentObject var viewModel: WatchViewModel
    
    var body: some View {
        List {
            ForEach(viewModel.notifications) { notification in
                NotificationRowView(notification: notification)
            }
        }
        .navigationTitle("Alerts")
    }
}

struct NotificationRowView: View {
    let notification: WatchNotification
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(notification.title)
                .font(.headline)
            
            Text(notification.message)
                .font(.caption)
                .foregroundColor(.secondary)
            
            Text(notification.timeAgo)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}

@MainActor
class WatchViewModel: ObservableObject {
    @Published var listings: [Listing] = []
    @Published var walletBalance: WalletBalance?
    @Published var notifications: [WatchNotification] = []
    @Published var isLoading = false
    
    func loadData() async {
        isLoading = true
        
        do {
            async let listings = fetchListings()
            async let balance = fetchWalletBalance()
            async let notifications = fetchNotifications()
            
            self.listings = try await listings
            self.walletBalance = try await balance
            self.notifications = try await notifications
            
            isLoading = false
        } catch {
            isLoading = false
            print("Error loading data: \(error)")
        }
    }
    
    private func fetchListings() async throws -> [Listing] {
        // Call the actual API or use WatchConnectivity to get data from phone
        // For now, return mock data
        return [
            Listing(id: 1, seller_id: 1, crop_name: "Maize", quantity_kg: 500, price_per_kg: 0.50, location: "Harare", status: "active", description: nil, image_urls: [], created_at: nil),
            Listing(id: 2, seller_id: 2, crop_name: "Tomatoes", quantity_kg: 200, price_per_kg: 1.20, location: "Bulawayo", status: "active", description: nil, image_urls: [], created_at: nil)
        ]
    }
    
    private func fetchWalletBalance() async throws -> WalletBalance {
        // Call the actual API or use WatchConnectivity
        return WalletBalance(available: 500.0, pending: 100.0, total: 600.0, currency: "USD")
    }
    
    private func fetchNotifications() async throws -> [WatchNotification] {
        // Call the actual API or use WatchConnectivity
        return [
            WatchNotification(id: 1, title: "Offer Accepted", message: "Your offer for Maize has been accepted", timeAgo: "2m ago"),
            WatchNotification(id: 2, title: "Delivery Update", message: "Your order is in transit", timeAgo: "1h ago")
        ]
    }
}

struct WatchNotification: Identifiable {
    let id: Int
    let title: String
    let message: String
    let timeAgo: String
}
