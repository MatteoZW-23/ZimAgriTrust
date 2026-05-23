import Foundation
import Combine
import CoreData
import UIKit

@MainActor
class ProfileViewModel: ObservableObject {
    @Published var user: User?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var isEditing = false
    @Published var notificationsEnabled = true
    @Published var biometricEnabled = false
    @Published var privacySettings = PrivacySettings(profile_visible: true, show_phone_number: false)
    
    private var cancellables = Set<AnyCancellable>()
    private let authService: AuthService
    private let coreDataStack: CoreDataStack
    private let biometricManager: BiometricManager
    
    init(authService: AuthService = .shared, coreDataStack: CoreDataStack = .shared, biometricManager: BiometricManager = .shared) {
        self.authService = authService
        self.coreDataStack = coreDataStack
        self.biometricManager = biometricManager
        loadProfile()
        checkBiometricAvailability()
    }
    
    func loadProfile() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let profile = try await authService.getProfile()
                await MainActor.run {
                    self.user = profile
                    self.isLoading = false
                    self.saveToCoreData(profile)
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                    self.loadFromCoreData()
                }
            }
        }
    }
    
    func updateProfile(name: String?, email: String?, phone: String?) {
        isLoading = true
        
        Task {
            do {
                let updated = try await authService.updateProfile(
                    name: name,
                    email: email,
                    phone: phone
                )
                await MainActor.run {
                    self.user = updated
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func uploadIDDocument(image: UIImage, documentType: String) {
        isLoading = true
        
        Task {
            do {
                guard let imageData = image.jpegData(compressionQuality: 0.8) else {
                    throw NSError(domain: "ImageError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Failed to process image"])
                }
                
                _ = try await authService.uploadIDDocument(
                    imageData: imageData,
                    documentType: documentType
                )
                await MainActor.run {
                    self.isLoading = false
                    self.loadProfile()
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func changePassword(currentPassword: String, newPassword: String) {
        isLoading = true
        
        Task {
            do {
                _ = try await authService.changePassword(
                    currentPassword: currentPassword,
                    newPassword: newPassword
                )
                await MainActor.run {
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func enableBiometrics() {
        biometricManager.authenticate(reason: "Enable biometric login") { result in
            Task { @MainActor in
                switch result {
                case .success:
                    self.biometricEnabled = true
                    UserDefaultsManager.shared.set(true, forKey: "biometricEnabled")
                case .failure(let error):
                    self.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func disableBiometrics() {
        biometricEnabled = false
        UserDefaultsManager.shared.set(false, forKey: "biometricEnabled")
        KeychainManager.shared.delete(key: "biometricPassword")
    }
    
    func requestAccountDeletion() {
        isLoading = true
        
        Task {
            do {
                _ = try await authService.deleteAccount()
                await MainActor.run {
                    self.isLoading = false
                    self.logout()
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func exportUserData() -> URL? {
        guard let user = user else { return nil }
        
        let data: [String: Any] = [
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email ?? "",
            "phone_number": user.phone_number,
            "trust_score": user.trust_score,
            "exported_at": ISO8601DateFormatter().string(from: Date())
        ]
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: data, options: .prettyPrinted)
            let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent("zimagritrust_data_export.json")
            try jsonData.write(to: tempURL)
            return tempURL
        } catch {
            errorMessage = "Failed to export data: \(error.localizedDescription)"
            return nil
        }
    }
    
    func logout() {
        authService.logout()
        UserDefaultsManager.shared.remove(forKey: "isLoggedIn")
        KeychainManager.shared.delete(key: "authToken")
        KeychainManager.shared.delete(key: "refreshToken")
    }
    
    private func checkBiometricAvailability() {
        biometricEnabled = UserDefaultsManager.shared.bool(forKey: "biometricEnabled")
    }
    
    private func saveToCoreData(_ user: User) {
        let context = coreDataStack.viewContext
        let entity = UserEntity(context: context)
        entity.id = Int64(user.id)
        entity.fullName = user.full_name
        entity.email = user.email
        entity.phoneNumber = user.phone_number
        entity.trustScore = user.trust_score
        coreDataStack.save()
    }
    
    private func loadFromCoreData() {
        let context = coreDataStack.viewContext
        let request: NSFetchRequest<UserEntity> = UserEntity.fetchRequest()
        
        do {
            let entities = try context.fetch(request)
            if let entity = entities.first {
                self.user = User(
                    id: Int(entity.id),
                    full_name: entity.fullName ?? "",
                    email: entity.email,
                    phone_number: entity.phoneNumber ?? "",
                    trust_score: entity.trustScore,
                    is_verified: false,
                    created_at: nil
                )
            }
        } catch {
            print("Core Data fetch error: \(error)")
        }
    }
}
