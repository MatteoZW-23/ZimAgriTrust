import Foundation
import Combine
import CoreData
import UIKit

@MainActor
class ListingsViewModel: ObservableObject {
    @Published var listings: [Listing] = []
    @Published var filteredListings: [Listing] = []
    @Published var selectedListing: Listing?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var searchText = ""
    @Published var selectedCategory: String = "All"
    @Published var selectedLocation: String = "All"
    @Published var priceRange: ClosedRange<Double> = 0...10000
    @Published var savedListings: Set<Int> = []
    
    private var cancellables = Set<AnyCancellable>()
    private let listingService: ListingService
    private let coreDataStack: CoreDataStack
    
    let categories = ["All", "Maize", "Tomatoes", "Potatoes", "Groundnuts", "Sugar Beans"]
    let locations = ["All", "Harare", "Bulawayo", "Mutare", "Gweru", "Masvingo"]
    
    init(listingService: ListingService = .shared, coreDataStack: CoreDataStack = .shared) {
        self.listingService = listingService
        self.coreDataStack = coreDataStack
        loadListings()
        setupSearchBinding()
        loadSavedListings()
    }
    
    private func setupSearchBinding() {
        $searchText
            .combineLatest($selectedCategory, $selectedLocation, $priceRange)
            .debounce(for: .milliseconds(300), scheduler: RunLoop.main)
            .sink { [weak self] _, _, _, _ in
                self?.applyFilters()
            }
            .store(in: &cancellables)
    }
    
    func loadListings() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let fetched = try await listingService.getListings()
                await MainActor.run {
                    self.listings = fetched
                    self.applyFilters()
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
    
    func applyFilters() {
        filteredListings = listings.filter { listing in
            let matchesSearch = searchText.isEmpty ||
                listing.crop_name.localizedCaseInsensitiveContains(searchText) ||
                listing.location.localizedCaseInsensitiveContains(searchText)
            
            let matchesCategory = selectedCategory == "All" ||
                listing.crop_name == selectedCategory
            
            let matchesLocation = selectedLocation == "All" ||
                listing.location == selectedLocation
            
            let matchesPrice = listing.price_per_kg >= priceRange.lowerBound &&
                listing.price_per_kg <= priceRange.upperBound
            
            return matchesSearch && matchesCategory && matchesLocation && matchesPrice
        }
    }
    
    func createListing(cropName: String, quantityKg: Double, pricePerKg: Double, location: String, description: String, images: [UIImage]) {
        isLoading = true
        
        Task {
            do {
                let imageDataArray = try images.compactMap { image -> Data in
                    guard let data = image.jpegData(compressionQuality: 0.8) else {
                        throw NSError(domain: "ImageError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Failed to process image"])
                    }
                    return data
                }
                
                let newListing = try await listingService.createListing(
                    cropName: cropName,
                    quantityKg: quantityKg,
                    pricePerKg: pricePerKg,
                    location: location,
                    description: description,
                    images: imageDataArray
                )
                
                await MainActor.run {
                    self.isLoading = false
                    self.listings.append(newListing)
                    self.applyFilters()
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func updateListing(listingId: Int, cropName: String?, quantityKg: Double?, pricePerKg: Double?, location: String?, description: String?) {
        isLoading = true
        
        Task {
            do {
                let updated = try await listingService.updateListing(
                    listingId: listingId,
                    cropName: cropName,
                    quantityKg: quantityKg,
                    pricePerKg: pricePerKg,
                    location: location,
                    description: description
                )
                
                await MainActor.run {
                    self.isLoading = false
                    if let index = self.listings.firstIndex(where: { $0.id == listingId }) {
                        self.listings[index] = updated
                        self.applyFilters()
                    }
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func deleteListing(listingId: Int) {
        isLoading = true
        
        Task {
            do {
                _ = try await listingService.deleteListing(listingId: listingId)
                await MainActor.run {
                    self.isLoading = false
                    self.listings.removeAll { $0.id == listingId }
                    self.applyFilters()
                    self.savedListings.remove(listingId)
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func makeOffer(listingId: Int, offeredPricePerKg: Double, offeredQuantityKg: Double, message: String?) {
        isLoading = true
        
        Task {
            do {
                _ = try await listingService.makeOffer(
                    listingId: listingId,
                    offeredPricePerKg: offeredPricePerKg,
                    offeredQuantityKg: offeredQuantityKg,
                    message: message
                )
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
    
    func toggleSaveListing(listingId: Int) {
        if savedListings.contains(listingId) {
            savedListings.remove(listingId)
        } else {
            savedListings.insert(listingId)
        }
        UserDefaultsManager.shared.set(Array(savedListings), forKey: "savedListings")
    }
    
    private func loadSavedListings() {
        if let saved = UserDefaultsManager.shared.array(forKey: "savedListings") as? [Int] {
            savedListings = Set(saved)
        }
    }
    
    private func saveToCoreData(_ listings: [Listing]) {
        let context = coreDataStack.viewContext
        listings.forEach { listing in
            let entity = ListingEntity(context: context)
            entity.id = Int64(listing.id)
            entity.cropName = listing.crop_name
            entity.quantityKg = listing.quantity_kg
            entity.pricePerKg = listing.price_per_kg
            entity.location = listing.location
            entity.status = listing.status
        }
        coreDataStack.save()
    }
    
    private func loadFromCoreData() {
        let context = coreDataStack.viewContext
        let request: NSFetchRequest<ListingEntity> = ListingEntity.fetchRequest()
        
        do {
            let entities = try context.fetch(request)
            self.listings = entities.compactMap { entity in
                Listing(
                    id: Int(entity.id),
                    seller_id: 0,
                    crop_name: entity.cropName ?? "",
                    quantity_kg: entity.quantityKg,
                    price_per_kg: entity.pricePerKg,
                    location: entity.location ?? "",
                    status: entity.status ?? "active",
                    description: nil,
                    image_urls: [],
                    created_at: nil
                )
            }
            self.applyFilters()
        } catch {
            print("Core Data fetch error: \(error)")
        }
    }
}
