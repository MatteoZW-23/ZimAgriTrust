//
//  ProfileTabView.swift
//  ZimAgriTrust
//
//  Profile tab with user info, settings, and account actions
//

import SwiftUI

struct ProfileTabView: View {
    @StateObject private var authService = AuthService.shared
    @StateObject private var listingService = ListingService.shared
    @State private var showEditProfile = false
    @State private var showSettings = false
    @State private var showLogoutAlert = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Profile Header
                    if let user = authService.currentUser {
                        ProfileHeader(user: user)
                    }
                    
                    // Quick Stats
                    HStack(spacing: 16) {
                        QuickStatCard(icon: "list.bullet", title: "My Listings", count: listingService.myListings.count)
                        QuickStatCard(icon: "star.fill", title: "Trust Score", count: Int(authService.currentUser?.trust_score ?? 0))
                    }
                    .padding(.horizontal)
                    
                    // Menu Sections
                    VStack(spacing: 0) {
                        MenuSection(title: "Account") {
                            MenuRow(icon: "person.circle", title: "Edit Profile") {
                                showEditProfile = true
                            }
                            MenuRow(icon: "gear", title: "Settings") {
                                showSettings = true
                            }
                        }
                        
                        MenuSection(title: "Data & Privacy") {
                            MenuRow(icon: "square.and.arrow.down", title: "Export My Data") {
                                handleExportData()
                            }
                            MenuRow(icon: "eye.slash", title: "Deactivate Account") {
                                handleDeactivate()
                            }
                            MenuRow(icon: "trash", title: "Delete Account", isDestructive: true) {
                                handleDeleteAccount()
                            }
                        }
                        
                        MenuSection(title: "Support") {
                            MenuRow(icon: "questionmark.circle", title: "Help Center") {
                                // Navigate to help
                            }
                            MenuRow(icon: "info.circle", title: "About") {
                                // Show about
                            }
                        }
                    }
                    
                    // Logout Button
                    Button {
                        showLogoutAlert = true
                    } label: {
                        Text("Logout")
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.red.opacity(0.1))
                            .foregroundColor(.red)
                            .cornerRadius(10)
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical)
            }
            .navigationTitle("Profile")
            .sheet(isPresented: $showEditProfile) {
                EditProfileView()
            }
            .sheet(isPresented: $showSettings) {
                SettingsView()
            }
            .alert("Logout", isPresented: $showLogoutAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Logout", role: .destructive) {
                    authService.logout()
                }
            } message: {
                Text("Are you sure you want to logout?")
            }
            .onAppear {
                Task {
                    try? await listingService.fetchMyListings()
                }
            }
        }
    }
    
    private func handleExportData() {
        Task {
            do {
                let _: [String: Any] = try await APIClient.shared.request(
                    endpoint: APIConfig.Auth.dataExport,
                    method: .get
                )
                // Handle data export response
            } catch {
                print("Export failed: \(error)")
            }
        }
    }
    
    private func handleDeactivate() {
        Task {
            do {
                let _: [String: String] = try await APIClient.shared.request(
                    endpoint: APIConfig.Auth.deactivate,
                    method: .post
                )
                authService.logout()
            } catch {
                print("Deactivation failed: \(error)")
            }
        }
    }
    
    private func handleDeleteAccount() {
        Task {
            do {
                let _: [String: String] = try await APIClient.shared.request(
                    endpoint: "/users/data",
                    method: .delete
                )
                authService.logout()
            } catch {
                print("Delete failed: \(error)")
            }
        }
    }
}

struct ProfileHeader: View {
    let user: User
    
    var body: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(Color.green.opacity(0.1))
                    .frame(width: 80, height: 80)
                
