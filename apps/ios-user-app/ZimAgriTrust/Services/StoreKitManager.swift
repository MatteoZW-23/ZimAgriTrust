import Foundation
import StoreKit

@MainActor
class StoreKitManager: NSObject, ObservableObject {
    @Published var products: [Product] = []
    @Published var purchasedProductIDs: Set<String> = []
    @Published var isPurchasing = false
    @Published var errorMessage: String?
    
    private var updateListenerTask: Task<Void, Error>?
    
    // Product IDs
    enum ProductID: String, CaseIterable {
        case premiumMonthly = "com.zimagritrust.premium.monthly"
        case premiumYearly = "com.zimagritrust.premium.yearly"
        case featuredListing = "com.zimagritrust.featured.listing"
        case verificationBadge = "com.zimagritrust.verification.badge"
    }
    
    override init() {
        super.init()
        updateListenerTask = listenForTransactions()
    }
    
    deinit {
        updateListenerTask?.cancel()
    }
    
    func loadProducts() async {
        do {
            let storeProducts = try await Product.products(for: ProductID.allCases.map { $0.rawValue })
            self.products = storeProducts.sorted { $0.price < $1.price }
        } catch {
            self.errorMessage = "Failed to load products: \(error.localizedDescription)"
        }
    }
    
    func purchase(_ product: Product) async throws -> Transaction? {
        isPurchasing = true
        
        defer {
            isPurchasing = false
        }
        
        let result = try await product.purchase()
        
        switch result {
        case .success(let verification):
            let transaction = try checkVerified(verification)
            await updatePurchasedProductIDs()
            await transaction.finish()
            return transaction
            
        case .userCancelled:
            errorMessage = "Purchase cancelled"
            return nil
            
        case .pending:
            errorMessage = "Purchase pending approval"
            return nil
            
        @unknown default:
            errorMessage = "Unknown purchase result"
            return nil
        }
    }
    
    func restorePurchases() async {
        isPurchasing = true
        
        defer {
            isPurchasing = false
        }
        
        try? await AppStore.sync()
        await updatePurchasedProductIDs()
    }
    
    func checkVerified<T>(_ verification: VerificationResult<T>) throws -> T {
        switch verification {
        case .verified(let safe):
            return safe
        case .unverified:
            throw StoreError.failedVerification
        }
    }
    
    private func listenForTransactions() -> Task<Void, Error> {
        return Task.detached {
            for await result in Transaction.updates {
                do {
                    let transaction = try self.checkVerified(result)
                    await self.updatePurchasedProductIDs()
                    await transaction.finish()
                } catch {
                    await MainActor.run {
                        self.errorMessage = "Transaction verification failed: \(error.localizedDescription)"
                    }
                }
            }
        }
    }
    
    private func updatePurchasedProductIDs() async {
        var purchasedIDs = Set<String>()
        
        for await result in Transaction.currentEntitlements {
            do {
                let transaction = try checkVerified(result)
                purchasedIDs.insert(transaction.productID)
            } catch {
                continue
            }
        }
        
        self.purchasedProductIDs = purchasedIDs
    }
    
    func hasPurchased(_ productID: ProductID) -> Bool {
        purchasedProductIDs.contains(productID.rawValue)
    }
    
    func isPremiumUser() -> Bool {
        hasPurchased(.premiumMonthly) || hasPurchased(.premiumYearly)
    }
    
    func hasVerificationBadge() -> Bool {
        hasPurchased(.verificationBadge)
    }
    
    func subscriptionStatus() async -> SubscriptionStatus? {
        guard isPremiumUser() else { return nil }
        
        for await result in Transaction.currentEntitlements {
            do {
                let transaction = try checkVerified(result)
                if transaction.productID == ProductID.premiumMonthly.rawValue || transaction.productID == ProductID.premiumYearly.rawValue {
                    let renewalInfo = try checkVerified(transaction.latestRenewalInfo)
                    
                    return SubscriptionStatus(
                        productID: transaction.productID,
                        state: renewalInfo.state,
                        expirationDate: renewalInfo.expirationDate
                    )
                }
            } catch {
                continue
            }
        }
        
        return nil
    }
}

struct SubscriptionStatus {
    let productID: String
    let state: ProductSubscriptionInfo.RenewalState
    let expirationDate: Date?
}

enum StoreError: LocalizedError {
    case failedVerification
    
    var errorDescription: String? {
        switch self {
        case .failedVerification:
            return "Failed to verify transaction"
        }
    }
}
