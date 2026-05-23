//
//  APIConfig.swift
//  ZimAgriTrust
//
//  API configuration
//

import Foundation

struct APIConfig {
    // Base URL - set this to your production backend URL
    #if DEBUG
    static let baseURL = "http://localhost:8080/api/v1"
    #else
    static let baseURL = "https://api.zimagritrust.com/api/v1"
    #endif
    
    static let apiVersion = "v1"
    static let timeout: TimeInterval = 30.0
}
