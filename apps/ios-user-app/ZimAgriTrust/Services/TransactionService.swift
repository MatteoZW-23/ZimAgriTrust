//
//  TransactionService.swift
//  ZimAgriTrust
//
//  Service for transaction-related operations
//

import Foundation

class TransactionService: ObservableObject {
    static let shared = TransactionService()
    
    private let apiClient = APIClient.shared
    
    @Published var transactions: [Transaction] = []
    
    private init() {}
    
    // MARK: - Fetch Transactions
    
    func fetchTransactions() async throws {
        let response: [Transaction] = try await apiClient.request(
            endpoint: APIConfig.Transactions.all,
            method: .get
        )
        
        await MainActor.run {
            self.transactions = response
        }
    }
    
    // MARK: - Fetch Transaction Details
    
    func fetchTransactionDetails(id: Int) async throws -> Transaction {
        let response: Transaction = try await apiClient.request(
            endpoint: "\(APIConfig.Transactions.details)/\(id)",
            method: .get
        )
        return response
    }
    
    // MARK: - Confirm Delivery
    
    func confirmDelivery(transactionId: Int, deliveryCode: String) async throws {
        let request = DeliveryConfirmationRequest(delivery_code: deliveryCode)
        let _: [String: String] = try await apiClient.request(
            endpoint: "\(APIConfig.Transactions.details)/\(transactionId)/confirm-delivery",
            method: .post,
            body: request
        )
        
        await fetchTransactions()
    }
    
    // MARK: - Create Review
    
    func createReview(transactionId: Int, _ request: CreateReviewRequest) async throws {
        let _: [String: String] = try await apiClient.request(
            endpoint: "\(APIConfig.Transactions.details)/\(transactionId)/review",
            method: .post,
            body: request
        )
    }
    
    // MARK: - Fetch Transaction Reviews
    
    func fetchTransactionReviews(transactionId: Int) async throws -> [Review] {
        let response: [Review] = try await apiClient.request(
            endpoint: "\(APIConfig.Transactions.details)/\(transactionId)/reviews",
            method: .get
        )
        return response
    }
}
