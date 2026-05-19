//
//  DriverRegistrationView.swift
//  ZimAgriDriver
//
//  Self-registration for new drivers
//

import SwiftUI

struct DriverRegistrationView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var driverService = DriverService.shared
    
    @State private var phoneNumber = ""
    @State private var fullName = ""
    @State private var idNumber = ""
    @State private var vehicleType = ""
    @State private var licensePlate = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var showSuccess = false
    
    private let vehicleTypes = ["Motorcycle", "Car", "Van", "Truck"]
    
    var body: some View {
        NavigationView {
            Form {
                Section("Personal Information") {
                    TextField("Full Name", text: $fullName)
                        .autocapitalization(.words)
                    
                    TextField("Phone Number", text: $phoneNumber)
                        .keyboardType(.phonePad)
                        .autocapitalization(.none)
                    
                    TextField("ID Number", text: $idNumber)
                        .autocapitalization(.none)
                }
                
                Section("Vehicle Information") {
                    Picker("Vehicle Type", selection: $vehicleType) {
                        Text("Select Vehicle").tag("")
                        ForEach(vehicleTypes, id: \.self) { type in
                            Text(type).tag(type)
                        }
                    }
                    
                    TextField("License Plate", text: $licensePlate)
                        .autocapitalization(.allCharacters)
                }
                
                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Register as Driver")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Submit") {
                        handleRegister()
                    }
                    .disabled(isLoading)
                }
            }
            .alert("Registration Successful", isPresented: $showSuccess) {
                Button("OK") {
                    dismiss()
                }
            } message: {
                Text("Your registration has been submitted. You will be contacted once approved.")
            }
        }
    }
    
    private func handleRegister() {
        guard !fullName.isEmpty, !phoneNumber.isEmpty, !idNumber.isEmpty else {
            errorMessage = "Please fill in all required fields"
            return
        }
        
        guard !vehicleType.isEmpty, !licensePlate.isEmpty else {
            errorMessage = "Please enter vehicle information"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let request = SelfRegisterRequest(
                    phone_number: phoneNumber,
                    full_name: fullName,
                    id_number: idNumber,
                    vehicle_type: vehicleType.lowercased(),
                    license_plate: licensePlate.uppercased()
                )
                try await driverService.selfRegister(request)
                
                await MainActor.run {
                    isLoading = false
                    showSuccess = true
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
    DriverRegistrationView()
}
