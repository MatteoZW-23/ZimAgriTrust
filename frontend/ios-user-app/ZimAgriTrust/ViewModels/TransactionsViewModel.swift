import Foundation
import Combine
import CoreData

@MainActor
class TransactionsViewModel: ObservableObject {
    @Published var transactions: [Transaction] = []
    @Published var filteredTransactions: [Transaction] = []
    @Published var selectedTransaction: Transaction?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var selectedFilter: TransactionFilter = .all
    
    private var cancellables = Set<AnyCancellable>()
    private let transactionService: TransactionService
    private let coreDataStack: CoreDataStack
    
    enum TransactionFilter: String, CaseIterable {
        case all = "All"
        case pending = "Pending"
        case completed = "Completed"
        case cancelled = "Cancelled"
        case inTransit = "In Transit"
    }
    
    init(transactionService: TransactionService = .shared, coreDataStack: CoreDataStack = .shared) {
        self.transactionService = transactionService
        self.coreDataStack = coreDataStack
        loadTransactions()
    }
    
    func loadTransactions() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let fetched = try await transactionService.getTransactions()
                await MainActor.run {
                    self.transactions = fetched
                    self.applyFilter()
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
    
    func applyFilter() {
        switch selectedFilter {
        case .all:
            filteredTransactions = transactions
        case .pending:
            filteredTransactions = transactions.filter { $0.status == "pending" }
        case .completed:
            filteredTransactions = transactions.filter { $0.status == "completed" }
        case .cancelled:
            filteredTransactions = transactions.filter { $0.status == "cancelled" }
        case .inTransit:
            filteredTransactions = transactions.filter { $0.status == "in_transit" }
        }
    }
    
    func confirmDelivery(transactionId: Int, rating: Int, comment: String?) {
        isLoading = true
        
        Task {
            do {
                _ = try await transactionService.confirmDelivery(
                    transactionId: transactionId,
                    rating: rating,
                    comment: comment
                )
                await MainActor.run {
                    self.isLoading = false
                    self.loadTransactions()
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func cancelTransaction(transactionId: Int, reason: String) {
        isLoading = true
        
        Task {
            do {
                _ = try await transactionService.cancelTransaction(
                    transactionId: transactionId,
                    reason: reason
                )
                await MainActor.run {
                    self.isLoading = false
                    self.loadTransactions()
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    private func saveToCoreData(_ transactions: [Transaction]) {
        let context = coreDataStack.viewContext
        transactions.forEach { transaction in
            let entity = TransactionEntity(context: context)
            entity.id = Int64(transaction.id)
            entity.status = transaction.status
            entity.totalAmount = transaction.total_amount
            entity.createdAt = Date()
        }
        coreDataStack.save()
    }
    
    private func loadFromCoreData() {
        let context = coreDataStack.viewContext
        let request: NSFetchRequest<TransactionEntity> = TransactionEntity.fetchRequest()
        
        do {
            let entities = try context.fetch(request)
            self.transactions = entities.compactMap { entity in
                Transaction(
                    id: Int(entity.id),
                    listing_id: 0,
                    buyer_id: 0,
                    seller_id: 0,
                    status: entity.status ?? "unknown",
                    total_amount: entity.totalAmount,
                    currency: "USD",
                    created_at: nil
                )
            }
            self.applyFilter()
        } catch {
            print("Core Data fetch error: \(error)")
        }
    }
}
