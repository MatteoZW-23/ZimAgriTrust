import Foundation

struct Endpoints {
    struct Auth {
        static let requestOTP = "/auth/driver/request-otp"
        static let verifyOTP = "/auth/driver/verify-otp"
        static let register = "/drivers/self-register"
    }
    
    struct Deliveries {
        static let list = "/drivers/deliveries"
        static let detail = "/drivers/deliveries"
        static let updateStatus = "/drivers/deliveries"
        static let confirmPickup = "/drivers/deliveries"
        static let confirmDelivery = "/drivers/deliveries"
    }
    
    struct Transport {
        static let submitSurvey = "/drivers/transport-survey"
        static let updateLocation = "/drivers/location"
    }
    
    struct Profile {
        static let get = "/drivers/me"
        static let update = "/drivers/me"
    }
}
