//
//  ListingService.swift
//  ZimAgriTrust
//
//  Service for listing-related operations
//

import Foundation

class ListingService: ObservableObject {
    static let shared = ListingService()
    
    private let apiClient = APIClient.shared
    
    @Published var listings: [Listing] = []
    @Published var myListings: [Listing] = []
    @Published var savedListings: [Listing] = []
    
    private init() {}
    
    // MARK: - Fetch Listings
    
    func fetchListings(filters: ListingFilters? = nil) async throws {
        var endpoint = APIConfig.Listings.all
        
        if let filters = filters {
            var components = URLComponents(string: APIConfig.baseURL + APIConfig.Listings.search)
            components?.queryItems = [
                URLQueryItem(name: "crop_type", value: filters.crop_type),
                URLQueryItem(name: "province", value: filters.province),
                URLQueryItem(name: "district", value: filters.district),
                URLQueryItem(name: "min_price", value: filters.min_price?.description),
                URLQueryItem(name: "max_price", value: filters.max_price?.description),
                URLQueryItem(name: "min_quantity", value: filters.min_quantity?.description),
                URLQueryItem(name: "status", value: filters.status)
            ].filter { $0.value != nil }
            
            if let url = components?.url?.absoluteString {
                endpoint = url.replacingOccurrences(of: APIConfig.baseURL, with: "")
            }
        }
        
        let response: [Listing] = try await apiClient.request(
            endpoint: endpoint,
            method: .get,
            requiresAuth: false
        )
        
        await MainActor.run {
            self.listings = response
        }
    }
    
    // MARK: - Fetch My Listings
    
    func fetchMyListings() async throws {
        let response: [Listing] = try await apiClient.request(
            endpoint: APIConfig.Listings.myListings,
            method: .get
        )
        
        await MainActor.run {
            self.myListings = response
        }
    }
    
    // MARK: - Fetch Saved Listings
    
    func fetchSavedListings() async throws {
        let response: [Listing] = try await apiClient.request(
            endpoint: APIConfig.Listings.saved,
            method: .get
        )
        
        await MainActor.run {
            self.savedListings = response
        }
    }
    
    // MARK: - Fetch Listing Details
    
    func fetchListingDetails(id: Int) async throws -> Listing {
        let response: Listing = try await apiClient.request(
            endpoint: "\(APIConfig.Listings.details)/\(id)",
            method: .get
        )
        return response
    }
    
    // MARK: - Create Listing
    
    func createListing(_ request: CreateListingRequest) async throws -> Listing {
        let response: Listing = try await apiClient.request(
            endpoint: APIConfig.Listings.create,
            method: .post,
            body: request
        )
        
        await MainActor.run {
            self.myListings.append(response)
        }
        
        return response
    }
    
    // MARK: - Update Listing
    
    func updateListing(id: Int, _ request: UpdateListingRequest) async throws -> Listing {
        let response: Listing = try await apiClient.request(
            endpoint: "\(APIConfig.Listings.details)/\(id)",
            method: .put,
            body: request
        )
        
        await MainActor.run {
            if let index = myListings.firstIndex(where: { $0.id == id }) {
                myListings[index] = response
            }
        }
        
        return response
    }
    
    // MARK: - Delete Listing
    
    func deleteListing(id: Int) async throws {
        let _: [String: String] = try await apiClient.request(
            endpoint: "\(APIConfig.Listings.details)/\(id)",
            method: .delete
        )
        
        await MainActor.run {
            self.myListings.removeAll { $0.id == id }
        }
    }
    
    // MARK: - Save Listing
    
    func saveListing(id: Int) async throws {
        let _: [String: String] = try await apiClient.request(
            endpoint: "\(APIConfig.Listings.details)/\(id)/save",
            method: .post
        )
    }
    
    // MARK: - Report Listing
    
    func reportListing(id: Int, reason: String) async throws {
        let _: [String: String] = try await apiClient.request(
            endpoint: "\(APIConfig.Listings.details)/\(id)/report",
            method: .post,
            body: ["reason": reason]
        )
    }
}
