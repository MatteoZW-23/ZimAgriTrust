import UIKit
import SwiftUI

class AppClipViewController: UIViewController {
    var listingURL: URL?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        loadListing()
    }
    
    private func setupUI() {
        view.backgroundColor = .systemBackground
        
        let hostingController = UIHostingController(rootView: AppClipView(listingURL: listingURL))
        addChild(hostingController)
        view.addSubview(hostingController.view)
        hostingController.view.translatesAutoresizingMaskIntoConstraints = false
        
        NSLayoutConstraint.activate([
            hostingController.view.topAnchor.constraint(equalTo: view.topAnchor),
            hostingController.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            hostingController.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            hostingController.view.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
        
        hostingController.didMove(toParent: self)
    }
    
    private func loadListing() {
        guard let url = listingURL else { return }
        
        // Parse URL to extract listing ID
        if let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
           let queryItems = components.queryItems,
           let listingIDItem = queryItems.first(where: { $0.name == "listing_id" }),
           let listingID = listingIDItem.value {
            // Load listing details
            Task {
                await loadListingDetails(id: Int(listingID) ?? 0)
            }
        }
    }
    
    private func loadListingDetails(id: Int) async {
        // Fetch listing details from API
        // This would call the actual API in production
    }
}

struct AppClipView: View {
    var listingURL: URL?
    @State private var listing: Listing?
    @State private var isLoading = true
    
    var body: some View {
        NavigationView {
            ZStack {
                if isLoading {
                    ProgressView("Loading listing...")
                } else if let listing = listing {
                    ListingClipDetailView(listing: listing)
                } else {
                    VStack {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.system(size: 60))
                            .foregroundColor(.orange)
                        Text("Listing not found")
                            .font(.headline)
                        Text("The listing may have been removed")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("ZimAgriTrust")
            .navigationBarTitleDisplayMode(.inline)
        }
        .task {
            if let url = listingURL {
                await loadListing(from: url)
            }
        }
    }
    
    private func loadListing(from url: URL) async {
        // Parse URL and fetch listing
        isLoading = false
    }
}

struct ListingClipDetailView: View {
    let listing: Listing
    @State private var showFullApp = false
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Listing Image
                if let imageURL = listing.image_urls.first {
                    AsyncImage(url: URL(string: imageURL)) { phase in
                        switch phase {
                        case .empty:
                            ProgressView()
                        case .success(let image):
                            image
                                .resizable()
                                .scaledToFill()
                                .frame(height: 200)
                                .clipped()
                        case .failure:
                            Image(systemName: "photo")
                                .font(.system(size: 60))
                                .foregroundColor(.gray)
                        @unknown default:
                            EmptyView()
                        }
                    }
                } else {
                    Rectangle()
                        .fill(Color.gray.opacity(0.2))
                        .frame(height: 200)
                        .overlay(
                            Image(systemName: "photo")
                                .font(.system(size: 60))
                                .foregroundColor(.gray)
                        )
                }
                
                VStack(alignment: .leading, spacing: 8) {
                    Text(listing.crop_name)
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    HStack {
                        Text("\(Int(listing.quantity_kg)) kg")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        
                        Spacer()
                        
                        Text("$\(String(format: "%.2f", listing.price_per_kg))/kg")
                            .font(.headline)
                            .foregroundColor(.green)
                    }
                    
                    HStack {
                        Image(systemName: "location.fill")
                            .foregroundColor(.blue)
                        Text(listing.location)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    if let description = listing.description {
                        Text(description)
                            .font(.body)
                            .padding(.top, 8)
                    }
                }
                .padding()
                
                Divider()
                
                // Download App CTA
                VStack(spacing: 12) {
                    Button(action: {
                        showFullApp = true
                    }) {
                        HStack {
                            Image(systemName: "app.badge")
                                .font(.title3)
                            Text("Download ZimAgriTrust")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    
                    Text("Get the full app to make offers, track deliveries, and more")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding()
            }
        }
        .sheet(isPresented: $showFullApp) {
            if let appURL = URL(string: "zimagritrust://listing/\(listing.id)") {
                UIApplication.shared.open(appURL)
            }
        }
    }
}

#Preview {
    AppClipView(listingURL: URL(string: "https://zimagritrust.com/clip?listing_id=123"))
}
