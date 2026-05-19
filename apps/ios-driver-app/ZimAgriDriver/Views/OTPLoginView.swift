//
//  OTPLoginView.swift
//  ZimAgriDriver
//
//  OTP-based authentication for drivers
//

import SwiftUI

struct OTPLoginView: View {
    @StateObject private var driverService = DriverService.shared
    
    @State private var phoneNumber = ""
    @State private var otp = ""
    @State private var isRequestingOTP = false
    @State private var isVerifyingOTP = false
    @State private var showRegister = false
    @State private var errorMessage = ""
    @State private var step: Int = 1 // 1: Request OTP, 2: Verify OTP
    
    var body: some View {
        NavigationView {
            ZStack {
                Color(UIColor.systemGroupedBackground)
                    .ignoresSafeArea()
                
                VStack(spacing: 32) {
                    // Logo and Title
                    VStack(spacing: 12) {
                        Image(systemName: "truck.fill")
                            .font(.system(size: 60))
                            .foregroundColor(.green)
                        
                        Text("ZimAgriDriver")
                            .font(.title)
                            .fontWeight(.bold)
                        
                        Text("Driver Portal")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.top, 60)
                    
                    // Form
                    VStack(spacing: 16) {
                        if step == 1 {
                            TextField("Phone Number", text: $phoneNumber)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .keyboardType(.phonePad)
                                .autocapitalization(.none)
                            
                            Button(action: handleRequestOTP) {
                                if isRequestingOTP {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                } else {
                                    Text("Send OTP")
                                        .fontWeight(.semibold)
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.green)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                            .disabled(isRequestingOTP)
                        } else {
                            VStack(spacing: 12) {
                                Text("Enter the OTP sent to your phone")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                                
                                TextField("OTP Code", text: $otp)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .keyboardType(.numberPad)
                                    .textContentType(.oneTimeCode)
                                    .onChange(of: otp) { _, newValue in
                                        otp = String(newValue.prefix(6))
                                    }
                                
                                Button(action: handleVerifyOTP) {
                                    if isVerifyingOTP {
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
                                .disabled(isVerifyingOTP || otp.count != 6)
                                
                                Button("Resend OTP") {
                                    step = 1
                                    otp = ""
                                }
                                .font(.caption)
                            }
                        }
                        
                        if !errorMessage.isEmpty {
                            Text(errorMessage)
                                .foregroundColor(.red)
                                .font(.caption)
                        }
                    }
                    .padding(.horizontal, 32)
                    
                    // Register Link
                    if step == 1 {
                        Button(action: {
                            showRegister = true
                        }) {
                            Text("New Driver? Register Here")
                                .font(.caption)
                                .foregroundColor(.green)
                        }
                    }
                    
                    Spacer()
                }
                .padding()
            }
            .navigationDestination(isPresented: $showRegister) {
                DriverRegistrationView()
            }
        }
    }
    
    private func handleRequestOTP() {
        guard !phoneNumber.isEmpty else {
            errorMessage = "Please enter your phone number"
            return
        }
        
        isRequestingOTP = true
        errorMessage = ""
        
        Task {
            do {
                try await driverService.requestOTP(phoneNumber: phoneNumber)
                await MainActor.run {
                    isRequestingOTP = false
                    step = 2
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isRequestingOTP = false
                }
            }
        }
    }
    
    private func handleVerifyOTP() {
        guard otp.count == 6 else {
            errorMessage = "Please enter a valid 6-digit OTP"
            return
        }
        
        isVerifyingOTP = true
        errorMessage = ""
        
        Task {
            do {
                try await driverService.verifyOTP(phoneNumber: phoneNumber, otp: otp)
                await MainActor.run {
                    isVerifyingOTP = false
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isVerifyingOTP = false
                }
            }
        }
    }
}

#Preview {
    OTPLoginView()
}