                Text(user.full_name.prefix(1).uppercased())
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.green)
            }
            
            Text(user.full_name)
                .font(.title2)
                .fontWeight(.bold)
            
            Text(user.phone_number)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            if let trustScore = user.trust_score {
                HStack(spacing: 4) {
                    Image(systemName: "star.fill")
                        .foregroundColor(.yellow)
                    Text(String(format: "%.1f", trustScore))
                        .font(.subheadline)
                        .fontWeight(.semibold)
                }
            }
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(UIColor.systemGray6))
        .cornerRadius(12)
        .padding(.horizontal)
    }
}

struct QuickStatCard: View {
    let icon: String
    let title: String
    let count: Int
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 24))
                .foregroundColor(.green)
            
            Text("\(count)")
                .font(.title2)
                .fontWeight(.bold)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(UIColor.systemGray6))
        .cornerRadius(12)
    }
}

struct MenuSection<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.horizontal)
                .padding(.top, 16)
            
            VStack(spacing: 0) {
                content
            }
            .background(Color(UIColor.systemBackground))
            .cornerRadius(12)
        }
        .padding(.horizontal)
    }
}

struct MenuRow: View {
    let icon: String
    let title: String
    let isDestructive: Bool
    let action: () -> Void
    
    init(icon: String, title: String, isDestructive: Bool = false, action: @escaping () -> Void) {
        self.icon = icon
        self.title = title
        self.isDestructive = isDestructive
        self.action = action
    }
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .foregroundColor(isDestructive ? .red : .green)
                    .frame(width: 24)
                
                Text(title)
                    .foregroundColor(isDestructive ? .red : .primary)
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }
            .padding()
        }
    }
}

struct EditProfileView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var authService = AuthService.shared
    
    @State private var fullName = ""
    @State private var email = ""
    @State private var province = ""
    @State private var district = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section("Personal Information") {
                    TextField("Full Name", text: $fullName)
                    TextField("Email", text: $email)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                }
                
                Section("Location") {
                    TextField("Province", text: $province)
                    TextField("District", text: $district)
                }
                
                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Edit Profile")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        handleSave()
                    }
                    .disabled(isLoading)
                }
            }
            .onAppear {
                if let user = authService.currentUser {
                    fullName = user.full_name
                    email = user.email ?? ""
                    province = user.province ?? ""
                    district = user.district ?? ""
                }
            }
        }
    }
    
    private func handleSave() {
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let request = UpdateProfileRequest(
                    full_name: fullName.isEmpty ? nil : fullName,
                    email: email.isEmpty ? nil : email,
                    province: province.isEmpty ? nil : province,
                    district: district.isEmpty ? nil : district
                )
                _ = try await authService.updateProfile(request)
                
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

struct SettingsView: View {
    @StateObject private var notificationService = NotificationService.shared
    @State private var notificationsEnabled = true
    @State private var emailNotifications = true
    @State private var smsNotifications = false
    
    var body: some View {
        NavigationView {
            Form {
                Section("Notifications") {
                    Toggle("Push Notifications", isOn: $notificationsEnabled)
                        .onChange(of: notificationsEnabled) { _, newValue in
                            if newValue {
                                Task {
                                    let granted = await notificationService.requestAuthorization()
                                    if !granted {
                                        await MainActor.run {
                                            notificationsEnabled = false
                                        }
                                    }
                                }
                            } else {
                                notificationService.removeAllPendingNotifications()
                            }
                        }
                    
                    Toggle("Email Notifications", isOn: $emailNotifications)
                    Toggle("SMS Notifications", isOn: $smsNotifications)
                }
                
                Section("Privacy") {
                    Toggle("Profile Visible to Others", isOn: .constant(true))
                    Toggle("Show Phone Number", isOn: .constant(true))
                }
                
                Section("Language") {
                    Picker("Preferred Language", selection: .constant("en")) {
                        Text("English").tag("en")
                        Text("Shona").tag("sn")
                        Text("Ndebele").tag("nd")
                    }
                }
                
                Section {
                    HStack {
                        Text("App Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("Settings")
            .onAppear {
                notificationsEnabled = notificationService.isAuthorized
            }
        }
    }
}

#Preview {
    ProfileTabView()
}
