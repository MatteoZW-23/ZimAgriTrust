//
//  TwoFAView.swift
//  ZimAgriTrust
//
//  Two-factor authentication verification screen
//

import SwiftUI

struct TwoFAView: View {
    @StateObject private var authService = AuthService.shared
    @Environment(\.dismiss) private var dismiss
    
    let phoneNumber: String
    
    @State private var otp = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationView {
            ZStack {
                Color(UIColor.systemGroupedBackground)
                    .ignoresSafeArea()
                
                VStack(spacing: 32) {
                    // Icon and Title
                    VStack(spacing: 16) {
                        Image(systemName: "lock.shield.fill")
                            .font(.system(size: 50))
                            .foregroundColor(.green)
                        
                        Text("Two-Factor Authentication")
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        Text("Enter the OTP sent to your phone")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.top, 60)
                    
                    // OTP Input
                    VStack(spacing: 16) {
                        Text("OTP Code")
                            .font(.headline)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        
                        TextField("Enter 6-digit code", text: $otp)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.numberPad)
                            .textContentType(.oneTimeCode)
                            .onChange(of: otp) { _, newValue in
                                otp = String(newValue.prefix(6))
                            }
                        
                        if !errorMessage.isEmpty {
                            Text(errorMessage)
                                .foregroundColor(.red)
                                .font(.caption)
                        }
                        
                        Button(action: handleVerify) {
                            if isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            } else {
                                Text("Verify")
                                    .fontWeight(.semibold)
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                        .disabled(isLoading || otp.count != 6)
                    }
                    .padding(.horizontal, 32)
                    
                    // Resend Option
                    Button(action: handleResend) {
                        Text("Resend OTP")
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                    
                    Spacer()
                }
                .padding()
            }
            .navigationTitle("Verify OTP")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        authService.logout()
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func handleVerify() {
        guard otp.count == 6 else {
            errorMessage = "Please enter a valid 6-digit OTP"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                try await authService.verify2FA(otp: otp)
                isLoading = false
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }
    
    private func handleResend() {
        Task {
            do {
                try await authService.login(phoneNumber: phoneNumber, password: "")
                errorMessage = "OTP resent successfully"
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                }
            }
        }
    }
}

#Preview {
    TwoFAView(phoneNumber: "+263123456789")
}
