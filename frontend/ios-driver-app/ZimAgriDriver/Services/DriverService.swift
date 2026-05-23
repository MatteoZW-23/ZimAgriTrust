//
//  DriverService.swift
//  ZimAgriDriver
//
//  Service for driver authentication and delivery management
//

import Foundation
import CoreLocation

class DriverService {
    static let shared = DriverService()
    
    private let apiClient = APIClient.shared
    
    private init() {}
    
    // MARK: - OTP Authentication
    
    func requestOTP(phoneNumber: String) async throws {
        let request = OTPRequest(phone_number: phoneNumber)
        _ = try await apiClient.post(Endpoints.Auth.requestOTP, body: request)
    }
    
    func verifyOTP(phoneNumber: String, otp: String) async throws -> AuthResponse {
        let request = OTPVerifyRequest(phone_number: phoneNumber, otp: otp)
        return try await apiClient.post(Endpoints.Auth.verifyOTP, body: request)
    }
    
    // MARK: - Self Registration
    
    func register(driver: DriverRegistration) async throws -> AuthResponse {
        return try await apiClient.post(Endpoints.Auth.register, body: driver)
    }
    
    // MARK: - Deliveries
    
    func getDeliveries() async throws -> [Delivery] {
        return try await apiClient.get(Endpoints.Deliveries.list)
    }
    
    func getDeliveryDetails(deliveryId: Int) async throws -> Delivery {
        return try await apiClient.get("\(Endpoints.Deliveries.detail)/\(deliveryId)")
    }
    
    func updateDeliveryStatus(deliveryId: Int, status: String, notes: String? = nil) async throws {
        let body = ["status": status, "notes": notes ?? ""]
        _ = try await apiClient.put("\(Endpoints.Deliveries.updateStatus)/\(deliveryId)", body: body)
    }
    
    func confirmPickup(deliveryId: Int, notes: String? = nil) async throws {
        let body = ["notes": notes ?? ""]
        _ = try await apiClient.post("\(Endpoints.Deliveries.confirmPickup)/\(deliveryId)/pickup", body: body)
    }
    
    func confirmDelivery(deliveryId: Int, notes: String? = nil, signature: Data? = nil) async throws {
        var body: [String: Any] = ["notes": notes ?? ""]
        if let signature = signature {
            body["signature"] = signature.base64EncodedString()
        }
        _ = try await apiClient.post("\(Endpoints.Deliveries.confirmDelivery)/\(deliveryId)/confirm-delivery", body: body)
    }
    
    // MARK: - Transport Survey
    
    func submitTransportSurvey(survey: TransportSurvey) async throws {
        _ = try await apiClient.post(Endpoints.Transport.submitSurvey, body: survey)
    }
    
    // MARK: - Location Updates
    
    func updateLocation(latitude: Double, longitude: Double) async throws {
        let body = ["latitude": latitude, "longitude": longitude]
        _ = try await apiClient.post(Endpoints.Transport.updateLocation, body: body)
    }
}
