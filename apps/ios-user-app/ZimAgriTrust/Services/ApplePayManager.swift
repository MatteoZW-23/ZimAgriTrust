import Foundation
import PassKit
import UIKit

@MainActor
class ApplePayManager: NSObject, ObservableObject {
    @Published var isApplePayAvailable = false
    @Published var paymentStatus: PaymentStatus = .idle
    @Published var errorMessage: String?
    
    private var paymentController: PKPaymentAuthorizationController?
    private var paymentCompletionHandler: ((Bool) -> Void)?
    
    enum PaymentStatus {
        case idle
        case processing
        case success
        case failed
    }
    
    override init() {
        super.init()
        checkApplePayAvailability()
    }
    
    func checkApplePayAvailability() {
        isApplePayAvailable = PKPaymentAuthorizationController.canMakePayments()
    }
    
    func canMakePayments(usingNetworks: [PKPaymentNetwork] = [.visa, .masterCard]) -> Bool {
        PKPaymentAuthorizationController.canMakePayments(usingNetworks: usingNetworks)
    }
    
    func startPayment(amount: Double, currency: String = "USD", orderId: Int, description: String) {
        guard isApplePayAvailable else {
            errorMessage = "Apple Pay is not available on this device"
            return
        }
        
        let paymentRequest = PKPaymentRequest()
        paymentRequest.merchantIdentifier = "merchant.com.zimagritrust"
        paymentRequest.supportedNetworks = [.visa, .masterCard]
        paymentRequest.supportedCountries = ["ZW"]
        paymentRequest.merchantCapabilities = .capability3DS
        paymentRequest.countryCode = "ZW"
        paymentRequest.currencyCode = currency
        
        let paymentAmount = NSDecimalNumber(value: amount)
        paymentRequest.paymentSummaryItems = [
            PKPaymentSummaryItem(label: description, amount: paymentAmount)
        ]
        
        paymentController = PKPaymentAuthorizationController(paymentRequest)
        paymentController?.delegate = self
        paymentController?.present(completion: { [weak self] presented in
            if !presented {
                self?.paymentStatus = .failed
                self?.errorMessage = "Failed to present Apple Pay sheet"
            }
        })
        
        paymentStatus = .processing
    }
    
    func startTopUpPayment(amount: Double) {
        startPayment(amount: amount, orderId: 0, description: "Wallet Top-up")
    }
    
    func startListingPayment(amount: Double, orderId: Int, cropName: String) {
        startPayment(amount: amount, orderId: orderId, description: "Payment for \(cropName)")
    }
}

extension ApplePayManager: PKPaymentAuthorizationControllerDelegate {
    func paymentAuthorizationController(_ controller: PKPaymentAuthorizationController, didAuthorizePayment payment: PKPayment, handler completion: @escaping (PKPaymentAuthorizationResult) -> Void) {
        paymentCompletionHandler = { success in
            completion(PKPaymentAuthorizationResult(status: success ? .success : .failure, errors: nil))
        }
        
        // Process payment with backend
        Task {
            do {
                let token = payment.token
                let paymentData = String(data: token.paymentData, encoding: .utf8) ?? ""
                
                // Call backend to process payment
                // let success = try await processPaymentWithBackend(token: paymentData, orderId: orderId)
                
                // For now, simulate success
                await MainActor.run {
                    self.paymentStatus = .success
                    self.paymentCompletionHandler?(true)
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.paymentStatus = .failed
                    self.paymentCompletionHandler?(false)
                }
            }
        }
    }
    
    func paymentAuthorizationControllerDidFinish(_ controller: PKPaymentAuthorizationController) {
        controller.dismiss()
        
        if paymentStatus == .idle {
            paymentStatus = .failed
        }
    }
}

// Backend payment processing would go here
/*
extension ApplePayManager {
    private func processPaymentWithBackend(token: String, orderId: Int) async throws -> Bool {
        let endpoint = Endpoints.payments.applePay
        let body: [String: Any] = [
            "order_id": orderId,
            "payment_token": token,
            "amount": amount
        ]
        
        let response: PaymentResponse = try await APIClient.shared.post(endpoint, body: body)
        return response.success
    }
}
*/
