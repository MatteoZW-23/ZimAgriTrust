//
//  ListingDetailView.swift
//  ZimAgriTrust
//
//  Detailed view of a single listing
//

import SwiftUI

struct ListingDetailView: View {
    let listing: Listing
    @StateObject private var listingService = ListingService.shared
    @State private var showOfferSheet = false
    @State private var showSaveAlert = false
    @State private var isSaved = false
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Images
                if let images = listing.images, !images.isEmpty {
                    ImageCarousel(images: images)
                } else {
                    Rectangle()
                        .fill(Color(UIColor.systemGray4))
                        .frame(height: 250)
                        .overlay {
                            Image(systemName: "photo")
                                .font(.system(size: 50))
                                .foregroundColor(.gray)
                        }
                }
                
                // Title and Price
                VStack(alignment: .leading, spacing: 8) {
                    Text(listing.title)
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    HStack {
                        Text(listing.crop_type.capitalized)
                            .font(.subheadline)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.green.opacity(0.1))
                            .foregroundColor(.green)
                            .cornerRadius(4)
                        
                        Spacer()
                        
                        Text(listing.formattedPrice)
                            .font(.title)
                            .fontWeight(.bold)
                            .foregroundColor(.green)
                    }
                }
                .padding(.horizontal)
                
                // Details
                VStack(alignment: .leading, spacing: 12) {
                    Text("Details")
                        .font(.headline)
                    
                    DetailRow(label: "Quantity", value: "\(Int(listing.quantity_kg)) kg")
                    DetailRow(label: "Total Price", value: listing.formattedTotalPrice)
                    DetailRow(label: "Location", value: listing.location ?? "Not specified")
                    DetailRow(label: "Province", value: listing.province ?? "Not specified")
                    DetailRow(label: "District", value: listing.district ?? "Not specified")
                    DetailRow(label: "Status", value: listing.status.capitalized)
                }
                .padding()
                .background(Color(UIColor.systemGray6))
                .cornerRadius(12)
                .padding(.horizontal)
                
                // Description
                VStack(alignment: .leading, spacing: 8) {
                    Text("Description")
                        .font(.headline)
                    
                    Text(listing.description)
                        .font(.body)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal)
                
                // Seller Info
                VStack(alignment: .leading, spacing: 12) {
                    Text("Seller")
                        .font(.headline)
                    
                    HStack(spacing: 12) {
                        Circle()
                            .fill(Color.green.opacity(0.1))
                            .frame(width: 50, height: 50)
                            .overlay {
                                Text(listing.seller_name?.prefix(1).uppercased() ?? "S")
                                    .font(.title2)
                                    .fontWeight(.bold)
                                    .foregroundColor(.green)
                            }
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text(listing.seller_name ?? "Unknown Seller")
                                .font(.subheadline)
                                .fontWeight(.semibold)
                            
                            if let phone = listing.seller_phone {
                                Text(phone)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
                .padding()
                .background(Color(UIColor.systemGray6))
                .cornerRadius(12)
                .padding(.horizontal)
                
                // Action Buttons
                HStack(spacing: 12) {
                    Button {
                        showOfferSheet = true
                    } label: {
                        Text("Make Offer")
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.green)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                    }
                    
                    Button {
                        handleSave()
                    } label: {
                        Image(systemName: isSaved ? "bookmark.fill" : "bookmark")
                            .font(.title2)
                            .foregroundColor(isSaved ? .green : .gray)
                            .frame(width: 50, height: 50)
                            .background(Color(UIColor.systemGray6))
                            .cornerRadius(10)
                    }
                }
                .padding(.horizontal)
            }
            .padding(.vertical)
        }
        .navigationTitle("Listing Details")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showOfferSheet) {
            MakeOfferView(listing: listing)
        }
        .alert("Saved", isPresented: $showSaveAlert) {
            Button("OK") {}
        } message: {
            Text("Listing has been saved to your favorites.")
        }
    }
    
    private func handleSave() {
        Task {
            do {
                try await listingService.saveListing(id: listing.id)
                await MainActor.run {
                    isSaved = true
                    showSaveAlert = true
                }
            } catch {
                print("Failed to save listing: \(error)")
            }
        }
    }
}

struct ImageCarousel: View {
    let images: [String]
    @State private var currentIndex = 0
    
    var body: some View {
        TabView(selection: $currentIndex) {
            ForEach(Array(images.enumerated()), id: \.offset) { index, imageUrl in
                AsyncImage(url: URL(string: imageUrl)) { image in
                    image
                        .resizable()
                        .scaledToFill()
                } placeholder: {
                    Rectangle()
                        .fill(Color(UIColor.systemGray4))
                }
                .tag(index)
            }
        }
        .frame(height: 250)
        .tabViewStyle(.page(indexDisplayMode: .always))
    }
}

extension Listing {
    var formattedTotalPrice: String {
        String(format: "$%.2f", totalPrice)
    }
}

struct MakeOfferView: View {
    @Environment(\.dismiss) private var dismiss
    let listing: Listing
    @StateObject private var listingService = ListingService.shared
    
    @State private var offeredPrice = ""
    @State private var offeredQuantity = ""
    @State private var message = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section("Offer Details") {
                    HStack {
                        Text("Price per kg")
                        Spacer()
                        Text("$\(String(format: "%.2f", listing.price_per_kg))")
                            .foregroundColor(.secondary)
                    }
                    
                    TextField("Your Offer (per kg)", text: $offeredPrice)
                        .keyboardType(.decimalPad)
                    
                    HStack {
                        Text("Quantity")
                        Spacer()
                        Text("\(Int(listing.quantity_kg)) kg")
                            .foregroundColor(.secondary)
                    }
                    
                    TextField("Your Quantity (kg)", text: $offeredQuantity)
                        .keyboardType(.numberPad)
                }
                
                Section("Message (Optional)") {
                    TextEditor(text: $message)
                        .frame(minHeight: 80)
                }
                
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Offer Summary")
                            .font(.headline)
                        
                        if let price = Double(offeredPrice), let quantity = Double(offeredQuantity) {
                            HStack {
                                Text("Total")
                                Spacer()
                                Text(String(format: "$%.2f", price * quantity))
                                    .fontWeight(.bold)
                            }
                        }
                    }
                }
                
                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Make Offer")
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
        guard let price = Double(offeredPrice), price > 0 else {
            errorMessage = "Please enter a valid price"
            return
        }
        
        guard let quantity = Double(offeredQuantity), quantity > 0 else {
            errorMessage = "Please enter a valid quantity"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let request = CreateOfferRequest(
                    offered_price_per_kg: price,
                    offered_quantity_kg: quantity,
                    message: message.isEmpty ? nil : message
                )
                _ = try await listingService.createOffer(
                    listingId: listing.id,
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
        ListingDetailView(listing: Listing(
            id: 1,
            title: "Premium Maize",
            description: "High quality maize for sale",
            crop_type: "maize",
            quantity_kg: 500,
            price_per_kg: 0.50,
            location: "Harare",
            province: "Harare",
            district: "Harare Central",
            seller_id: 1,
            seller_name: "John Farmer",
            seller_phone: "+263123456789",
            status: "active",
            images: nil,
            created_at: "2024-01-01T00:00:00Z",
            updated_at: nil
        ))
    }
}
