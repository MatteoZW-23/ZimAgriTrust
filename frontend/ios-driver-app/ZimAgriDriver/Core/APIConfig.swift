import Foundation

struct APIConfig {
    static let baseURL = "http://localhost:8080/api/v1"
    static let apiVersion = "v1"
    static let timeout: TimeInterval = 30.0
    
    #if DEBUG
    static let environment = "development"
    #else
    static let environment = "production"
    #endif
}
