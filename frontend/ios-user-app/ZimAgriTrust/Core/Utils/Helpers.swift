//
//  Helpers.swift
//  ZimAgriTrust
//
//  Helper functions and utilities
//

import Foundation
import SwiftUI

// MARK: - Validation Helpers

struct ValidationHelper {
    static func validatePhoneNumber(_ phone: String) -> Bool {
        return phone.isValidPhoneNumber
    }
    
    static func validateEmail(_ email: String) -> Bool {
        return email.isValidEmail
    }
    
    static func validatePIN(_ pin: String) -> Bool {
        return pin.isValidPIN
    }
    
    static func validatePassword(_ password: String) -> Bool {
        return password.count >= Constants.minPasswordLength
    }
    
    static func validatePINStrength(_ pin: String) -> PINStrength {
        if pin == "1234" || pin == "1111" || pin == "0000" {
            return .weak
        }
        
        if pin.allSatisfy({ $0 == pin.first }) {
            return .weak
        }
        
        if pin.count >= 6 {
            return .strong
        }
        
        return .medium
    }
}

enum PINStrength {
    case weak
    case medium
    case strong
    
    var color: Color {
        switch self {
        case .weak:
            return .red
        case .medium:
            return .orange
        case .strong:
            return .green
        }
    }
}

// MARK: - Image Helpers

struct ImageHelper {
    static func compressImage(_ image: UIImage, maxSizeKB: Int = 500) -> Data? {
        guard let data = image.jpegData(compressionQuality: 1.0) else { return nil }
        
        var compression: CGFloat = 1.0
        var imageData = data
        
        while imageData.count > maxSizeKB * 1024 && compression > 0.1 {
            compression -= 0.1
            guard let compressed = image.jpegData(compressionQuality: compression) else { break }
            imageData = compressed
        }
        
        return imageData
    }
    
    static func resizeImage(_ image: UIImage, targetSize: CGSize) -> UIImage {
        let size = image.size
        
        let widthRatio  = targetSize.width  / size.width
        let heightRatio = targetSize.height / size.height
        
        var newSize: CGSize
        if widthRatio > heightRatio {
            newSize = CGSize(width: size.width * heightRatio, height: size.height * heightRatio)
        } else {
            newSize = CGSize(width: size.width * widthRatio, height: size.height * widthRatio)
        }
        
        let rect = CGRect(origin: .zero, size: newSize)
        
        UIGraphicsBeginImageContextWithOptions(newSize, false, 1.0)
        image.draw(in: rect)
        let newImage = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()
        
        return newImage ?? image
    }
}

// MARK: - Date Helpers

struct DateHelper {
    static func parseISO8601(_ dateString: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.date(from: dateString)
    }
    
    static func formatISO8601(_ date: Date) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.string(from: date)
    }
}

// MARK: - Haptic Helpers

struct HapticHelper {
    static func impact(_ style: UIImpactFeedbackGenerator.FeedbackStyle = .medium) {
        let generator = UIImpactFeedbackGenerator(style: style)
        generator.impactOccurred()
    }
    
    static func notification(_ type: UINotificationFeedbackGenerator.FeedbackType) {
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(type)
    }
    
    static func selection() {
        let generator = UISelectionFeedbackGenerator()
        generator.selectionChanged()
    }
}

// MARK: - Animation Helpers

struct AnimationHelper {
    static func spring(response: Double = 0.5, dampingFraction: Double = 0.7) -> Animation {
        .spring(response: response, dampingFraction: dampingFraction)
    }
    
    static func easeInOut(duration: Double = 0.3) -> Animation {
        .easeInOut(duration: duration)
    }
}

// MARK: - Formatter Helpers

struct FormatterHelper {
    static let currency: NumberFormatter = {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "USD"
        return formatter
    }()
    
    static let number: NumberFormatter = {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.maximumFractionDigits = 2
        return formatter
    }()
    
    static let percentage: NumberFormatter = {
        let formatter = NumberFormatter()
        formatter.numberStyle = .percent
        formatter.maximumFractionDigits = 1
        return formatter
    }()
}

// MARK: - Cache Helpers

struct CacheHelper {
    static func clearCache() {
        let cacheURL = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        
        if let enumerator = FileManager.default.enumerator(at: cacheURL, includingPropertiesForKeys: nil) {
            for case let fileURL as URL in enumerator {
                try? FileManager.default.removeItem(at: fileURL)
            }
        }
    }
    
    static func getCacheSize() -> Int {
        let cacheURL = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        var totalSize = 0
        
        if let enumerator = FileManager.default.enumerator(at: cacheURL, includingPropertiesForKeys: [.fileSizeKey]) {
            for case let fileURL as URL in enumerator {
                if let resourceValues = try? fileURL.resourceValues(forKeys: [.fileSizeKey]),
                   let fileSize = resourceValues.fileSize {
                    totalSize += fileSize
                }
            }
        }
        
        return totalSize
    }
    
    static func formatCacheSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }
}
