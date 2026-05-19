import Foundation
import Intents

@available(iOS 12.0, *)
class SearchListingsIntent: NSObject, INIntentHandler {
    func handle(intent: SearchListingsIntentInput, completion: @escaping (SearchListingsIntentResponse) -> Void) {
        Task {
            do {
                let listings = try await searchListings(crop: intent.crop, location: intent.location)
                let response = SearchListingsIntentResponse.success(listings: listings)
                completion(response)
            } catch {
                completion(SearchListingsIntentResponse.failure(error: error.localizedDescription))
            }
        }
    }
    
    private func searchListings(crop: String?, location: String?) async throws -> [Listing] {
        // Call the actual API to search listings
        // For now, return mock data
        return [
            Listing(id: 1, seller_id: 1, crop_name: crop ?? "Maize", quantity_kg: 500, price_per_kg: 0.50, location: location ?? "Harare", status: "active", description: nil, image_urls: [], created_at: nil)
        ]
    }
}

@available(iOS 12.0, *)
class SearchListingsIntentInput: INIntent {
    @NSManaged public var crop: String?
    @NSManaged public var location: String?
}

@available(iOS 12.0, *)
class SearchListingsIntentResponse: INIntentResponse {
    public var listings: [Listing]?
    
    convenience init(success listings: [Listing]) {
        self.init(code: .success, userActivity: nil)
        self.listings = listings
    }
    
    convenience init(failure error: String) {
        self.init(code: .failure, userActivity: nil)
    }
}

@available(iOS 12.0, *)
class CreateListingIntent: NSObject, INIntentHandler {
    func handle(intent: CreateListingIntentInput, completion: @escaping (CreateListingIntentResponse) -> Void) {
        Task {
            do {
                let listing = try await createListing(
                    crop: intent.crop,
                    quantity: intent.quantity,
                    price: intent.price,
                    location: intent.location
                )
                let response = CreateListingIntentResponse.success(listing: listing)
                completion(response)
            } catch {
                completion(CreateListingIntentResponse.failure(error: error.localizedDescription))
            }
        }
    }
    
    private func createListing(crop: String, quantity: Double, price: Double, location: String) async throws -> Listing {
        // Call the actual API to create listing
        // For now, return mock data
        return Listing(
            id: 1,
            seller_id: 1,
            crop_name: crop,
            quantity_kg: quantity,
            price_per_kg: price,
            location: location,
            status: "active",
            description: nil,
            image_urls: [],
            created_at: nil
        )
    }
}

@available(iOS 12.0, *)
class CreateListingIntentInput: INIntent {
    @NSManaged public var crop: String?
    @NSManaged public var quantity: NSNumber?
    @NSManaged public var price: NSNumber?
    @NSManaged public var location: String?
}

@available(iOS 12.0, *)
class CreateListingIntentResponse: INIntentResponse {
    public var listing: Listing?
    
    convenience init(success listing: Listing) {
        self.init(code: .success, userActivity: nil)
        self.listing = listing
    }
    
    convenience init(failure error: String) {
        self.init(code: .failure, userActivity: nil)
    }
}

@available(iOS 12.0, *)
class CheckWalletBalanceIntent: NSObject, INIntentHandler {
    func handle(intent: INIntent, completion: @escaping (CheckWalletBalanceIntentResponse) -> Void) {
        Task {
            do {
                let balance = try await getWalletBalance()
                let response = CheckWalletBalanceIntentResponse.success(balance: balance)
                completion(response)
            } catch {
                completion(CheckWalletBalanceIntentResponse.failure(error: error.localizedDescription))
            }
        }
    }
    
    private func getWalletBalance() async throws -> WalletBalance {
        // Call the actual API to get wallet balance
        // For now, return mock data
        return WalletBalance(available: 500.0, pending: 100.0, total: 600.0, currency: "USD")
    }
}

@available(iOS 12.0, *)
class CheckWalletBalanceIntentResponse: INIntentResponse {
    public var balance: WalletBalance?
    
    convenience init(success balance: WalletBalance) {
        self.init(code: .success, userActivity: nil)
        self.balance = balance
    }
    
    convenience init(failure error: String) {
        self.init(code: .failure, userActivity: nil)
    }
}

struct WalletBalance {
    let available: Double
    let pending: Double
    let total: Double
    let currency: String
}
