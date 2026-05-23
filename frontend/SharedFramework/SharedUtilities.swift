import Foundation
import UIKit

// MARK: - Date Utilities

extension Date {
    func formatted(format: String = "yyyy-MM-dd HH:mm:ss") -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = format
        return formatter.string(from: self)
    }
    
    func timeAgo() -> String {
        let seconds = Int(Date().timeIntervalSince(self))
        
        if seconds < 60 {
            return "Just now"
        } else if seconds < 3600 {
            let minutes = seconds / 60
            return "\(minutes)m ago"
        } else if seconds < 86400 {
            let hours = seconds / 3600
            return "\(hours)h ago"
        } else if seconds < 604800 {
            let days = seconds / 86400
            return "\(days)d ago"
        } else {
            let formatter = DateFormatter()
            formatter.dateStyle = .short
            return formatter.string(from: self)
        }
    }
}

// MARK: - String Utilities

extension String {
    var isValidEmail: Bool {
        let emailRegex = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
        let emailPredicate = NSPredicate(format: "SELF MATCHES %@", emailRegex)
        return emailPredicate.evaluate(with: self)
    }
    
    var isValidPhoneNumber: Bool {
        let phoneRegex = "^\\+?[0-9]{10,15}$"
        let phonePredicate = NSPredicate(format: "SELF MATCHES %@", phoneRegex)
        return phonePredicate.evaluate(with: self)
    }
    
    func formattedCurrency(currencyCode: String = "USD") -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = currencyCode
        return formatter.string(from: NSNumber(value: Double(self) ?? 0)) ?? self
    }
}

// MARK: - Image Utilities

extension UIImage {
    func resized(to size: CGSize) -> UIImage {
        UIGraphicsBeginImageContextWithOptions(size, false, scale)
        defer { UIGraphicsEndImageContext() }
        draw(in: CGRect(origin: .zero, size: size))
        return UIGraphicsGetImageFromCurrentImageContext() ?? self
    }
    
    func compressed(quality: CGFloat = 0.8) -> Data? {
        return jpegData(compressionQuality: quality)
    }
}

// MARK: - Validation Utilities

class Validator {
    static func validateEmail(_ email: String) -> Bool {
        return email.isValidEmail
    }
    
    static func validatePhoneNumber(_ phone: String) -> Bool {
        return phone.isValidPhoneNumber
    }
    
    static func validatePassword(_ password: String) -> Bool {
        return password.count >= 8
    }
    
    static func validateQuantity(_ quantity: Double) -> Bool {
        return quantity > 0
    }
    
    static func validatePrice(_ price: Double) -> Bool {
        return price > 0
    }
}

// MARK: - Storage Utilities

class StorageManager {
    static let shared = StorageManager()
    
    private let userDefaults = UserDefaults.standard
    
    private init() {}
    
    func save<T: Codable>(_ value: T, forKey key: String) {
        if let encoded = try? JSONEncoder().encode(value) {
            userDefaults.set(encoded, forKey: key)
        }
    }
    
    func load<T: Codable>(forKey key: String) -> T? {
        guard let data = userDefaults.data(forKey: key),
              let decoded = try? JSONDecoder().decode(T.self, from: data) else {
            return nil
        }
        return decoded
    }
    
    func remove(forKey key: String) {
        userDefaults.removeObject(forKey: key)
    }
    
    func bool(forKey key: String) -> Bool {
        return userDefaults.bool(forKey: key)
    }
    
    func set(_ value: Bool, forKey key: String) {
        userDefaults.set(value, forKey: key)
    }
}

// MARK: - Logging Utilities

class Logger {
    static func log(_ message: String, level: LogLevel = .info) {
        let timestamp = Date().formatted()
        print("[\(timestamp)] [\(level.rawValue)] \(message)")
    }
    
    static func error(_ message: String) {
        log(message, level: .error)
    }
    
    static func warning(_ message: String) {
        log(message, level: .warning)
    }
    
    static func info(_ message: String) {
        log(message, level: .info)
    }
    
    static func debug(_ message: String) {
        #if DEBUG
        log(message, level: .debug)
        #endif
    }
}

enum LogLevel: String {
    case debug = "DEBUG"
    case info = "INFO"
    case warning = "WARNING"
    case error = "ERROR"
}
