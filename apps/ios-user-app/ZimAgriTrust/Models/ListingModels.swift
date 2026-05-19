//
//  ListingModels.swift
//  ZimAgriTrust
//
//  Listing-related data models
//

import Foundation

// MARK: - Listing

struct Listing: Decodable, Identifiable {
    let id: Int
    let title: String
    let description: String
    let crop_type: String
    let quantity_kg: Double
    let price_per_kg: Double
    let location: String?
    let province: String?
    let district: String?
    let seller_id: Int
    let seller_name: String?
    let seller_phone: String?
    let status: String
    let images: [String]?
    let created_at: String
    let updated_at: String?
    
    var totalPrice: Double {
        return quantity_kg * price_per_kg
    }
}

struct CreateListingRequest: Encodable {
    let title: String
    let description: String
    let crop_type: String
    let quantity_kg: Double
    let price_per_kg: Double
    let location: String?
    let province: String?
    let district: String?
}

struct UpdateListingRequest: Encodable {
    let title: String?
    let description: String?
    let quantity_kg: Double?
    let price_per_kg: Double?
    let location: String?
    let status: String?
}

// MARK: - Search Filters

struct ListingFilters: Encodable {
    let crop_type: String?
    let province: String?
    let district: String?
    let min_price: Double?
    let max_price: Double?
    let min_quantity: Double?
    let status: String?
}

// MARK: - Offer

struct Offer: Decodable, Identifiable {
    let id: Int
    let listing_id: Int
    let buyer_id: Int
    let buyer_name: String?
    let offered_price_per_kg: Double
    let offered_quantity_kg: Double
    let total_price: Double
    let status: String
    let message: String?
    let created_at: String
}

struct CreateOfferRequest: Encodable {
    let offered_price_per_kg: Double
    let offered_quantity_kg: Double
    let message: String?
}
