//
//  DeliveryDetailView.swift
//  ZimAgriDriver
//
//  Detailed view of a single delivery
//

import SwiftUI

struct DeliveryDetailView: View {
    let delivery: Delivery
    @StateObject private var driverService = DriverService.shared
    @State private var showPickupConfirmation = false
    @State private var deliveryCode = ""
    @State private var showDeliveryConfirmation = false
    @State private var showSurveySheet = false
    @State private var errorMessage = ""
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Status Card
                VStack(spacing: 12) {
                    Image(systemName: statusIcon)
                        .font(.system(size: 40))
                        .foregroundColor(statusColor)
                    
                    Text(delivery.status.capitalized.replacingOccurrences(of: "_", with: " "))
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    if let code = delivery.delivery_code {
                        VStack(spacing: 4) {
                            Text("Delivery Code")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            
                            Text(code)
                                .font(.title3)
                                .fontWeight(.bold)
                        }
                    }
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(statusColor.opacity(0.1))
                .cornerRadius(12)
                .padding(.horizontal)
                
                // Route Information
                VStack(alignment: .leading, spacing: 12) {
                    Text("Route Information")
                        .font(.headline)
                    
                    RouteRow(label: "Pickup", value: delivery.pickup_address, icon: "mappin.circle.fill")
                    RouteRow(label: "Delivery", value: delivery.delivery_address, icon: "flag.fill")
                }
                .padding()
                .background(Color(UIColor.systemGray6))
                .cornerRadius(12)
                .padding(.horizontal)
                
                // Order Details
                VStack(alignment: .leading, spacing: 12) {
                    Text("Order Details")
                        .font(.headline)
                    
                    DetailRow(label: "Listing", value: delivery.listing_title ?? "N/A")
                    DetailRow(label: "Quantity", value: "\(Int(delivery.quantity_kg)) kg")
                    DetailRow(label: "Seller", value: delivery.seller_name ?? "N/A")
                    DetailRow(label: "Buyer", value: delivery.buyer_name ?? "N/A")
                }
                .padding()
                .background(Color(UIColor.systemGray6))
                .cornerRadius(12)
                .padding(.horizontal)
                
                // Schedule
                if let pickup = delivery.scheduled_pickup, let deliveryTime = delivery.scheduled_delivery {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Schedule")
                            .font(.headline)
                        
                        DetailRow(label: "Pickup", value: formatDate(pickup))
                        DetailRow(label: "Delivery", value: formatDate(deliveryTime))
                    }
                    .padding()
                    .background(Color(UIColor.systemGray6))
                    .cornerRadius(12)
                    .padding(.horizontal)
                }
                
                // Action Buttons
                VStack(spacing: 12) {
                    if delivery.status.lowercased() == "assigned" {
                        Button {
                            showPickupConfirmation = true
                        } label: {
                            Text("Confirm Pickup")
                                .fontWeight(.semibold)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(10)
                        }
                    }
                    
                    if delivery.status.lowercased() == "picked_up" || delivery.status.lowercased() == "in_transit" {
                        Button {
                            showDeliveryConfirmation = true
                        } label: {
                            Text("Confirm Delivery")
                                .fontWeight(.semibold)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.green)
                                .foregroundColor(.white)
                                .cornerRadius(10)
                        }
                    }
                    
                    if delivery.status.lowercased() == "delivered" {
                        Button {
                            showSurveySheet = true
                        } label: {
                            Text("Submit Transport Survey")
                                .fontWeight(.semibold)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.orange)
                                .foregroundColor(.white)
                                .cornerRadius(10)
                        }
                    }
                }
                .padding(.horizontal)
            }
            .padding(.vertical)
        }
        .navigationTitle("Delivery Details")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showPickupConfirmation) {
            PickupConfirmationView(delivery: delivery)
        }
        .sheet(isPresented: $showDeliveryConfirmation) {
            DeliveryConfirmationView(delivery: delivery, deliveryCode: $deliveryCode)
        }
        .sheet(isPresented: $showSurveySheet) {
            TransportSurveyView(transactionId: delivery.id)
        }
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
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "ISO8601"
        
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }
        
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct RouteRow: View {
    let label: String
    let value: String
    let icon: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.green)
                .frame(width: 24)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text(value)
                    .font(.subheadline)
            }
        }
    }
}

struct PickupConfirmationView: View {
    @Environment(\.dismiss) private var dismiss
    let delivery: Delivery
    @StateObject private var driverService = DriverService.shared
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                Image(systemName: "truck.box")
                    .font(.system(size: 60))
                    .foregroundColor(.blue)
                
