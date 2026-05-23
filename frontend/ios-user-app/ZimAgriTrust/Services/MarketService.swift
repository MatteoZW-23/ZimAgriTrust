//
//  MarketService.swift
//  ZimAgriTrust
//
//  Service for market-related operations
//

import Foundation

class MarketService: ObservableObject {
    static let shared = MarketService()
    
    private let apiClient = APIClient.shared
    
    @Published var prices: [MarketPrice] = []
    @Published var trendingCrops: [TrendingCrop] = []
    @Published var news: [MarketNews] = []
    @Published var summary: MarketSummary?
    
    private init() {}
    
    // MARK: - Fetch Market Prices
    
    func fetchMarketPrices() async throws {
        let response: [MarketPrice] = try await apiClient.request(
            endpoint: APIConfig.Market.prices,
            method: .get,
            requiresAuth: false
        )
        
        await MainActor.run {
            self.prices = response
        }
    }
    
    // MARK: - Fetch Trending Crops
    
    func fetchTrendingCrops() async throws {
        let response: [TrendingCrop] = try await apiClient.request(
            endpoint: APIConfig.Market.trending,
            method: .get,
            requiresAuth: false
        )
        
        await MainActor.run {
            self.trendingCrops = response
        }
    }
    
    // MARK: - Fetch Market News
    
    func fetchMarketNews() async throws {
        let response: [MarketNews] = try await apiClient.request(
            endpoint: APIConfig.Market.news,
            method: .get
        )
        
        await MainActor.run {
            self.news = response
        }
    }
    
    // MARK: - Fetch Market Summary
    
    func fetchMarketSummary() async throws {
        let response: MarketSummary = try await apiClient.request(
            endpoint: APIConfig.Market.summary,
            method: .get
        )
        
        await MainActor.run {
            self.summary = response
        }
    }
}
