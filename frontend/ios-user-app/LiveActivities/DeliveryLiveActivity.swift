import ActivityKit
import WidgetKit
import SwiftUI
import Intents

struct DeliveryAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        var orderId: Int
        var cropName: String
        var quantity: Double
        var status: DeliveryStatus
        var driverName: String?
        var driverPhone: String?
        var estimatedArrival: Date?
        var currentLocation: String?
        var progress: Double
    }
    
    var orderId: Int
    var cropName: String
    var quantity: Double
}

enum DeliveryStatus: String, Codable {
    case confirmed = "confirmed"
    case pickedUp = "picked_up"
    case inTransit = "in_transit"
    case delivered = "delivered"
    
    var displayName: String {
        switch self {
        case .confirmed: return "Confirmed"
        case .pickedUp: return "Picked Up"
        case .inTransit: return "In Transit"
        case .delivered: return "Delivered"
        }
    }
    
    var icon: String {
        switch self {
        case .confirmed: return "checkmark.circle"
        case .pickedUp: return "box.truck"
        case .inTransit: return "truck"
        case .delivered: return "checkmark.circle.fill"
        }
    }
}

struct DeliveryLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: DeliveryAttributes.self) { context in
            // Lock screen / banner
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(context.attributes.cropName)
                        .font(.headline)
                    Text("\(Int(context.attributes.quantity)) kg")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    HStack {
                        Image(systemName: context.state.status.icon)
                            .foregroundColor(.green)
                        Text(context.state.status.displayName)
                            .font(.caption)
                    }
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    if let driverName = context.state.driverName {
                        Text(driverName)
                            .font(.caption)
                            .fontWeight(.semibold)
                    }
                    
                    if let estimated = context.state.estimatedArrival {
                        Text("ETA: \(formatTime(estimated))")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    
                    ProgressView(value: context.state.progress)
                        .progressViewStyle(CircularProgressViewStyle(tint: .green))
                        .scaleEffect(0.8)
                }
            }
            .padding()
        } dynamicIsland: { context in
            // Dynamic Island
            DynamicIsland {
                // Expanded
                DynamicIslandExpandedRegion(.leading) {
                    HStack {
                        Image(systemName: "truck.box.fill")
                            .foregroundColor(.green)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(context.attributes.cropName)
                                .font(.headline)
                            Text("\(Int(context.attributes.quantity)) kg")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                DynamicIslandExpandedRegion(.trailing) {
                    VStack(alignment: .trailing, spacing: 2) {
                        if let driverName = context.state.driverName {
                            Text(driverName)
                                .font(.caption)
                                .fontWeight(.semibold)
                        }
                        
                        if let driverPhone = context.state.driverPhone {
                            Button(action: {
                                // Call driver
                                if let url = URL(string: "tel:\(driverPhone)") {
                                    UIApplication.shared.open(url)
                                }
                            }) {
                                Image(systemName: "phone.fill")
                                    .foregroundColor(.green)
                            }
                        }
                    }
                }
                
                DynamicIslandExpandedRegion(.bottom) {
                    VStack(spacing: 8) {
                        HStack {
                            Text("Status:")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text(context.state.status.displayName)
                                .font(.caption)
                                .fontWeight(.semibold)
                        }
                        
                        ProgressView(value: context.state.progress)
                            .progressViewStyle(LinearProgressViewStyle(tint: .green))
                        
                        if let estimated = context.state.estimatedArrival {
                            HStack {
                                Image(systemName: "clock")
                                    .font(.caption)
                                Text("ETA: \(formatTime(estimated))")
                                    .font(.caption)
                            }
                            .foregroundColor(.secondary)
                        }
                        
                        if let location = context.state.currentLocation {
                            HStack {
                                Image(systemName: "location")
                                    .font(.caption)
                                Text(location)
                                    .font(.caption)
                            }
                            .foregroundColor(.secondary)
                        }
                    }
                }
            } compactLeading: {
                Image(systemName: "truck.box.fill")
                    .foregroundColor(.green)
            } compactTrailing: {
                if let estimated = context.state.estimatedArrival {
                    Text(formatTime(estimated))
                        .font(.caption)
                } else {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .green))
                        .scaleEffect(0.7)
                }
            } minimal: {
                Image(systemName: "truck.box.fill")
                    .foregroundColor(.green)
            }
        }
    }
    
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

class LiveActivityManager {
    static let shared = LiveActivityManager()
    
    private var activities: [String: Activity<DeliveryAttributes>] = [:]
    
    func startDeliveryActivity(orderId: Int, cropName: String, quantity: Double) {
        let attributes = DeliveryAttributes(orderId: orderId, cropName: cropName, quantity: quantity)
        let initialState = DeliveryAttributes.ContentState(
            orderId: orderId,
            cropName: cropName,
            quantity: quantity,
            status: .confirmed,
            driverName: nil,
            driverPhone: nil,
            estimatedArrival: nil,
            currentLocation: nil,
            progress: 0.1
        )
        
        let activity = Activity<DeliveryAttributes>.request(attributes: attributes, content: .init(state: initialState, staleDate: nil))
        
        activities["\(orderId)"] = activity
    }
    
    func updateDeliveryActivity(orderId: Int, status: DeliveryStatus, driverName: String? = nil, driverPhone: String? = nil, estimatedArrival: Date? = nil, currentLocation: String? = nil, progress: Double) {
        guard let activity = activities["\(orderId)"] else { return }
        
        Task {
            let updatedState = DeliveryAttributes.ContentState(
                orderId: orderId,
                cropName: activity.attributes.cropName,
                quantity: activity.attributes.quantity,
                status: status,
                driverName: driverName,
                driverPhone: driverPhone,
                estimatedArrival: estimatedArrival,
                currentLocation: currentLocation,
                progress: progress
            )
            
            await activity.update(using: .init(state: updatedState, staleDate: nil))
        }
    }
    
    func endDeliveryActivity(orderId: Int) {
        guard let activity = activities["\(orderId)"] else { return }
        
        Task {
            let finalState = DeliveryAttributes.ContentState(
                orderId: orderId,
                cropName: activity.attributes.cropName,
                quantity: activity.attributes.quantity,
                status: .delivered,
                driverName: nil,
                driverPhone: nil,
                estimatedArrival: nil,
                currentLocation: nil,
                progress: 1.0
            )
            
            await activity.end(using: .init(state: finalState, staleDate: nil), dismissalPolicy: .default)
            activities.removeValue(forKey: "\(orderId)")
        }
    }
    
    func stopDeliveryActivity(orderId: Int) {
        guard let activity = activities["\(orderId)"] else { return }
        
        Task {
            await activity.end(dismissalPolicy: .immediate)
            activities.removeValue(forKey: "\(orderId)")
        }
    }
}
