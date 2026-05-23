//
//  APIConfig.swift
//  ZimAgriTrust
//
//  API Configuration for ZimAgriTrust Backend
//

import Foundation

struct APIConfig {
    // Base URL - set this to your production backend URL
    #if DEBUG
    static let baseURL = "http://localhost:8080/api/v1"
    #else
    static let baseURL = "https://api.zimagritrust.com/api/v1"
    #endif
    
    // API Endpoints
    struct Auth {
        static let login = "/auth/app/login"
        static let verify2FA = "/auth/verify-login-2fa"
        static let register = "/auth/register"
        static let refreshToken = "/auth/refresh"
        static let forgotPassword = "/auth/forgot-password"
        static let resetPassword = "/auth/reset-password"
        static let dataExport = "/auth/data-export"
        static let deactivate = "/auth/deactivate"
    }
    
    struct User {
        static let profile = "/users/me"
        static let trustScore = "/users/trust-score"
        static let settings = "/users/settings"
    }
    
    struct Listings {
        static let all = "/public/listings"
        static let search = "/listings/search"
        static let create = "/listings"
        static let myListings = "/listings/me"
        static let saved = "/listings/me/saved"
        static let details = "/listings"
    }
    
    struct Wallet {
        static let balance = "/wallet"
        static let deposit = "/wallet/deposit"
        static let withdraw = "/wallet/withdraw"
        static let transactions = "/wallet/transactions"
    }
    
    struct Transactions {
        static let all = "/transactions"
        static let details = "/transactions"
    }
    
    struct Offers {
        static let received = "/offers/received"
        static let made = "/offers/made"
    }
    
    struct Market {
        static let prices = "/public/prices/current"
        static let trending = "/public/prices/trending"
        static let news = "/market/news"
        static let summary = "/market/summary"
    }
}
