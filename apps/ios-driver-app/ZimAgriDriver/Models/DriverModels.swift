//
//  DriverModels.swift
//  ZimAgriDriver
//
//  Driver-related data models
//

import Foundation

// MARK: - OTP Authentication

struct RequestOTPRequest: Encodable {
    let phone_number: String
}

struct RequestOTPResponse: Decodable {
    let message: String
    let expires_in: Int?
}

struct VerifyOTPRequest: Encodable {
    let phone_number: String
    let otp: String
}

struct VerifyOTPResponse: Decodable {
    let access_token: String
    let refresh_token: String
    let driver_id: Int
    let driver_name: String
}

// MARK: - Self Registration

struct SelfRegisterRequest: Encodable {
    let phone_number: String
    let full_name: String
    let id_number: String
    let vehicle_type: String
    let license_plate: String
}

struct SelfRegisterResponse: Decodable {
    let message: String
    let driver_id: Int?
}

// MARK: - Delivery

struct Delivery: Decodable, Identifiable {
    let id: Int
    let order_id: Int
    let listing_title: String?
    let pickup_address: String
    let delivery_address: String
    let seller_name: String?
    let buyer_name: String?
    let quantity_kg: Double
    let status: String
    let delivery_code: String?
    let scheduled_pickup: String?
    let scheduled_delivery: String?
    let created_at: String
}

struct DeliveryStatusUpdate: Encodable {
    let status: String
    let notes: String?
}

// MARK: - Transport Survey

struct TransportSurveyRequest: Encodable {
    let vehicle_condition: String
    let road_condition: String
    let weather_condition: String
    let delivery_time: Int
    let fuel_consumption: Double?
    let notes: String?
}
