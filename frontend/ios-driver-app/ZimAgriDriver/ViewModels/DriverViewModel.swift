import Foundation
import Combine
import CoreData

@MainActor
class DriverViewModel: ObservableObject {
    @Published var deliveries: [Delivery] = []
    @Published var activeDelivery: Delivery?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var currentLocation: CLLocationCoordinate2D?
    
    private let driverService: DriverService
    private let locationManager: LocationManager
    private let coreDataStack: CoreDataStack
    private var cancellables = Set<AnyCancellable>()
    
    init(driverService: DriverService = .shared, locationManager: LocationManager = .shared, coreDataStack: CoreDataStack = .shared) {
        self.driverService = driverService
        self.locationManager = locationManager
        self.coreDataStack = coreDataStack
        loadDeliveries()
        setupLocationTracking()
    }
    
    func loadDeliveries() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let fetched = try await driverService.getDeliveries()
                await MainActor.run {
                    self.deliveries = fetched
                    self.activeDelivery = fetched.first { $0.status == "in_transit" || $0.status == "picked_up" }
                    self.isLoading = false
                    self.saveToCoreData(fetched)
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                    self.loadFromCoreData()
                }
            }
        }
    }
    
    func confirmPickup(deliveryId: Int, notes: String? = nil) {
        isLoading = true
        
        Task {
            do {
                _ = try await driverService.confirmPickup(deliveryId: deliveryId, notes: notes)
                await MainActor.run {
                    self.isLoading = false
                    self.loadDeliveries()
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func confirmDelivery(deliveryId: Int, notes: String? = nil, signatureData: Data? = nil) {
        isLoading = true
        
        Task {
            do {
                _ = try await driverService.confirmDelivery(
                    deliveryId: deliveryId,
                    notes: notes,
                    signature: signatureData
                )
                await MainActor.run {
                    self.isLoading = false
                    self.loadDeliveries()
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func submitTransportSurvey(survey: TransportSurvey) {
        isLoading = true
        
        Task {
            do {
                _ = try await driverService.submitTransportSurvey(survey: survey)
                await MainActor.run {
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    private func setupLocationTracking() {
        locationManager.startUpdatingLocation()
        
        locationManager.$location
            .compactMap { $0 }
            .sink { [weak self] location in
                self?.currentLocation = location.coordinate
                self?.updateDriverLocation(location.coordinate)
            }
            .store(in: &cancellables)
    }
    
    private func updateDriverLocation(_ coordinate: CLLocationCoordinate2D) {
        Task {
            do {
                _ = try await driverService.updateLocation(
                    latitude: coordinate.latitude,
                    longitude: coordinate.longitude
                )
            } catch {
                print("Failed to update location: \(error)")
            }
        }
    }
    
    private func saveToCoreData(_ deliveries: [Delivery]) {
        let context = coreDataStack.viewContext
        deliveries.forEach { delivery in
            let entity = DeliveryEntity(context: context)
            entity.id = Int64(delivery.id)
            entity.status = delivery.status
            entity.pickupAddress = delivery.pickup_address
            entity.deliveryAddress = delivery.delivery_address
        }
        coreDataStack.save()
    }
    
    private func loadFromCoreData() {
        let context = coreDataStack.viewContext
        let request: NSFetchRequest<DeliveryEntity> = DeliveryEntity.fetchRequest()
        
        do {
            let entities = try context.fetch(request)
            self.deliveries = entities.compactMap { entity in
                Delivery(
                    id: Int(entity.id),
                    transaction_id: 0,
                    status: entity.status ?? "unknown",
                    pickup_address: entity.pickupAddress ?? "",
                    delivery_address: entity.deliveryAddress ?? "",
                    pickup_time: nil,
                    delivery_time: nil,
                    notes: nil
                )
            }
        } catch {
            print("Core Data fetch error: \(error)")
        }
    }
}
