import WidgetKit
import SwiftUI
import Intents

struct OrderStatusEntry: TimelineEntry {
    let date: Date
    let activeOrders: [ActiveOrder]
    let hasActiveDeliveries: Bool
}

struct ActiveOrder: Identifiable {
    let id: Int
    let cropName: String
    let quantity: Double
    let status: DeliveryStatus
    let estimatedDelivery: Date?
    let progress: Double
}

enum DeliveryStatus: String {
    case pending = "Pending"
    case confirmed = "Confirmed"
    case pickedUp = "Picked Up"
    case inTransit = "In Transit"
    case delivered = "Delivered"
    
    var icon: String {
        switch self {
        case .pending: return "clock"
        case .confirmed: return "checkmark.circle"
        case .pickedUp: return "box.truck"
        case .inTransit: return "truck"
        case .delivered: return "checkmark.circle.fill"
        }
    }
    
    var color: Color {
        switch self {
        case .pending: return .orange
        case .confirmed: return .blue
        case .pickedUp: return .purple
        case .inTransit: return .green
        case .delivered: return .green
        }
    }
}

struct OrderStatusProvider: TimelineProvider {
    func placeholder(in context: Context) -> OrderStatusEntry {
        OrderStatusEntry(
            date: Date(),
            activeOrders: [
                ActiveOrder(
                    id: 1,
                    cropName: "Maize",
                    quantity: 500,
                    status: .inTransit,
                    estimatedDelivery: Date().addingTimeInterval(3600),
                    progress: 0.6
                )
            ],
            hasActiveDeliveries: true
        )
    }

    func getSnapshot(in context: Context, completion: @escaping (OrderStatusEntry) -> Void) {
        let entry = placeholder(in: context)
        completion(entry)
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<OrderStatusEntry>) -> Void) {
        Task {
            let activeOrders = await fetchActiveOrders()
            let hasActiveDeliveries = activeOrders.contains { $0.status == .inTransit || $0.status == .pickedUp }
            
            let entry = OrderStatusEntry(
                date: Date(),
                marketPrices: activeOrders,
                hasActiveDeliveries: hasActiveDeliveries
            )
            
            // Update every 15 minutes for active deliveries, hourly otherwise
            let refreshInterval: TimeInterval = hasActiveDeliveries ? 900 : 3600
            let nextUpdate = Calendar.current.date(byAdding: .second, value: Int(refreshInterval), to: Date()) ?? Date()
            let timeline = Timeline(entries: [entry], policy: .after(nextUpdate))
            
            completion(timeline)
        }
    }
    
    private func fetchActiveOrders() async -> [ActiveOrder] {
        // In production, this would call the actual API
        // For now, return mock data
        return [
            ActiveOrder(
                id: 1,
                cropName: "Maize",
                quantity: 500,
                status: .inTransit,
                estimatedDelivery: Date().addingTimeInterval(3600),
                progress: 0.6
            )
        ]
    }
}

struct OrderStatusWidgetEntryView: View {
    var entry: OrderStatusProvider.Entry
    @Environment(\.widgetFamily) var family

    var body: some View {
        switch family {
        case .systemSmall:
            smallWidget
        case .systemMedium:
            mediumWidget
        default:
            smallWidget
        }
    }
    
    var smallWidget: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: entry.hasActiveDeliveries ? "truck.box.fill" : "cube.box")
                    .foregroundColor(entry.hasActiveDeliveries ? .green : .blue)
                Text("Order Status")
                    .font(.headline)
                Spacer()
            }
            
            if let firstOrder = entry.activeOrders.first {
                VStack(alignment: .leading, spacing: 4) {
                    Text(firstOrder.cropName)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                    
                    Text("\(Int(firstOrder.quantity)) kg")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    HStack {
                        Image(systemName: firstOrder.status.icon)
                            .foregroundColor(firstOrder.status.color)
                        Text(firstOrder.status.rawValue)
                            .font(.caption)
                    }
                    
                    if let estimated = firstOrder.estimatedDelivery {
                        Text("ETA: \(formatTime(estimated))")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    
                    ProgressView(value: firstOrder.progress)
                        .progressViewStyle(LinearProgressViewStyle(tint: .green))
                }
            } else {
                Text("No active orders")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
    }
    
    var mediumWidget: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: entry.hasActiveDeliveries ? "truck.box.fill" : "cube.box")
                    .foregroundColor(entry.hasActiveDeliveries ? .green : .blue)
                Text("Order Status")
                    .font(.headline)
                Spacer()
                Text("\(entry.activeOrders.count) active")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Divider()
            
            ForEach(entry.activeOrders.prefix(2)) { order in
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(order.cropName)
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        Text("\(Int(order.quantity)) kg")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing, spacing: 2) {
                        HStack {
                            Image(systemName: order.status.icon)
                                .font(.caption)
                            Text(order.status.rawValue)
                                .font(.caption)
                        }
                        .foregroundColor(order.status.color)
                        
                        if let estimated = order.estimatedDelivery {
                            Text("ETA: \(formatTime(estimated))")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                ProgressView(value: order.progress)
                    .progressViewStyle(LinearProgressViewStyle(tint: .green))
            }
            
            if entry.activeOrders.isEmpty {
                Text("No active orders")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
            }
        }
        .padding()
    }
    
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct OrderStatusWidget: Widget {
    let kind: String = "OrderStatusWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: OrderStatusProvider()) { entry in
            OrderStatusWidgetEntryView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("Order Status")
        .description("Track your active deliveries")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

@main
struct OrderStatusWidgetBundle: WidgetBundle {
    var body: some Widget {
        OrderStatusWidget()
    }
}
