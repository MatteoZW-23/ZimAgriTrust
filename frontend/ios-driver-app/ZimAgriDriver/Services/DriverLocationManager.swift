import Foundation
import CoreLocation
import Combine

@MainActor
class DriverLocationManager: NSObject, ObservableObject {
    @Published var currentLocation: CLLocation?
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined
    @Published var isTrackingInBackground = false
    @Published var errorMessage: String?
    
    private let locationManager = CLLocationManager()
    private var locationUpdateTimer: Timer?
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid
    
    override init() {
        super.init()
        setupLocationManager()
    }
    
    private func setupLocationManager() {
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
        locationManager.distanceFilter = 10
        locationManager.allowsBackgroundLocationUpdates = true
        locationManager.pausesLocationUpdatesAutomatically = false
        
        authorizationStatus = locationManager.authorizationStatus
    }
    
    func requestAlwaysAuthorization() {
        locationManager.requestAlwaysAuthorization()
    }
    
    func startForegroundTracking() {
        guard authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways else {
            errorMessage = "Location permission not granted"
            return
        }
        
        locationManager.startUpdatingLocation()
    }
    
    func startBackgroundTracking() {
        guard authorizationStatus == .authorizedAlways else {
            errorMessage = "Always location permission required for background tracking"
            return
        }
        
        isTrackingInBackground = true
        locationManager.startUpdatingLocation()
        
        // Start background task
        backgroundTask = UIApplication.shared.beginBackgroundTask(withName: "LocationTracking") { [weak self] in
            self?.endBackgroundTask()
        }
        
        // Set up periodic location updates
        locationUpdateTimer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            self?.uploadCurrentLocation()
        }
    }
    
    func stopBackgroundTracking() {
        isTrackingInBackground = false
        locationManager.stopUpdatingLocation()
        locationUpdateTimer?.invalidate()
        locationUpdateTimer = nil
        endBackgroundTask()
    }
    
    private func endBackgroundTask() {
        if backgroundTask != .invalid {
            UIApplication.shared.endBackgroundTask(backgroundTask)
            backgroundTask = .invalid
        }
    }
    
    private func uploadCurrentLocation() {
        guard let location = currentLocation else { return }
        
        Task {
            do {
                _ = try await DriverService.shared.updateLocation(
                    latitude: location.coordinate.latitude,
                    longitude: location.coordinate.longitude
                )
            } catch {
                print("Failed to upload location: \(error)")
            }
        }
    }
    
    func startMonitoringRegion(region: CLRegion) {
        locationManager.startMonitoring(for: region)
    }
    
    func stopMonitoringRegion(region: CLRegion) {
        locationManager.stopMonitoring(for: region)
    }
    
    func createGeofenceAroundDelivery(pickupLocation: CLLocationCoordinate2D, deliveryLocation: CLLocationCoordinate2D, radius: Double = 100) {
        let pickupRegion = CLCircularRegion(center: pickupLocation, radius: radius, identifier: "pickup")
        pickupRegion.notifyOnEntry = true
        pickupRegion.notifyOnExit = false
        
        let deliveryRegion = CLCircularRegion(center: deliveryLocation, radius: radius, identifier: "delivery")
        deliveryRegion.notifyOnEntry = true
        deliveryRegion.notifyOnExit = false
        
        startMonitoringRegion(region: pickupRegion)
        startMonitoringRegion(region: deliveryRegion)
    }
}

extension DriverLocationManager: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        
        currentLocation = location
        
        // If tracking in background, upload location immediately
        if isTrackingInBackground {
            uploadCurrentLocation()
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        if let clError = error as? CLError {
            switch clError.code {
            case .locationUnknown:
                errorMessage = "Location temporarily unavailable"
            case .denied:
                errorMessage = "Location permission denied"
            case .network:
                errorMessage = "Network error occurred"
            default:
                errorMessage = error.localizedDescription
            }
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didChangeAuthorization status: CLAuthorizationStatus) {
        authorizationStatus = status
        
        switch status {
        case .authorizedAlways:
            errorMessage = nil
        case .authorizedWhenInUse:
            errorMessage = nil
        case .denied, .restricted:
            errorMessage = "Location permission denied"
        case .notDetermined:
            errorMessage = nil
        @unknown default:
            break
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didEnterRegion region: CLRegion) {
        NotificationCenter.default.post(name: .didEnterRegion, object: region)
        
        if region.identifier == "pickup" {
            // Notify driver they've arrived at pickup location
            sendLocalNotification(title: "Arrived at Pickup", body: "You've reached the pickup location")
        } else if region.identifier == "delivery" {
            // Notify driver they've arrived at delivery location
            sendLocalNotification(title: "Arrived at Delivery", body: "You've reached the delivery location")
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didExitRegion region: CLRegion) {
        NotificationCenter.default.post(name: .didExitRegion, object: region)
    }
    
    private func sendLocalNotification(title: String, body: String) {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        
        let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
        UNUserNotificationCenter.current().add(request)
    }
}

extension Notification.Name {
    static let didEnterRegion = Notification.Name("driverDidEnterRegion")
    static let didExitRegion = Notification.Name("driverDidExitRegion")
}
