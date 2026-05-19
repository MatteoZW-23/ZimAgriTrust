//
//  MarketModels.swift
//  ZimAgriTrust
//
//  Market-related data models
//

import Foundation

// MARK: - Market Price

struct MarketPrice: Decodable, Identifiable {
    let id: Int?
    let crop_type: String
    let price_per_kg: Double
    let change_percent: Double?
    let date: String?
    
    var formattedPrice: String {
        return String(format: "$%.2f/kg", price_per_kg)
    }
    
    var changeIndicator: String {
        guard let change = change_percent else { return "—" }
        return change >= 0 ? "↑ \(String(format: "%.1f", change))%" : "↓ \(String(format: "%.1f", abs(change)))%"
    }
}

// MARK: - Trending Crop

struct TrendingCrop: Decodable, Identifiable {
    let id: Int?
    let crop_type: String
    let demand_score: Double
    let price_trend: String
}

// MARK: - Market News

struct MarketNews: Decodable, Identifiable {
    let id: Int?
    let title: String
    let summary: String?
    let url: String?
    let published_at: String
    let source: String?
}

// MARK: - Market Summary

struct MarketSummary: Decodable {
    let total_listings: Int
    let active_transactions: Int
    let total_volume_kg: Double
    let average_price: Double
    let top_crops: [String]
}
