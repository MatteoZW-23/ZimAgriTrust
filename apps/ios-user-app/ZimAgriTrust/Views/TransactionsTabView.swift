//
//  TransactionsTabView.swift
//  ZimAgriTrust
//
//  Transactions tab with history and details
//

import SwiftUI

struct TransactionsTabView: View {
    @StateObject private var transactionService = TransactionService.shared
    
    var body: some View {
        NavigationView {
            Group {
                if transactionService.transactions.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "arrow.left.arrow.right")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        
                        Text("No transactions yet")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Button("Refresh") {
                            Task {
                                try? await transactionService.fetchTransactions()
                            }
                        }
                        .buttonStyle(.bordered)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(transactionService.transactions) { transaction in
                            NavigationLink(destination: TransactionDetailView(transaction: transaction)) {
                                TransactionCard(transaction: transaction)
                            }
                        }
                    }
                    .listStyle(.plain)
                    .refreshable {
                        try? await transactionService.fetchTransactions()
                    }
                }
            }
            .navigationTitle("Transactions")
            .onAppear {
                Task {
                    try? await transactionService.fetchTransactions()
                }
            }
        }
    }
}

struct TransactionCard: View {
    let transaction: Transaction
    
    var body: some View {
        HStack(spacing: 12) {
            // Status Icon
            ZStack {
                Circle()
                    .fill(statusColor.opacity(0.2))
                    .frame(width: 40, height: 40)
                
                Image(systemName: statusIcon)
                    .foregroundColor(statusColor)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(transaction.listing_title ?? "Transaction #\(transaction.id)")
                    .font(.headline)
                    .lineLimit(1)
                
                Text(transaction.seller_name ?? "Unknown Seller")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                HStack {
                    Text(transaction.status.capitalized)
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(statusColor.opacity(0.2))
                        .foregroundColor(statusColor)
                        .cornerRadius(4)
                    
                    Spacer()
                    
                    Text(transaction.formattedAmount)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                }
            }
        }
        .padding(.vertical, 4)
    }
    
    private var statusColor: Color {
        switch transaction.status.lowercased() {
        case "completed":
            return .green
        case "pending", "in_progress":
            return .orange
        case "cancelled", "failed":
            return .red
        default:
            return .gray
        }
    }
    
    private var statusIcon: String {
        switch transaction.status.lowercased() {
        case "completed":
            return "checkmark.circle.fill"
        case "pending", "in_progress":
            return "clock.fill"
        case "cancelled", "failed":
            return "xmark.circle.fill"
        default:
            return "circle.fill"
        }
    }
}

struct TransactionDetailView: View {
    let transaction: Transaction
    @StateObject private var transactionService = TransactionService.shared
    @State private var deliveryCode = ""
    @State private var showDeliveryConfirmation = false
    @State private var showReviewSheet = false
    @State private var reviews: [Review] = []
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Status Card
                VStack(spacing: 12) {
                    Image(systemName: statusIcon)
                        .font(.system(size: 40))
                        .foregroundColor(statusColor)
                    
                    Text(transaction.status.capitalized)
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    if let deliveryCode = transaction.delivery_code {
                        VStack(spacing: 4) {
                            Text("Delivery Code")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            
                            Text(deliveryCode)
                                .font(.title3)
                                .fontWeight(.bold)
                        }
                    }
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(statusColor.opacity(0.1))
                .cornerRadius(12)
                
                // Details
                VStack(alignment: .leading, spacing: 16) {
                    Text("Transaction Details")
                        .font(.headline)
                    
                    DetailRow(label: "Listing", value: transaction.listing_title ?? "N/A")
                    DetailRow(label: "Total Amount", value: transaction.formattedAmount)
                    DetailRow(label: "Delivery Method", value: transaction.delivery_method?.capitalized ?? "N/A")
                    DetailRow(label: "Date", value: formatDate(transaction.created_at))
                }
                .padding()
                .background(Color(UIColor.systemGray6))
                .cornerRadius(12)
                
                // Actions
                if transaction.status.lowercased() == "in_progress" {
                    Button {
                        showDeliveryConfirmation = true
                    } label: {
                        Text("Confirm Delivery")
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.green)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                    }
                }
                
