import Foundation

// MARK: - Common Models

struct User: Codable {
    let id: Int
    let full_name: String
    let email: String?
    let phone_number: String
    let trust_score: Double
    let is_verified: Bool
    let created_at: String?
}

struct Listing: Codable, Identifiable {
    let id: Int
    let seller_id: Int
    let crop_name: String
    let quantity_kg: Double
    let price_per_kg: Double
    let location: String
    let status: String
    let description: String?
    let image_urls: [String]
    let created_at: String?
    let latitude: Double?
    let longitude: Double?
}

struct Transaction: Codable, Identifiable {
    let id: Int
    let listing_id: Int
    let buyer_id: Int
    let seller_id: Int
    let status: String
    let total_amount: Double
    let currency: String
    let created_at: String?
}

struct Delivery: Codable, Identifiable {
    let id: Int
    let transaction_id: Int
    let status: String
    let pickup_address: String
    let delivery_address: String
    let pickup_time: String?
    let delivery_time: String?
    let notes: String?
}

struct Driver: Codable {
    let id: Int
    let name: String
    let phone_number: String
    let vehicle_type: String?
    let license_plate: String?
    let rating: Double?
}

struct DriverRegistration: Codable {
    let name: String
    let phone_number: String
    let vehicle_type: String
    let license_plate: String
    let id_document_url: String?
}

struct TransportSurvey: Codable {
    let transaction_id: Int
    let delivery_time: Int
    let fuel_consumption: Double?
    let road_condition: String?
    let notes: String?
}

// MARK: - Common Enums

enum TransactionStatus: String, Codable {
    case pending = "pending"
    case confirmed = "confirmed"
    case pickedUp = "picked_up"
    case inTransit = "in_transit"
    case delivered = "delivered"
    case cancelled = "cancelled"
}

enum DeliveryStatus: String, Codable {
    case pending = "pending"
    case assigned = "assigned"
    case pickedUp = "picked_up"
    case inTransit = "in_transit"
    case delivered = "delivered"
}

// MARK: - Common Errors

enum APIError: LocalizedError {
    case invalidURL
    case networkError
    case authenticationFailed
    case serverError(String)
    case decodingError
    case unknown
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .networkError:
            return "Network error occurred"
        case .authenticationFailed:
            return "Authentication failed"
        case .serverError(let message):
            return message
        case .decodingError:
            return "Failed to decode response"
        case .unknown:
            return "An unknown error occurred"
        }
    }
}
