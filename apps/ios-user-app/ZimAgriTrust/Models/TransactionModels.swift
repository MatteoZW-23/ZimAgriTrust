//
//  TransactionModels.swift
//  ZimAgriTrust
//
//  Transaction-related data models
//

import Foundation

// MARK: - Transaction

struct Transaction: Decodable, Identifiable {
    let id: Int
    let listing_id: Int
    let listing_title: String?
    let buyer_id: Int
    let seller_id: Int
    let buyer_name: String?
    let seller_name: String?
    let total_amount: Double
    let status: String
    let delivery_method: String?
    let delivery_code: String?
    let created_at: String
    let updated_at: String?
    
    var formattedAmount: String {
        return String(format: "$%.2f", total_amount)
    }
}

// MARK: - Delivery Confirmation

struct DeliveryConfirmationRequest: Encodable {
    let delivery_code: String
}

// MARK: - Review

struct Review: Decodable, Identifiable {
    let id: Int
    let transaction_id: Int
    let reviewer_id: Int
    let reviewer_name: String?
    let rating: Int
    let comment: String?
    let created_at: String
}

struct CreateReviewRequest: Encodable {
    let rating: Int
    let comment: String?
}
