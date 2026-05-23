//
//  CreateListingView.swift
//  ZimAgriTrust
//
//  Create a new listing
//

import SwiftUI
import PhotosUI

struct CreateListingView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var listingService = ListingService.shared
    
    @State private var title = ""
    @State private var description = ""
    @State private var cropType = ""
    @State private var quantity = ""
    @State private var pricePerKg = ""
    @State private var location = ""
    @State private var province = ""
    @State private var district = ""
    
    @State private var selectedImages: [PhotosPickerItem] = []
    @State private var imageDatas: [Data] = []
    
    @State 
    \
    private var isLoading = false
    @State private var errorMessage = ""
    
    private let cropTypes = ["Maize", "Tomato", "Soybeans", "Groundnuts", "Cabbage", "Potato", "Onion", "Sugar Beans", "Sunflower", "Tobacco", "Cotton", "Mango"]
    private let provinces = ["Harare", "Bulawayo", "Manicaland", "Mashonaland Central", "Mashonaland East", "Mashonaland West", "Masvingo", "Matabeleland North", "Matabeleland South", "Midlands"]
    
    var body: some View {
        NavigationView {
            Form {
                Section("Listing Information") {
                    TextField("Title", text: $title)
                    TextField("Description", text: $description, axis: .vertical)
                        .lineLimit(3...6)
                }
                
                Section("Crop Details") {
                    Picker("Crop Type", selection: $cropType) {
                        Text("Select Crop").tag("")
                        ForEach(cropTypes, id: \.self) { crop in
                            Text(crop).tag(crop)
                        }
                    }
                    
                    TextField("Quantity (kg)", text: $quantity)
                        .keyboardType(.decimalPad)
                    
                    TextField("Price per kg (USD)", text: $pricePerKg)
                        .keyboardType(.decimalPad)
                }
                
                Section("Location") {
                    TextField("Location", text: $location)
                    
                    Picker("Province", selection: $province) {
                        Text("Select Province").tag("")
                        ForEach(provinces, id: \.self) { province in
                            Text(province).tag(province)
                        }
                    }
                    
                    TextField("District", text: $district)
                }
                
                Section("Images") {
                    PhotosPicker(
                        selection: $selectedImages,
                        maxSelectionCount: 5,
                        matching: .images
                    ) {
                        HStack {
                            Image(systemName: "photo.on.rectangle")
                            Text("Add Photos")
                        }
                    }
                    
                    if !imageDatas.isEmpty {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(Array(imageDatas.enumerated()), id: \.offset) { _, data in
                                    if let image = UIImage(data: data) {
                                        Image(uiImage: image)
                                            .resizable()
                                            .scaledToFill()
                                            .frame(width: 80, height: 80)
                                            .cornerRadius(8)
                                    }
                                }
                            }
                        }
                    }
                }
                .onChange(of: selectedImages) { _, newValue in
                    Task {
                        await loadImages(from: newValue)
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
            .navigationTitle("Create Listing")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Publish") {
                        handleCreate()
                    }
                    .disabled(isLoading)
                }
            }
        }
    }
    
    private func loadImages(from items: [PhotosPickerItem]) async {
        imageDatas.removeAll()
        
        for item in items {
            if let data = try? await item.loadTransferable(type: Data.self) {
                imageDatas.append(data)
            }
        }
    }
    
    private func handleCreate() {
        guard !title.isEmpty, !description.isEmpty else {
            errorMessage = "Please enter title and description"
            return
        }
        
        guard !cropType.isEmpty else {
            errorMessage = "Please select a crop type"
            return
        }
        
        guard let quantityValue = Double(quantity), quantityValue > 0 else {
            errorMessage = "Please enter a valid quantity"
            return
        }
        
        guard let priceValue = Double(pricePerKg), priceValue > 0 else {
            errorMessage = "Please enter a valid price"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let request = CreateListingRequest(
                    title: title,
                    description: description,
                    crop_type: cropType.lowercased(),
                    quantity_kg: quantityValue,
                    price_per_kg: priceValue,
                    location: location.isEmpty ? nil : location,
                    province: province.isEmpty ? nil : province,
                    district: district.isEmpty ? nil : district
                )
                
                let listing = try await listingService.createListing(request)
                
                // Upload images if any
                if !imageDatas.isEmpty {
                    for (index, imageData) in imageDatas.enumerated() {
                        let file = MultipartFile(
                            name: "images",
                            filename: "image_\(index).jpg",
                            mimeType: "image/jpeg",
                            data: imageData
                        )
                        _ = try? await APIClient.shared.uploadMultipart(
                            endpoint: "/listings/\(listing.id)/images",
                            method: .post,
                            files: [file]
                        )
                    }
                }
                
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
    CreateListingView()
}
