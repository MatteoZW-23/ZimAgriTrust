//
//  APIConfig.swift
//  ZimAgriDriver
//
//  API Configuration for ZimAgriTrust Driver Backend
//

import Foundation

struct APIConfig {
    // Base URL - set this to your production backend URL
    #if DEBUG
    static let baseURL = "http://localhost:8080/api/v1"
    #else
    static let baseURL = "https://api.zimagritrust.com/api/v1"
    #endif
    
    // Driver-specific endpoints
    struct Auth {
        static let requestOTP = "/auth/driver/request-otp"
        static let verifyOTP = "/auth/driver/verify-otp"
        static let selfRegister = "/drivers/self-register"
        static let refreshToken = "/auth/refresh"
    }
    
    struct Delivery {
        static let getDelivery = "/logistics/orders"
        static let updateStatus = "/logistics/orders"
        static let confirmPickup = "/logistics/orders"
        static let confirmDelivery = "/logistics/orders"
    }
    
    struct Transport {
        static let submitSurvey = "/transactions"
    }
}
