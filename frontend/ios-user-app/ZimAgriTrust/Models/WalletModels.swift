//
//  WalletModels.swift
//  ZimAgriTrust
//
//  Wallet-related data models
//

import Foundation

// MARK: - Wallet Balance

struct WalletBalance: Decodable {
    let balance_usd: Double
    let pending_usd: Double
    let available_usd: Double
    let currency: String?
    
    var formattedBalance: String {
        return String(format: "$%.2f", balance_usd)
    }
    
    var formattedAvailable: String {
        return String(format: "$%.2f", available_usd)
    }
}

// MARK: - Wallet Transaction

struct WalletTransaction: Decodable, Identifiable {
    let id: Int
    let type: String
    let amount: Double
    let status: String
    let description: String?
    let created_at: String
    
    var formattedAmount: String {
        let prefix = type == "credit" ? "+" : "-"
        return "\(prefix)$\(String(format: "%.2f", amount))"
    }
}

// MARK: - Deposit/Withdraw

struct DepositRequest: Encodable {
    let amount: Double
    let payment_method: String
    let reference: String?
}

struct WithdrawRequest: Encodable {
    let amount: Double
    let bank_account: String
    let bank_name: String
}

// MARK: - Fee Preview

struct FeePreview: Decodable {
    let amount: Double
    let fee: Double
    let total: Double
    let currency: String
}
