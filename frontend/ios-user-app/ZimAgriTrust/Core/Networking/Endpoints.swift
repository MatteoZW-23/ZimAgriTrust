//
//  Endpoints.swift
//  ZimAgriTrust
//
//  API endpoint definitions
//

import Foundation

struct Endpoints {
    // MARK: - Authentication
    static let login = "/auth/app/login"
    static let verify2FA = "/auth/verify-login-2fa"
    static let register = "/auth/register"
    static let refreshToken = "/auth/refresh"
    static let forgotPassword = "/auth/forgot-password"
    static let resetPassword = "/auth/reset-password"
    static let dataExport = "/auth/data-export"
    static let deactivate = "/auth/deactivate"
    
    // MARK: - User
    static let profile = "/users/me"
    static let trustScore = "/users/trust-score"
    static let settings = "/users/settings"
    
    // MARK: - Listings
    static let listings = "/public/listings"
    static let search = "/listings/search"
    static let createListing = "/listings"
    static let myListings = "/listings/me"
    static let savedListings = "/listings/me/saved"
    static let listingDetail = "/listings"
    
    // MARK: - Offers
    static let receivedOffers = "/offers/received"
    static let madeOffers = "/offers/made"
    
    // MARK: - Wallet
    static let wallet = "/wallet"
    static let deposit = "/wallet/deposit"
    static let withdraw = "/wallet/withdraw"
    static let transactions = "/wallet/transactions"
    
    // MARK: - Transactions
    static let transactions = "/transactions"
    static let transactionDetail = "/transactions"
    
    // MARK: - Market
    static let prices = "/public/prices/current"
    static let trending = "/public/prices/trending"
    static let news = "/market/news"
    static let summary = "/market/summary"
}
