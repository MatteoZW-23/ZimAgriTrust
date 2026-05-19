//
//  MarketplaceViewModel.swift
//  ZimAgriTrust
//
//  Marketplace view model with Combine
//

import Foundation
import Combine

@MainActor
class MarketplaceViewModel: ObservableObject {
    @Published var listings: [Listing] = []
    @Published var filteredListings: [Listing] = []
    @Published var searchText = ""
    @Published var selectedFilter: String = "All"
    @Published var isLoading = false
    @Published var errorMessage = ""
    @Published var currentPage = 1
    @Published var hasMorePages = true
    
    private let apiClient = APIClient.shared
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        setupBindings()
    }
    
    private func setupBindings() {
        $searchText
            .combineLatest($selectedFilter)
            .debounce(for: .milliseconds(300), scheduler: DispatchQueue.main)
            .sink { [weak self] in self?.filterListings() }
            .store(in: &cancellables)
    }
    
    // MARK: - Fetch Listings
    
    func fetchListings(refresh: Bool = false) {
        if refresh {
            currentPage = 1
            hasMorePages = true
        }
        
        guard !isLoading else { return }
        
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let response: [Listing] = try await apiClient.request(
                    endpoint: "\(Endpoints.listings)?page=\(currentPage)&limit=\(Constants.defaultPageSize)",
                    method: .get,
                    requiresAuth: false
                )
                
                if refresh {
                    listings = response
                } else {
                    listings.append(contentsOf: response)
                }
                
                hasMorePages = response.count == Constants.defaultPageSize
                filterListings()
                
                isLoading = false
            } catch {
                errorMessage = error.localizedDescription
                isLoading = false
            }
        }
    }
    
    // MARK: - Filter Listings
    
    private func filterListings() {
        filteredListings = listings.filter { listing in
            let matchesSearch = searchText.isEmpty ||
                listing.title.localizedCaseInsensitiveContains(searchText) ||
                listing.crop_type.localizedCaseInsensitiveContains(searchText)
            
            let matchesFilter = selectedFilter == "All" ||
                listing.crop_type.localizedCaseInsensitiveContains(selectedFilter)
            
            return matchesSearch && matchesFilter
        }
    }
    
    // MARK: - Load More
    
    func loadMore() {
        guard hasMorePages, !isLoading else { return }
        currentPage += 1
        fetchListings()
    }
    
    // MARK: - Save Listing
    
    func saveListing(_ listing: Listing) {
        Task {
            do {
                let _: [String: String] = try await apiClient.request(
                    endpoint: "\(Endpoints.listingDetail)/\(listing.id)/save",
                    method: .post
                )
                HapticHelper.selection()
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
    
    // MARK: - Report Listing
    
    func reportListing(_ listing: Listing, reason: String) {
        Task {
            do {
                let _: [String: String] = try await apiClient.request(
                    endpoint: "\(Endpoints.listingDetail)/\(listing.id)/report",
                    method: .post,
                    body: ["reason": reason]
                )
                HapticHelper.notification(.success)
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}
