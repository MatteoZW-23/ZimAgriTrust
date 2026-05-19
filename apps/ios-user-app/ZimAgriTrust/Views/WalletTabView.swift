//
//  WalletTabView.swift
//  ZimAgriTrust
//
//  Wallet tab with balance, deposit, withdraw, and transactions
//

import SwiftUI

struct WalletTabView: View {
    @StateObject private var walletService = WalletService.shared
    @State private var showDeposit = false
    @State private var showWithdraw = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Balance Card
                    if let balance = walletService.balance {
                        BalanceCard(balance: balance)
                    }
                    
                    // Action Buttons
                    HStack(spacing: 16) {
                        WalletActionButton(icon: "plus.circle.fill", title: "Deposit", color: .green) {
                            showDeposit = true
                        }
                        
                        WalletActionButton(icon: "minus.circle.fill", title: "Withdraw", color: .red) {
                            showWithdraw = true
                        }
                    }
                    .padding(.horizontal)
                    
                    // Recent Transactions
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("Recent Transactions")
                                .font(.headline)
                            Spacer()
                            NavigationLink(destination: AllTransactionsView()) {
                                Text("See All")
                                    .font(.caption)
                                    .foregroundColor(.green)
                            }
                        }
                        .padding(.horizontal)
                        
                        if walletService.transactions.isEmpty {
                            Text("No transactions yet")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                                .frame(maxWidth: .infinity, alignment: .center)
                                .padding()
                        } else {
                            VStack(spacing: 8) {
                                ForEach(walletService.transactions.prefix(5)) { transaction in
                                    TransactionRow(transaction: transaction)
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                }
                .padding(.vertical)
            }
            .navigationTitle("Wallet")
            .refreshable {
                await refreshWalletData()
            }
            .onAppear {
                Task {
                    await refreshWalletData()
                }
            }
            .sheet(isPresented: $showDeposit) {
                DepositView()
            }
            .sheet(isPresented: $showWithdraw) {
                WithdrawView()
            }
        }
    }
    
    private func refreshWalletData() async {
        async let balance = walletService.fetchBalance()
        async let transactions = walletService.fetchTransactions()
        
        try? await balance
        try? await transactions
    }
}

struct BalanceCard: View {
    let balance: WalletBalance
    
    var body: some View {
        VStack(spacing: 16) {
            Text("Available Balance")
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            Text(balance.formattedAvailable)
                .font(.system(size: 48, weight: .bold))
                .foregroundColor(.green)
            
            HStack(spacing: 24) {
                VStack(spacing: 4) {
                    Text("Pending")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(String(format: "$%.2f", balance.pending_usd))
                        .font(.subheadline)
                        .fontWeight(.semibold)
                }
                
                VStack(spacing: 4) {
                    Text("Total")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(balance.formattedBalance)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                }
            }
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(
            LinearGradient(
                colors: [Color.green.opacity(0.1), Color.green.opacity(0.05)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(16)
        .padding(.horizontal)
    }
}

struct WalletActionButton: View {
    let icon: String
    let title: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 32))
                    .foregroundColor(color)
                
                Text(title)
                    .font(.caption)
                    .foregroundColor(.primary)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(UIColor.systemGray6))
            .cornerRadius(12)
        }
    }
}

struct TransactionRow: View {
    let transaction: WalletTransaction
    
    var body: some View {
        HStack {
            Image(systemName: transaction.type == "credit" ? "arrow.down.left" : "arrow.up.right")
                .foregroundColor(transaction.type == "credit" ? .green : .red)
                .frame(width: 32)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(transaction.description ?? transaction.type.capitalized)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(formatDate(transaction.created_at))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Text(transaction.formattedAmount)
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(transaction.type == "credit" ? .green : .red)
        }
        .padding()
        .background(Color(UIColor.systemGray6))
        .cornerRadius(8)
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "ISO8601"
        
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }
        
        formatter.dateStyle = .short
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct AllTransactionsView: View {
    @StateObject private var walletService = WalletService.shared
    
    var body: some View {
        List {
            ForEach(walletService.transactions) { transaction in
                TransactionRow(transaction: transaction)
            }
        }
        .navigationTitle("All Transactions")
        .onAppear {
            Task {
                try? await walletService.fetchTransactions()
            }
        }
    }
}

struct DepositView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var walletService = WalletService.shared
    
    @State private var amount = ""
    @State private var paymentMethod = "ecocash"
    @State private var reference = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section("Amount") {
                    TextField("Amount (USD)", text: $amount)
                        .keyboardType(.decimalPad)
                }
                
                Section("Payment Method") {
                    Picker("Method", selection: $paymentMethod) {
                        Text("EcoCash").tag("ecocash")
                        Text("Bank Transfer").tag("bank")
                        Text("Mobile Money").tag("mobile")
                    }
                    .pickerStyle(.segmented)
                }
                
                Section("Reference (Optional)") {
                    TextField("Transaction Reference", text: $reference)
                }
                
                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Deposit")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Deposit") {
                        handleDeposit()
                    }
                    .disabled(isLoading)
                }
            }
        }
    }
    
    private func handleDeposit() {
        guard let amountValue = Double(amount), amountValue > 0 else {
            errorMessage = "Please enter a valid amount"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let request = DepositRequest(
                    amount: amountValue,
                    payment_method: paymentMethod,
                    reference: reference.isEmpty ? nil : reference
                )
                try await walletService.deposit(request)
                
                await MainActor.run {
                    isLoading = false
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }
}

struct WithdrawView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var walletService = WalletService.shared
    
    @State private var amount = ""
    @State private var bankAccount = ""
    @State private var bankName = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section("Amount") {
                    TextField("Amount (USD)", text: $amount)
                        .keyboardType(.decimalPad)
                }
                
                Section("Bank Details") {
                    TextField("Bank Account Number", text: $bankAccount)
                    TextField("Bank Name", text: $bankName)
                }
                
                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Withdraw")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Withdraw") {
                        handleWithdraw()
                    }
                    .disabled(isLoading)
                }
            }
        }
    }
    
    private func handleWithdraw() {
        guard let amountValue = Double(amount), amountValue > 0 else {
            errorMessage = "Please enter a valid amount"
            return
        }
        
        guard !bankAccount.isEmpty, !bankName.isEmpty else {
            errorMessage = "Please enter bank details"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let request = WithdrawRequest(
                    amount: amountValue,
                    bank_account: bankAccount,
                    bank_name: bankName
                )
                try await walletService.withdraw(request)
                
                await MainActor.run {
                    isLoading = false
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }
}

#Preview {
    WalletTabView()
}
