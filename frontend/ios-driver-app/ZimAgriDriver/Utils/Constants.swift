import Foundation

struct Constants {
    struct App {
        static let name = "ZimAgriDriver"
        static let version = "1.0.0"
        static let bundleIdentifier = "com.zimagritrust.driver"
    }
    
    struct API {
        static let baseURL = APIConfig.baseURL
        static let timeout: TimeInterval = 30.0
    }
    
    struct Location {
        static let defaultZoomLevel: Double = 0.05
        static let geofenceRadius: Double = 100.0 // meters
        static let locationUpdateInterval: TimeInterval = 30.0 // seconds
        static let backgroundLocationUpdateInterval: TimeInterval = 60.0 // seconds
    }
    
    struct Delivery {
        static let maxDeliveryDistance: Double = 50000.0 // meters (50km)
        static let pickupTimeout: TimeInterval = 1800.0 // 30 minutes
        static let deliveryTimeout: TimeInterval = 3600.0 // 1 hour
    }
    
    struct Storage {
        static let driverProfileKey = "driverProfile"
        static let lastLocationKey = "lastLocation"
        static let activeDeliveryKey = "activeDelivery"
    }
    
    struct Notification {
        static let pickupArrived = "driver_pickup_arrived"
        static let deliveryArrived = "driver_delivery_arrived"
        static let newDeliveryAssigned = "new_delivery_assigned"
        static let deliveryUpdated = "delivery_updated"
    }
}
