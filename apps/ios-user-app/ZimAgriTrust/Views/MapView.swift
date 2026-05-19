import SwiftUI
import MapKit

struct MapView: View {
    @StateObject private var mapManager = MapManager()
    @State private var selectedListing: Listing?
    @State private var showListingDetail = false
    @State private var showSearch = false
    
    let listings: [Listing]
    
    var body: some View {
        NavigationView {
            ZStack {
                Map(coordinateRegion: $mapManager.region,
                    annotationItems: mapManager.annotations) { annotation in
                    MapMarker(coordinate: annotation.coordinate, tint: .blue)
                        .onTapGesture {
                            if let listingAnnotation = annotation as? ListingAnnotation {
                                selectedListing = listingAnnotation.listing
                                showListingDetail = true
                            }
                        }
                }
                .ignoresSafeArea()
                .onAppear {
                    mapManager.addAnnotations(for: listings)
                    mapManager.centerOnUserLocation()
                }
                
                // Search Button
                VStack {
                    HStack {
                        Spacer()
                        
                        Button(action: {
                            showSearch = true
                        }) {
                            Image(systemName: "magnifyingglass")
                                .font(.title2)
                                .foregroundColor(.white)
                                .padding()
                                .background(Color.blue)
                                .clipShape(Circle())
                                .shadow(radius: 4)
                        }
                        .padding()
                    }
                    
                    Spacer()
                    
                    // Center on User Button
                    HStack {
                        Spacer()
                        
                        Button(action: {
                            mapManager.centerOnUserLocation()
                        }) {
                            Image(systemName: "location.fill")
                                .font(.title2)
                                .foregroundColor(.white)
                                .padding()
                                .background(Color.blue)
                                .clipShape(Circle())
                                .shadow(radius: 4)
                        }
                        .padding()
                    }
                    .padding(.bottom, 20)
                }
            }
            .navigationTitle("Nearby Listings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        mapManager.centerOnUserLocation()
                    }) {
                        Image(systemName: "location.fill")
                    }
                }
            }
            .sheet(isPresented: $showSearch) {
                LocationSearchView(mapManager: mapManager)
            }
            .sheet(item: $selectedListing) { listing in
                ListingDetailView(listing: listing)
            }
        }
    }
}

struct LocationSearchView: View {
    @StateObject private var mapManager: MapManager
    @State private var searchText = ""
    @State private var searchResults: [MKMapItem] = []
    @State private var isSearching = false
    
    @Environment(\.dismiss) var dismiss
    
    init(mapManager: MapManager) {
        self._mapManager = StateObject(wrappedValue: mapManager)
    }
    
    var body: some View {
        NavigationView {
            VStack {
                // Search Bar
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(.gray)
                    
                    TextField("Search location", text: $searchText)
                        .onSubmit {
                            performSearch()
                        }
                    
                    if !searchText.isEmpty {
                        Button(action: {
                            searchText = ""
                            searchResults = []
                        }) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundColor(.gray)
                        }
                    }
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(10)
                .padding()
                
                // Search Results
                if isSearching {
                    ProgressView("Searching...")
                        .padding()
                } else if searchResults.isEmpty && !searchText.isEmpty {
                    Text("No results found")
                        .foregroundColor(.secondary)
                        .padding()
                }
                
                List(searchResults, id: \.name) { item in
                    Button(action: {
                        if let coordinate = item.placemark.location?.coordinate {
                            mapManager.region = MKCoordinateRegion(
                                center: coordinate,
                                span: MKCoordinateSpan(latitudeDelta: 0.05, longitudeDelta: 0.05)
                            )
                            dismiss()
                        }
                    }) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(item.name ?? "Unknown")
                                .font(.headline)
                            if let address = item.placemark.title {
                                Text(address)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Search Location")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func performSearch() {
        guard !searchText.isEmpty else { return }
        
        isSearching = true
        
        Task {
            do {
                let results = try await mapManager.searchLocations(query: searchText)
                await MainActor.run {
                    self.searchResults = results
                    self.isSearching = false
                }
            } catch {
                await MainActor.run {
                    self.isSearching = false
                }
            }
        }
    }
}

#Preview {
    MapView(listings: [
        Listing(id: 1, seller_id: 1, crop_name: "Maize", quantity_kg: 1000, price_per_kg: 0.50, location: "Harare", status: "active", description: nil, image_urls: [], created_at: nil, latitude: -19.0154, longitude: 29.1549),
        Listing(id: 2, seller_id: 2, crop_name: "Tomatoes", quantity_kg: 500, price_per_kg: 1.20, location: "Bulawayo", status: "active", description: nil, image_urls: [], created_at: nil, latitude: -20.1505, longitude: 28.5833)
    ])
}
