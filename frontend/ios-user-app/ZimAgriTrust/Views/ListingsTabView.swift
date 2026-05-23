//
//  ListingsTabView.swift
//  ZimAgriTrust
//
//  Main listings tab with browse, search, and my listings
//

import SwiftUI

struct ListingsTabView: View {
    @StateObject private var listingService = ListingService.shared
    @State private var searchText = ""
    @State private var selectedFilter: String = "All"
    @State private var showCreateListing = false
    
    private let filters = ["All", "Maize", "Tomato", "Soybeans", "Groundnuts", "Cabbage"]
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Search Bar
                SearchBar(text: $searchText)
                    .padding(.horizontal)
                    .padding(.top, 8)
                
                // Filter Chips
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        ForEach(filters, id: \.self) { filter in
                            FilterChip(title: filter, isSelected: selectedFilter == filter) {
                                selectedFilter = filter
                            }
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical, 8)
                
                // Listings List
                if listingService.listings.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "list.bullet.rectangle")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        
                        Text("No listings available")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Button("Refresh") {
                            Task {
                                try? await listingService.fetchListings()
                            }
                        }
                        .buttonStyle(.bordered)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(filteredListings) { listing in
                            NavigationLink(destination: ListingDetailView(listing: listing)) {
                                ListingCard(listing: listing)
                            }
                        }
                    }
                    .listStyle(.plain)
                    .refreshable {
                        try? await listingService.fetchListings()
                    }
                }
            }
            .navigationTitle("Listings")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showCreateListing = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showCreateListing) {
                CreateListingView()
            }
            .onAppear {
                Task {
                    try? await listingService.fetchListings()
                }
            }
        }
    }
    
    private var filteredListings: [Listing] {
        listingService.listings.filter { listing in
            let matchesSearch = searchText.isEmpty || 
                listing.title.localizedCaseInsensitiveContains(searchText) ||
                listing.crop_type.localizedCaseInsensitiveContains(searchText)
            
            let matchesFilter = selectedFilter == "All" || 
                listing.crop_type.localizedCaseInsensitiveContains(selectedFilter)
            
            return matchesSearch && matchesFilter
        }
    }
}

struct SearchBar: View {
    @Binding var text: String
    
    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.gray)
            
            TextField("Search listings...", text: $text)
                .textFieldStyle(.plain)
            
            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.gray)
                }
            }
        }
        .padding(8)
        .background(Color(UIColor.systemGray6))
        .cornerRadius(10)
    }
}

struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .fontWeight(.medium)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(isSelected ? Color.green : Color(UIColor.systemGray5))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(20)
        }
    }
}

struct ListingCard: View {
    let listing: Listing
    
    var body: some View {
        HStack(spacing: 12) {
            // Placeholder for image
            Rectangle()
                .fill(Color(UIColor.systemGray4))
                .frame(width: 80, height: 80)
                .cornerRadius(8)
                .overlay {
                    if let firstImage = listing.images?.first {
                        AsyncImage(url: URL(string: firstImage)) { image in
                            image.resizable()
                        } placeholder: {
                            Image(systemName: "photo")
                                .foregroundColor(.gray)
                        }
                    } else {
                        Image(systemName: "leaf.fill")
                            .foregroundColor(.green)
                    }
                }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(listing.title)
                    .font(.headline)
                    .lineLimit(1)
                
                Text(listing.crop_type)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                HStack {
                    Text("\(Int(listing.quantity_kg)) kg")
                        .font(.caption)
                    
                    Spacer()
                    
                    Text(listing.formattedPrice)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(.green)
                }
                
                Text(listing.location ?? "Unknown location")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

extension Listing {
    var formattedPrice: String {
        String(format: "$%.2f/kg", price_per_kg)
    }
}

#Preview {
    ListingsTabView()
}