                Text("Confirm Pickup")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text("Are you sure you want to confirm pickup for this delivery?")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Pickup Address:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(delivery.pickup_address)
                        .font(.subheadline)
                }
                .padding()
                .background(Color(UIColor.systemGray6))
                .cornerRadius(8)
                
                if !errorMessage.isEmpty {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .font(.caption)
                }
                
                HStack(spacing: 12) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .buttonStyle(.bordered)
                    
                    Button("Confirm") {
                        handleConfirm()
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(isLoading)
                }
            }
            .padding()
            .navigationTitle("Confirm Pickup")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
    
    private func handleConfirm() {
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                try await driverService.confirmPickup(deliveryId: delivery.id)
                await MainActor.run {
                    isLoading = false
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }
}

struct DeliveryConfirmationView: View {
    @Environment(\.dismiss) private var dismiss
    let delivery: Delivery
    @Binding var deliveryCode: String
    @StateObject private var driverService = DriverService.shared
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section {
                    TextField("Enter Delivery Code", text: $deliveryCode)
                        .keyboardType(.default)
                } header: {
                    Text("Confirm Delivery")
                } footer: {
                    Text("Enter the delivery code provided by the buyer to confirm delivery.")
                }
                
                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Confirm Delivery")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Confirm") {
                        handleConfirm()
                    }
                    .disabled(isLoading || deliveryCode.isEmpty)
                }
            }
        }
    }
    
    private func handleConfirm() {
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                try await driverService.confirmDelivery(
                    deliveryId: delivery.id,
                    deliveryCode: deliveryCode
                )
                await MainActor.run {
                    isLoading = false
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }
}

struct TransportSurveyView: View {
    @Environment(\.dismiss) private var dismiss
    let transactionId: Int
    @StateObject private var driverService = DriverService.shared
    
    @State private var vehicleCondition = "good"
    @State private var roadCondition = "good"
    @State private var weatherCondition = "clear"
    @State private var deliveryTime = 30
    @State private var fuelConsumption = ""
    @State private var notes = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    private let conditions = ["excellent", "good", "fair", "poor"]
    
    var body: some View {
        NavigationView {
            Form {
                Section("Vehicle & Road Conditions") {
                    Picker("Vehicle Condition", selection: $vehicleCondition) {
                        ForEach(conditions, id: \.self) { condition in
                            Text(condition.capitalized).tag(condition)
                        }
                    }
                    
                    Picker("Road Condition", selection: $roadCondition) {
                        ForEach(conditions, id: \.self) { condition in
                            Text(condition.capitalized).tag(condition)
                        }
                    }
                    
                    Picker("Weather", selection: $weatherCondition) {
                        Text("Clear").tag("clear")
                        Text("Rainy").tag("rainy")
                        Text("Cloudy").tag("cloudy")
                    }
                }
                
                Section("Delivery Details") {
                    HStack {
                        Text("Delivery Time")
                        Spacer()
                        Stepper("\(deliveryTime) min", value: $deliveryTime, inRange: 5...180)
                    }
                    
                    TextField("Fuel Consumption (L)", text: $fuelConsumption)
                        .keyboardType(.decimalPad)
                }
                
                Section("Notes (Optional)") {
                    TextEditor(text: $notes)
                        .frame(minHeight: 80)
                }
                
                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Transport Survey")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Submit") {
                        handleSubmit()
                    }
                    .disabled(isLoading)
                }
            }
        }
    }
    
    private func handleSubmit() {
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let request = TransportSurveyRequest(
                    vehicle_condition: vehicleCondition,
                    road_condition: roadCondition,
                    weather_condition: weatherCondition,
                    delivery_time: deliveryTime,
                    fuel_consumption: Double(fuelConsumption),
                    notes: notes.isEmpty ? nil : notes
                )
                try await driverService.submitTransportSurvey(
                    transactionId: transactionId,
                    request
                )
                
                await MainActor.run {
                    isLoading = false
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }
}

#Preview {
    NavigationView {
        DeliveryDetailView(delivery: Delivery(
            id: 1,
            order_id: 1,
            listing_title: "Maize Delivery",
            pickup_address: "123 Farm Road, Harare",
            delivery_address: "456 Market Street, Bulawayo",
            seller_name: "John Farmer",
            buyer_name: "Jane Buyer",
            quantity_kg: 500,
            status: "assigned",
            delivery_code: "ABC123",
            scheduled_pickup: "2024-01-01T10:00:00Z",
            scheduled_delivery: "2024-01-01T14:00:00Z",
            created_at: "2024-01-01T00:00:00Z"
        ))
    }
}
