import Foundation
import CloudKit
import Combine

@MainActor
class CloudKitManager: ObservableObject {
    static let shared = CloudKitManager()
    
    private let container = CKContainer(identifier: "iCloud.com.zimagritrust.ios")
    private let privateDatabase: CKDatabase
    private let publicDatabase: CKDatabase
    
    @Published var isSyncing = false
    @Published var syncError: String?
    
    private init() {
        self.privateDatabase = container.privateCloudDatabase
        self.publicDatabase = container.publicCloudDatabase
    }
    
    func checkAccountStatus() async throws -> CKAccountStatus {
        return try await container.accountStatus()
    }
    
    // MARK: - Save Data
    
    func saveListing(_ listing: Listing) async throws {
        isSyncing = true
        defer { isSyncing = false }
        
        let record = CKRecord(recordType: "Listing")
        record["id"] = listing.id
        record["cropName"] = listing.crop_name
        record["quantity"] = listing.quantity_kg
        record["price"] = listing.price_per_kg
        record["location"] = listing.location
        record["status"] = listing.status
        record["sellerId"] = listing.seller_id
        
        try await privateDatabase.save(record)
    }
    
    func saveTransaction(_ transaction: Transaction) async throws {
        isSyncing = true
        defer { isSyncing = false }
        
        let record = CKRecord(recordType: "Transaction")
        record["id"] = transaction.id
        record["listingId"] = transaction.listing_id
        record["buyerId"] = transaction.buyer_id
        record["sellerId"] = transaction.seller_id
        record["status"] = transaction.status
        record["totalAmount"] = transaction.total_amount
        record["currency"] = transaction.currency
        
        try await privateDatabase.save(record)
    }
    
    func saveUserProfile(_ user: User) async throws {
        isSyncing = true
        defer { isSyncing = false }
        
        let record = CKRecord(recordType: "UserProfile")
        record["id"] = user.id
        record["fullName"] = user.full_name
        record["email"] = user.email
        record["phoneNumber"] = user.phone_number
        record["trustScore"] = user.trust_score
        
        try await privateDatabase.save(record)
    }
    
    // MARK: - Fetch Data
    
    func fetchListings() async throws -> [Listing] {
        isSyncing = true
        defer { isSyncing = false }
        
        let query = CKQuery(recordType: "Listing", predicate: NSPredicate(value: true))
        let (records, _) = try await privateDatabase.records(matching: query)
        
        return records.compactMap { record in
            guard let listingRecord = record.1 else { return nil }
            return Listing(
                id: listingRecord["id"] as? Int ?? 0,
                seller_id: listingRecord["sellerId"] as? Int ?? 0,
                crop_name: listingRecord["cropName"] as? String ?? "",
                quantity_kg: listingRecord["quantity"] as? Double ?? 0,
                price_per_kg: listingRecord["price"] as? Double ?? 0,
                location: listingRecord["location"] as? String ?? "",
                status: listingRecord["status"] as? String ?? "unknown",
                description: nil,
                image_urls: [],
                created_at: nil
            )
        }
    }
    
    func fetchTransactions() async throws -> [Transaction] {
        isSyncing = true
        defer { isSyncing = false }
        
        let query = CKQuery(recordType: "Transaction", predicate: NSPredicate(value: true))
        let (records, _) = try await privateDatabase.records(matching: query)
        
        return records.compactMap { record in
            guard let transactionRecord = record.1 else { return nil }
            return Transaction(
                id: transactionRecord["id"] as? Int ?? 0,
                listing_id: transactionRecord["listingId"] as? Int ?? 0,
                buyer_id: transactionRecord["buyerId"] as? Int ?? 0,
                seller_id: transactionRecord["sellerId"] as? Int ?? 0,
                status: transactionRecord["status"] as? String ?? "unknown",
                total_amount: transactionRecord["totalAmount"] as? Double ?? 0,
                currency: transactionRecord["currency"] as? String ?? "USD",
                created_at: nil
            )
        }
    }
    
    // MARK: - Delete Data
    
    func deleteListing(id: Int) async throws {
        isSyncing = true
        defer { isSyncing = false }
        
        let predicate = NSPredicate(format: "id == %d", id)
        let query = CKQuery(recordType: "Listing", predicate: predicate)
        let (records, _) = try await privateDatabase.records(matching: query)
        
        for (_, record) in records {
            try await privateDatabase.deleteRecord(withID: record.recordID)
        }
    }
    
    // MARK: - Sync
    
    func syncWithLocalData(listings: [Listing], transactions: [Transaction]) async throws {
        isSyncing = true
        defer { isSyncing = false }
        
        // Save listings to CloudKit
        for listing in listings {
            try? await saveListing(listing)
        }
        
        // Save transactions to CloudKit
        for transaction in transactions {
            try? await saveTransaction(transaction)
        }
    }
    
    // MARK: - Subscribe to Changes
    
    func subscribeToChanges() async throws {
        let subscription = CKQuerySubscription(
            recordType: "Listing",
            predicate: NSPredicate(value: true),
            subscriptionID: "listingChanges"
        )
        
        subscription.notificationInfo = CKSubscription.NotificationInfo()
        
        try await privateDatabase.save(subscription)
    }
}
