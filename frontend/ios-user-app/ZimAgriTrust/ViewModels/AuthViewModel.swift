//
//  AuthViewModel.swift
//  ZimAgriTrust
//
//  Authentication view model with Combine
//

import Foundation
import Combine

@MainActor
class AuthViewModel: ObservableObject {
    @Published var phoneNumber = ""
    @Published var password = ""
    @Published var otp = ""
    @Published var fullName = ""
    @Published var email = ""
    @Published var isLoading = false
    @Published var errorMessage = ""
    @Published var isAuthenticated = false
    @Published var requires2FA = false
    
    private let authManager = AuthManager.shared
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        setupBindings()
    }
    
    private func setupBindings() {
        authManager.$isAuthenticated
            .assign(to: &$isAuthenticated)
        
        authManager.$requires2FA
            .assign(to: &$requires2FA)
    }
    
    // MARK: - Login
    
    func login() {
        guard !phoneNumber.isEmpty, !password.isEmpty else {
            errorMessage = "Please enter phone number and password"
            return
        }
        
        guard ValidationHelper.validatePhoneNumber(phoneNumber) else {
            errorMessage = "Please enter a valid phone number"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        authManager.login(phoneNumber: phoneNumber, password: password)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.errorMessage = error.localizedDescription
                    }
                },
                receiveValue: { _ in }
            )
            .store(in: &cancellables)
    }
    
    // MARK: - 2FA Verification
    
    func verify2FA() {
        guard otp.count == 6 else {
            errorMessage = "Please enter a valid 6-digit OTP"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        authManager.verify2FA(otp: otp)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.errorMessage = error.localizedDescription
                    }
                },
                receiveValue: { _ in }
            )
            .store(in: &cancellables)
    }
    
    // MARK: - Registration
    
    func register() {
        guard !phoneNumber.isEmpty, !password.isEmpty, !fullName.isEmpty else {
            errorMessage = "Please fill in all required fields"
            return
        }
        
        guard ValidationHelper.validatePhoneNumber(phoneNumber) else {
            errorMessage = "Please enter a valid phone number"
            return
        }
        
        guard ValidationHelper.validatePassword(password) else {
            errorMessage = "Password must be at least 8 characters"
            return
        }
        
        if !email.isEmpty, !ValidationHelper.validateEmail(email) {
            errorMessage = "Please enter a valid email address"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        authManager.register(
            phoneNumber: phoneNumber,
            password: password,
            fullName: fullName,
            email: email.isEmpty ? nil : email
        )
        .receive(on: DispatchQueue.main)
        .sink(
            receiveCompletion: { [weak self] completion in
                self?.isLoading = false
                if case .failure(let error) = completion {
                    self?.errorMessage = error.localizedDescription
                }
            },
            receiveValue: { [weak self] _ in
                // Registration successful
                self?.phoneNumber = ""
                self?.password = ""
                self?.fullName = ""
                self?.email = ""
            }
        )
        .store(in: &cancellables)
    }
    
    // MARK: - Logout
    
    func logout() {
        authManager.logout()
        phoneNumber = ""
        password = ""
        otp = ""
        fullName = ""
        email = ""
    }
    
    // MARK: - Biometric Login
    
    func biometricLogin() {
        guard BiometricManager.shared.isAvailable else {
            errorMessage = "Biometric authentication not available"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let success = try await BiometricManager.shared.authenticate(reason: "Login to ZimAgriTrust")
                
                await MainActor.run {
                    self.isLoading = false
                    if success {
                        // Retrieve saved credentials and login
                        if let savedPhone = UserDefaultsManager.shared.string(forKey: "savedPhone"),
                           let savedPassword = KeychainManager.shared.getBiometricProtected(key: "savedPassword") {
                            self.phoneNumber = savedPhone
                            self.password = savedPassword
                            self.login()
                        }
                    }
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                    self.errorMessage = "Biometric authentication failed"
                }
            }
        }
    }
    
    // MARK: - Save Credentials for Biometric
    
    func saveCredentialsForBiometric() {
        UserDefaultsManager.shared.set(phoneNumber, forKey: "savedPhone")
        KeychainManager.shared.saveBiometricProtected(password, key: "savedPassword")
    }
}
