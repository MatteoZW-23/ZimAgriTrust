import Foundation
import MapKit
import Combine
import CoreLocation

@MainActor
class MapManager: NSObject, ObservableObject {
    @Published var region: MKCoordinateRegion = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: -19.0154, longitude: 29.1549), // Zimbabwe center
        span: MKCoordinateSpan(latitudeDelta: 5.0, longitudeDelta: 5.0)
    )
    @Published var annotations: [MKAnnotation] = []
    @Published var routes: [MKRoute] = []
    @Published var selectedAnnotation: MKAnnotation?
    @Published var isCalculatingRoute = false
    
    private let locationManager = CLLocationManager()
    private let geocoder = CLGeocoder()
    
    override init() {
        super.init()
        setupLocationManager()
    }
    
    private func setupLocationManager() {
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBest
    }
    
    func centerOnUserLocation() {
        guard let location = locationManager.location else {
            requestLocationAuthorization()
            return
        }
        
        region = MKCoordinateRegion(
            center: location.coordinate,
            span: MKCoordinateSpan(latitudeDelta: 0.05, longitudeDelta: 0.05)
        )
    }
    
    func requestLocationAuthorization() {
        locationManager.requestWhenInUseAuthorization()
    }
    
    func addAnnotation(for listing: Listing) {
        let annotation = ListingAnnotation(
            coordinate: CLLocationCoordinate2D(latitude: listing.latitude ?? -19.0154, longitude: listing.longitude ?? 29.1549),
            title: listing.crop_name,
            subtitle: "\(listing.quantity_kg) kg - $\(listing.price_per_kg)/kg",
            listing: listing
        )
        
        annotations.append(annotation)
    }
    
    func addAnnotations(for listings: [Listing]) {
        listings.forEach { addAnnotation(for: $0) }
    }
    
    func clearAnnotations() {
        annotations.removeAll()
    }
    
    func selectAnnotation(_ annotation: MKAnnotation) {
        selectedAnnotation = annotation
        
        if let coordinate = annotation.coordinate as? CLLocationCoordinate2D {
            region = MKCoordinateRegion(
                center: coordinate,
                span: MKCoordinateSpan(latitudeDelta: 0.1, longitudeDelta: 0.1)
            )
        }
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
        let response = try await directions.calculate()
        
        guard let route = response.routes.first else {
            throw MapError.noRouteFound
        }
        
        isCalculatingRoute = false
        routes = [route]
        
        return route
    }
    
    func searchLocations(query: String) async throws -> [MKMapItem] {
        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = query
        request.region = region
        
        let search = MKLocalSearch(request: request)
        let response = try await search.start()
        
        return response.mapItems
    }
    
    func geocodeAddress(_ address: String) async throws -> CLLocationCoordinate2D {
        let placemarks = try await geocoder.geocodeAddressString(address)
        
        guard let location = placemarks.first?.location else {
            throw MapError.geocodingFailed
        }
        
        return location.coordinate
    }
    
    func reverseGeocode(coordinate: CLLocationCoordinate2D) async throws -> String {
        let location = CLLocation(latitude: coordinate.latitude, longitude: coordinate.longitude)
        let placemarks = try await geocoder.reverseGeocodeLocation(location)
        
        guard let placemark = placemarks.first else {
            throw MapError.reverseGeocodingFailed
        }
        
        return [placemark.subThoroughfare, placemark.thoroughfare, placemark.locality, placemark.administrativeArea, placemark.country]
            .compactMap { $0 }
            .joined(separator: ", ")
    }
    
    func openInMaps(coordinate: CLLocationCoordinate2D) {
        let placemark = MKPlacemark(coordinate: coordinate)
        let mapItem = MKMapItem(placemark: placemark)
        mapItem.name = "Location"
        mapItem.openInMaps(launchOptions: nil)
    }
    
    func getDirectionsTo(coordinate: CLLocationCoordinate2D) {
        let placemark = MKPlacemark(coordinate: coordinate)
        let mapItem = MKMapItem(placemark: placemark)
        
        let options = [MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDriving]
        mapItem.openInMaps(launchOptions: options)
    }
}

extension MapManager: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        
        region = MKCoordinateRegion(
            center: location.coordinate,
            span: MKCoordinateSpan(latitudeDelta: 0.05, longitudeDelta: 0.05)
        )
    }
    
    func locationManager(_ manager: CLLocationManager, didChangeAuthorization status: CLAuthorizationStatus) {
        if status == .authorizedWhenInUse || status == .authorizedAlways {
            centerOnUserLocation()
        }
    }
}

class ListingAnnotation: NSObject, MKAnnotation {
    let coordinate: CLLocationCoordinate2D
    let title: String?
    let subtitle: String?
    let listing: Listing
    
    init(coordinate: CLLocationCoordinate2D, title: String?, subtitle: String?, listing: Listing) {
        self.coordinate = coordinate
        self.title = title
        self.subtitle = subtitle
        self.listing = listing
        super.init()
    }
}

enum MapError: LocalizedError {
    case noRouteFound
    case geocodingFailed
    case reverseGeocodingFailed
    
    var errorDescription: String? {
        switch self {
        case .noRouteFound:
            return "No route could be found"
        case .geocodingFailed:
            return "Failed to geocode address"
        case .reverseGeocodingFailed:
            return "Failed to reverse geocode location"
        }
    }
}
