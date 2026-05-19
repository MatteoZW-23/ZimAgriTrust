//
//  WalletService.swift
//  ZimAgriTrust
//
//  Service for wallet-related operations
//

import Foundation

class WalletService: ObservableObject {
    static let shared = WalletService()
    
    private let apiClient = APIClient.shared
    
    @Published var balance: WalletBalance?
    @Published var transactions: [WalletTransaction] = []
    
    private init() {}
    
    // MARK: - Fetch Balance
    
    func fetchBalance() async throws {
        let response: WalletBalance = try await apiClient.request(
            endpoint: APIConfig.Wallet.balance,
            method: .get
        )
        
        await MainActor.run {
            self.balance = response
        }
    }
    
    // MARK: - Fetch Transactions
    
    func fetchTransactions() async throws {
        let response: [WalletTransaction] = try await apiClient.request(
            endpoint: APIConfig.Wallet.transactions,
            method: .get
        )
        
        await MainActor.run {
            self.transactions = response
        }
    }
    
    // MARK: - Deposit
    
    func deposit(_ request: DepositRequest) async throws {
        let _: [String: String] = try await apiClient.request(
            endpoint: APIConfig.Wallet.deposit,
            method: .post,
            body: request
        )
        
        await fetchBalance()
    }
    
    // MARK: - Withdraw
    
    func withdraw(_ request: WithdrawRequest) async throws {
        let _: [String: String] = try await apiClient.request(
            endpoint: APIConfig.Wallet.withdraw,
            method: .post,
            body: request
        )
        
        await fetchBalance()
    }
    
    // MARK: - Fee Preview
    
    func getFeePreview(amount: Double, currency: String = "USD") async throws -> FeePreview {
        let response: FeePreview = try await apiClient.request(
            endpoint: "/payments/fee-preview?amount=\(amount)&currency=\(currency)",
            method: .get
        )
        return response
    }
}
