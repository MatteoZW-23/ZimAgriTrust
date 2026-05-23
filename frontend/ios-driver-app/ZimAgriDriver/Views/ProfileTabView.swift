//
//  ProfileTabView.swift
//  ZimAgriDriver
//
//  Driver profile and settings
//

import SwiftUI

struct ProfileTabView: View {
    @StateObject private var driverService = DriverService.shared
    @State private var showLogoutAlert = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Profile Header
                    if let driver = driverService.currentDriver {
                        ProfileHeader(driver: driver)
                    }
                    
                    // Quick Stats
                    HStack(spacing: 16) {
                        QuickStatCard(icon: "truck.box", title: "Deliveries", count: driverService.deliveries.count)
                        QuickStatCard(icon: "checkmark.circle.fill", title: "Completed", count: driverService.deliveries.filter { $0.status.lowercased() == "delivered" }.count)
                    }
                    .padding(.horizontal)
                    
                    // Menu Sections
                    VStack(spacing: 0) {
                        MenuSection(title: "Account") {
                            MenuRow(icon: "person.circle", title: "Edit Profile") {
                                // Navigate to edit profile
                            }
                            MenuRow(icon: "gear", title: "Settings") {
                                // Navigate to settings
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
            .alert("Logout", isPresented: $showLogoutAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Logout", role: .destructive) {
                    driverService.logout()
                }
            } message: {
                Text("Are you sure you want to logout?")
            }
        }
    }
}

struct ProfileHeader: View {
    let driver: DriverInfo
    
    var body: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(Color.green.opacity(0.1))
                    .frame(width: 80, height: 80)
                
                Text(driver.name.prefix(1).uppercased())
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.green)
            }
            
            Text(driver.name)
                .font(.title2)
                .fontWeight(.bold)
            
            Text(driver.phoneNumber)
                .font(.subheadline)
                .foregroundColor(.secondary)
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
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .foregroundColor(.green)
                    .frame(width: 24)
                
                Text(title)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }
            .padding()
        }
    }
}

#Preview {
    ProfileTabView()
}
