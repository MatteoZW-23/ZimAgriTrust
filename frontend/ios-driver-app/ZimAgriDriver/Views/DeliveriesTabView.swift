//
//  DeliveriesTabView.swift
//  ZimAgriDriver
//
//  Main deliveries tab for drivers
//

import SwiftUI

struct DeliveriesTabView: View {
    @StateObject private var driverService = DriverService.shared
    
    var body: some View {
        NavigationView {
            Group {
                if driverService.deliveries.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "truck.box")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        
                        Text("No deliveries assigned")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Button("Refresh") {
                            Task {
                                try? await driverService.fetchDeliveries()
                            }
                        }
                        .buttonStyle(.bordered)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(driverService.deliveries) { delivery in
                            NavigationLink(destination: DeliveryDetailView(delivery: delivery)) {
                                DeliveryCard(delivery: delivery)
                            }
                        }
                    }
                    .listStyle(.plain)
                    .refreshable {
                        try? await driverService.fetchDeliveries()
                    }
                }
            }
            .navigationTitle("Deliveries")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        Task {
                            try? await driverService.fetchDeliveries()
                        }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .onAppear {
                Task {
                    try? await driverService.fetchDeliveries()
                }
            }
        }
    }
}

struct DeliveryCard: View {
    let delivery: Delivery
    
    var body: some View {
        HStack(spacing: 12) {
            // Status Icon
            ZStack {
                Circle()
                    .fill(statusColor.opacity(0.2))
                    .frame(width: 40, height: 40)
                
                Image(systemName: statusIcon)
                    .foregroundColor(statusColor)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(delivery.listing_title ?? "Delivery #\(delivery.id)")
                    .font(.headline)
                    .lineLimit(1)
                
                Text("\(delivery.seller_name ?? "Seller") → \(delivery.buyer_name ?? "Buyer")")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                HStack {
                    Text("\(Int(delivery.quantity_kg)) kg")
                        .font(.caption)
                    
                    Spacer()
                    
                    Text(delivery.status.capitalized)
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(statusColor.opacity(0.2))
                        .foregroundColor(statusColor)
                        .cornerRadius(4)
                }
            }
        }
        .padding(.vertical, 4)
    }
    
    private var statusColor: Color {
        switch delivery.status.lowercased() {
        case "assigned", "pending":
            return .orange
        case "picked_up", "in_transit":
            return .blue
        case "delivered":
            return .green
        case "cancelled":
            return .red
        default:
            return .gray
        }
    }
    
    private var statusIcon: String {
        switch delivery.status.lowercased() {
        case "assigned", "pending":
            return "clock.fill"
        case "picked_up", "in_transit":
            return "truck.fill"
        case "delivered":
            return "checkmark.circle.fill"
        case "cancelled":
            return "xmark.circle.fill"
        default:
            return "circle.fill"
        }
    }
}

#Preview {
    DeliveriesTabView()
}