                if transaction.status.lowercased() == "completed" {
                    Button {
                        showReviewSheet = true
                    } label: {
                        Text("Leave Review")
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                    }
                }
                
                // Reviews
                if !reviews.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Reviews")
                            .font(.headline)
                        
                        VStack(spacing: 8) {
                            ForEach(reviews) { review in
                                ReviewRow(review: review)
                            }
                        }
                    }
                    .padding()
                    .background(Color(UIColor.systemGray6))
                    .cornerRadius(12)
                }
            }
            .padding()
        }
        .navigationTitle("Transaction Details")
        .sheet(isPresented: $showDeliveryConfirmation) {
            DeliveryConfirmationView(transactionId: transaction.id)
        }
        .sheet(isPresented: $showReviewSheet) {
            CreateReviewView(transactionId: transaction.id)
        }
        .onAppear {
            Task {
                reviews = (try? await transactionService.fetchTransactionReviews(id: transaction.id)) ?? []
            }
        }
    }
    
    private var statusColor: Color {
        switch transaction.status.lowercased() {
        case "completed":
            return .green
        case "pending", "in_progress":
            return .orange
        case "cancelled", "failed":
            return .red
        default:
            return .gray
        }
    }
    
    private var statusIcon: String {
        switch transaction.status.lowercased() {
        case "completed":
            return "checkmark.circle.fill"
        case "pending", "in_progress":
            return "clock.fill"
        case "cancelled", "failed":
            return "xmark.circle.fill"
        default:
            return "circle.fill"
        }
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "ISO8601"
        
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }
        
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct DetailRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .fontWeight(.medium)
        }
    }
}

struct DeliveryConfirmationView: View {
    @Environment(\.dismiss) private var dismiss
    let transactionId: Int
    @StateObject private var transactionService = TransactionService.shared
    
    @State private var deliveryCode = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section {
                    TextField("Enter Delivery Code", text: $deliveryCode)
                        .keyboardType(.default)
                } header: {
                    Text("Delivery Confirmation")
                } footer: {
                    Text("Enter the delivery code provided by the driver to confirm receipt.")
                }
                
                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Confirm Delivery")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Confirm") {
                        handleConfirm()
                    }
                    .disabled(isLoading || deliveryCode.isEmpty)
                }
            }
        }
    }
    
    private func handleConfirm() {
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                try await transactionService.confirmDelivery(
                    transactionId: transactionId,
                    deliveryCode: deliveryCode
                )
                
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

struct CreateReviewView: View {
    @Environment(\.dismiss) private var dismiss
    let transactionId: Int
    @StateObject private var transactionService = TransactionService.shared
    
    @State private var rating = 5
    @State private var comment = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section("Rating") {
                    HStack {
                        ForEach(1...5, id: \.self) { star in
                            Button {
                                rating = star
                            } label: {
                                Image(systemName: star <= rating ? "star.fill" : "star")
                                    .foregroundColor(star <= rating ? .yellow : .gray)
                            }
                        }
                    }
                    .font(.title2)
                }
                
                Section("Comment (Optional)") {
                    TextEditor(text: $comment)
                        .frame(minHeight: 100)
                }
                
                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Leave Review")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Submit") {
                        handleSubmit()
                    }
                    .disabled(isLoading)
                }
            }
        }
    }
    
    private func handleSubmit() {
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let request = CreateReviewRequest(
                    rating: rating,
                    comment: comment.isEmpty ? nil : comment
                )
                try await transactionService.createReview(
                    transactionId: transactionId,
                    request
                )
                
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

struct ReviewRow: View {
    let review: Review
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(review.reviewer_name ?? "Anonymous")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                HStack(spacing: 2) {
                    ForEach(1...5, id: \.self) { star in
                        Image(systemName: star <= review.rating ? "star.fill" : "star")
                            .font(.caption)
                            .foregroundColor(star <= review.rating ? .yellow : .gray)
                    }
                }
            }
            
            if let comment = review.comment {
                Text(comment)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Text(formatDate(review.created_at))
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(UIColor.systemGray5))
        .cornerRadius(8)
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "ISO8601"
        
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }
        
        formatter.dateStyle = .short
        return formatter.string(from: date)
    }
}

#Preview {
    TransactionsTabView()
}
