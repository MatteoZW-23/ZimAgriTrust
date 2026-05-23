//
//  SignInWithAppleManager.swift
//  ZimAgriTrust
//
//  Sign in with Apple authentication
//

import Foundation
import AuthenticationServices
import Combine

@MainActor
class SignInWithAppleManager: NSObject, ObservableObject {
    static let shared = SignInWithAppleManager()
    
    @Published var isAvailable = false
    @Published var isLoading = false
    
    private var continuation: CheckedContinuation<ASAuthorization, Error>?
    
    private override init() {
        super.init()
        checkAvailability()
    }
    
    private func checkAvailability() {
        isAvailable = ASAuthorizationAppleIDProvider().isAvailable
    }
    
    func performSignIn() async throws -> ASAuthorization {
        guard isAvailable else {
            throw NSError(domain: "SignInWithApple", code: -1, userInfo: [NSLocalizedDescriptionKey: "Sign in with Apple is not available"])
        }
        
        isLoading = true
        
        let request = ASAuthorizationAppleIDProvider().createRequest()
        request.requestedScopes = [.fullName, .email]
        
        let authorizationController = ASAuthorizationController(authorizationRequests: [request])
        
        return try await withCheckedThrowingContinuation { continuation in
            self.continuation = continuation
            authorizationController.delegate = self
            authorizationController.presentationContextProvider = self
            authorizationController.performRequests()
        }
    }
    
    func getCredentialState(for userID: String) async -> ASAuthorizationAppleIDProvider.CredentialState {
        return await ASAuthorizationAppleIDProvider().credentialState(forUserID: userID)
    }
}

extension SignInWithAppleManager: ASAuthorizationControllerDelegate {
    func authorizationController(controller: ASAuthorizationController, didCompleteWithAuthorization authorization: ASAuthorization) {
        if let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential {
            let userIdentifier = appleIDCredential.user
            let fullName = appleIDCredential.fullName
            let email = appleIDCredential.email
            let identityToken = appleIDCredential.identityToken
            let authorizationCode = appleIDCredential.authorizationCode
            
            // Store user identifier for future credential state checks
            UserDefaultsManager.shared.set(userIdentifier, forKey: "appleUserID")
            
            continuation?.resume(returning: authorization)
            continuation = nil
        }
    }
    
    func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        continuation?.resume(throwing: error)
        continuation = nil
    }
}

extension SignInWithAppleManager: ASAuthorizationControllerPresentationContextProviding {
    func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
        guard let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let window = windowScene.windows.first else {
            return ASPresentationAnchor()
        }
        return window
    }
}
