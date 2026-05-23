//
//  WalletViewModel.swift
//  ZimAgriTrust
//
//  Wallet view model with Combine
//

import Foundation
import Combine

@MainActor
class WalletViewModel: ObservableObject {
    @Published var balance: WalletBalance?
    @Published var transactions: [WalletTransaction] = []
    @Published var isLoading = false
    @Published var errorMessage = ""
    
    private let apiClient = APIClient.shared
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        Task {
            await fetchBalance()
            await fetchTransactions()
        }
    }
    
    // MARK: - Fetch Balance
    
    func fetchBalance() async {
        do {
            let response: WalletBalance = try await apiClient.request(
                endpoint: Endpoints.wallet,
                method: .get
            )
            balance = response
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    // MARK: - Fetch Transactions
    
    func fetchTransactions() async {
        do {
            let response: [WalletTransaction] = try await apiClient.request(
                endpoint: Endpoints.transactions,
                method: .get
            )
            transactions = response
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    // MARK: - Deposit
    
    func deposit(amount: Double, paymentMethod: String, reference: String? = nil) async {
        isLoading = true
        errorMessage = ""
        
        do {
            let request = DepositRequest(
                amount: amount,
                payment_method: paymentMethod,
                reference: reference
            )
            let _: [String: String] = try await apiClient.request(
                endpoint: Endpoints.deposit,
                method: .post,
                body: request
            )
            await fetchBalance()
            HapticHelper.notification(.success)
            isLoading = false
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }
    
    // MARK: - Withdraw
    
    func withdraw(amount: Double, bankAccount: String, bankName: String) async {
        isLoading = true
        errorMessage = ""
        
        do {
            let request = WithdrawRequest(
                amount: amount,
                bank_account: bankAccount,
                bank_name: bankName
            )
            let _: [String: String] = try await apiClient.request(
                endpoint: Endpoints.withdraw,
                method: .post,
                body: request
            )
            await fetchBalance()
            HapticHelper.notification(.success)
            isLoading = false
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }
}
