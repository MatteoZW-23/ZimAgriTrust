//
//  Constants.swift
//  ZimAgriTrust
//
//  App-wide constants
//

import Foundation

struct Constants {
    // MARK: - App Info
    static let appName = "ZimAgriTrust"
    static let appVersion = "1.0.0"
    static let bundleID = "com.zimagritrust.ios"
    
    // MARK: - API
    static let apiTimeout: TimeInterval = 30.0
    static let apiTimeoutForResource: TimeInterval = 60.0
    
    // MARK: - Pagination
    static let defaultPageSize = 20
    static let maxPageSize = 100
    
    // MARK: - Validation
    static let minPINLength = 4
    static let maxPINLength = 6
    static let minPasswordLength = 8
    static let maxPasswordLength = 128
    
    // MARK: - Images
    static let maxImageSize: Int = 10 * 1024 * 1024 // 10MB
    static let maxImageCount = 5
    static let allowedImageTypes = ["jpg", "jpeg", "png", "heic"]
    
    // MARK: - Location
    static let defaultLocationRadius: Double = 50.0 // km
    static let locationUpdateInterval: TimeInterval = 30.0 // seconds
    
    // MARK: - Cache
    static let cacheExpirationDays = 7
    static let maxCacheSize: Int = 100 * 1024 * 1024 // 100MB
    
    // MARK: - UI
    static let animationDuration: Double = 0.3
    static let cornerRadius: CGFloat = 12.0
    
    // MARK: - Zimbabwe Provinces
    static let provinces = [
        "Harare",
        "Bulawayo",
        "Manicaland",
        "Mashonaland Central",
        "Mashonaland East",
        "Mashonaland West",
        "Masvingo",
        "Matabeleland North",
        "Matabeleland South",
        "Midlands"
    ]
    
    // MARK: - Crop Types
    static let cropTypes = [
        "Maize",
        "Tomato",
        "Soybeans",
        "Groundnuts",
        "Cabbage",
        "Potato",
        "Onion",
        "Sugar Beans",
        "Sunflower",
        "Tobacco",
        "Cotton",
        "Mango"
    ]
    
    // MARK: - Vehicle Types
    static let vehicleTypes = [
        "Motorcycle",
        "Car",
        "Van",
        "Truck"
    ]
    
    // MARK: - Languages
    static let languages = [
        "en": "English",
        "sn": "Shona",
        "nd": "Ndebele"
    ]
    
    // MARK: - Currencies
    static let currencies = [
        "USD": "US Dollar",
        "ZWL": "Zimbabwe Dollar"
    ]
}
