import Foundation
import MapKit
import Combine

@MainActor
class DriverRouteManager: NSObject, ObservableObject {
    @Published var currentRoute: MKRoute?
    @Published var estimatedTimeRemaining: TimeInterval?
    @Published var distanceRemaining: CLLocationDistance?
    @Published var isCalculatingRoute = false
    @Published var errorMessage: String?
    
    private let locationManager = CLLocationManager()
    private var directions: MKDirections?
    
    override init() {
        super.init()
        locationManager.delegate = self
    }
    
    func calculateRoute(from source: CLLocationCoordinate2D, to destination: CLLocationCoordinate2D, transportType: MKDirectionsTransportType = .automobile) async throws -> MKRoute {
        isCalculatingRoute = true
        
        let sourcePlacemark = MKPlacemark(coordinate: source)
        let destinationPlacemark = MKPlacemark(coordinate: destination)
        
        let request = MKDirections.Request()
        request.source = MKMapItem(placemark: sourcePlacemark)
        request.destination = MKMapItem(placemark: destinationPlacemark)
        request.transportType = transportType
        request.requestsAlternateRoutes = false
        
        let directions = MKDirections(request: request)
        self.directions = directions
        
        do {
            let response = try await directions.calculate()
            
            guard let route = response.routes.first else {
                throw RouteError.noRouteFound
            }
            
            currentRoute = route
            estimatedTimeRemaining = route.expectedTravelTime
            distanceRemaining = route.distance
            isCalculatingRoute = false
            
            return route
        } catch {
            isCalculatingRoute = false
            throw error
        }
    }
    
    func calculateRouteToDelivery(pickupLocation: CLLocationCoordinate2D, deliveryLocation: CLLocationCoordinate2D) async throws -> (pickupRoute: MKRoute, deliveryRoute: MKRoute) {
        guard let currentLocation = locationManager.location?.coordinate else {
            throw RouteError.locationNotAvailable
        }
        
        let pickupRoute = try await calculateRoute(from: currentLocation, to: pickupLocation)
        let deliveryRoute = try await calculateRoute(from: pickupLocation, to: deliveryLocation)
        
        return (pickupRoute, deliveryRoute)
    }
    
    func startNavigation(to destination: CLLocationCoordinate2D) {
        let placemark = MKPlacemark(coordinate: destination)
        let mapItem = MKMapItem(placemark: placemark)
        mapItem.name = "Destination"
        
        let options = [MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDriving]
        mapItem.openInMaps(launchOptions: options)
    }
    
    func getRouteInstructions() -> [RouteInstruction] {
        guard let route = currentRoute else { return [] }
        
        return route.steps.enumerated().map { index, step in
            RouteInstruction(
                step: index + 1,
                instruction: step.instructions,
                distance: step.distance,
                transportType: step.transportType
            )
        }
    }
    
    func getNextInstruction() -> RouteInstruction? {
        guard let route = currentRoute else { return nil }
        
        if let firstStep = route.steps.first {
            return RouteInstruction(
                step: 1,
                instruction: firstStep.instructions,
                distance: firstStep.distance,
                transportType: firstStep.transportType
            )
        }
        
        return nil
    }
    
    func updateProgress(currentLocation: CLLocationCoordinate2D) {
        guard let route = currentRoute else { return }
        
        let currentCLLocation = CLLocation(latitude: currentLocation.latitude, longitude: currentLocation.longitude)
        var remainingDistance: CLLocationDistance = 0
        var remainingTime: TimeInterval = 0
        
        for step in route.steps {
            let stepPolyline = step.polyline
            let stepLocation = CLLocation(latitude: stepPolyline.coordinate.latitude, longitude: stepPolyline.coordinate.longitude)
            
            if currentCLLocation.distance(from: stepLocation) < step.distance {
                remainingDistance += step.distance - currentCLLocation.distance(from: stepLocation)
                remainingTime += step.expectedTravelTime
            } else {
                remainingDistance += step.distance
                remainingTime += step.expectedTravelTime
            }
        }
        
        distanceRemaining = remainingDistance
        estimatedTimeRemaining = remainingTime
    }
}

struct RouteInstruction {
    let step: Int
    let instruction: String
    let distance: CLLocationDistance
    let transportType: MKDirectionsTransportType
}

enum RouteError: LocalizedError {
    case noRouteFound
    case locationNotAvailable
    
    var errorDescription: String? {
        switch self {
        case .noRouteFound:
            return "No route could be found"
        case .locationNotAvailable:
            return "Current location not available"
        }
    }
}

extension DriverRouteManager: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        updateProgress(currentLocation: location.coordinate)
    }
}
