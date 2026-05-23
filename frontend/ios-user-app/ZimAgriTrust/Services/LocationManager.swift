import Foundation
import CoreLocation
import Combine

@MainActor
class LocationManager: NSObject, ObservableObject {
    @Published var location: CLLocation?
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined
    @Published var authorizationError: String?
    @Published var isUpdatingLocation = false
    
    private let locationManager = CLLocationManager()
    private var locationUpdateHandler: ((CLLocation) -> Void)?
    
    override init() {
        super.init()
        setupLocationManager()
    }
    
    private func setupLocationManager() {
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBest
        locationManager.distanceFilter = 10
        
        authorizationStatus = locationManager.authorizationStatus
    }
    
    func requestAuthorization() {
        locationManager.requestWhenInUseAuthorization()
    }
    
    func requestAlwaysAuthorization() {
        locationManager.requestAlwaysAuthorization()
    }
    
    func startUpdatingLocation() {
        guard authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways else {
            authorizationError = "Location permission not granted"
            return
        }
        
        isUpdatingLocation = true
        locationManager.startUpdatingLocation()
    }
    
    func stopUpdatingLocation() {
        isUpdatingLocation = false
        locationManager.stopUpdatingLocation()
    }
    
    func requestCurrentLocation() async throws -> CLLocation {
        return try await withCheckedThrowingContinuation { continuation in
            guard authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways else {
                continuation.resume(throwing: LocationError.notAuthorized)
                return
            }
            
            locationUpdateHandler = { location in
                continuation.resume(returning: location)
                self.locationUpdateHandler = nil
            }
            
            locationManager.requestLocation()
        }
    }
    
    func startMonitoringSignificantLocationChanges() {
        guard authorizationStatus == .authorizedAlways else {
            authorizationError = "Always location permission required for background monitoring"
            return
        }
        
        locationManager.startMonitoringSignificantLocationChanges()
    }
    
    func stopMonitoringSignificantLocationChanges() {
        locationManager.stopMonitoringSignificantLocationChanges()
    }
    
    func startMonitoringRegion(region: CLRegion) {
        locationManager.startMonitoring(for: region)
    }
    
    func stopMonitoringRegion(region: CLRegion) {
        locationManager.stopMonitoring(for: region)
    }
    
    func geocodeAddress(_ address: String) async throws -> CLLocation {
        let geocoder = CLGeocoder()
        let placemarks = try await geocoder.geocodeAddressString(address)
        
        guard let location = placemarks.first?.location else {
            throw LocationError.geocodingFailed
        }
        
        return location
    }
    
    func reverseGeocode(location: CLLocation) async throws -> String {
        let geocoder = CLGeocoder()
        let placemarks = try await geocoder.reverseGeocodeLocation(location)
        
        guard let placemark = placemarks.first else {
            throw LocationError.reverseGeocodingFailed
        }
        
        var addressComponents: [String] = []
        
        if let subThoroughfare = placemark.subThoroughfare {
            addressComponents.append(subThoroughfare)
        }
        if let thoroughfare = placemark.thoroughfare {
            addressComponents.append(thoroughfare)
        }
        if let locality = placemark.locality {
            addressComponents.append(locality)
        }
        if let administrativeArea = placemark.administrativeArea {
            addressComponents.append(administrativeArea)
        }
        if let country = placemark.country {
            addressComponents.append(country)
        }
        
        return addressComponents.joined(separator: ", ")
    }
    
    func calculateDistance(from: CLLocation, to: CLLocation) -> CLLocationDistance {
        return from.distance(from: to)
    }
}

extension LocationManager: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        
        self.location = location
        locationUpdateHandler?(location)
    }
    
    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        if let clError = error as? CLError {
            switch clError.code {
            case .locationUnknown:
                authorizationError = "Location temporarily unavailable"
            case .denied:
                authorizationError = "Location permission denied"
            case .network:
                authorizationError = "Network error occurred"
            default:
                authorizationError = error.localizedDescription
            }
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didChangeAuthorization status: CLAuthorizationStatus) {
        authorizationStatus = status
        
        switch status {
        case .authorizedWhenInUse, .authorizedAlways:
            authorizationError = nil
        case .denied, .restricted:
            authorizationError = "Location permission denied"
        case .notDetermined:
            authorizationError = nil
        @unknown default:
            break
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didEnterRegion region: CLRegion) {
        NotificationCenter.default.post(name: .didEnterRegion, object: region)
    }
    
    func locationManager(_ manager: CLLocationManager, didExitRegion region: CLRegion) {
        NotificationCenter.default.post(name: .didExitRegion, object: region)
    }
}

extension Notification.Name {
    static let didEnterRegion = Notification.Name("didEnterRegion")
    static let didExitRegion = Notification.Name("didExitRegion")
}

enum LocationError: LocalizedError {
    case notAuthorized
    case geocodingFailed
    case reverseGeocodingFailed
    case locationUnknown
    
    var errorDescription: String? {
        switch self {
        case .notAuthorized:
            return "Location permission not granted"
        case .geocodingFailed:
            return "Failed to geocode address"
        case .reverseGeocodingFailed:
            return "Failed to reverse geocode location"
        case .locationUnknown:
            return "Location temporarily unavailable"
        }
    }
}
