# ZimAgriTrust iOS User App

Production-ready native iOS app built with SwiftUI and MVVM + Combine architecture for the ZimAgriTrust agricultural marketplace.

## Prerequisites

- Xcode 15.0 or later
- iOS 15.0+ deployment target (iPadOS 15.0+ supported)
- Swift 5.9+
- Apple Developer Account (for App Store distribution, APNs, etc.)

## Architecture

### MVVM + Combine Pattern

The app follows the Model-View-ViewModel (MVVM) architecture with Combine for reactive state management:

- **Models**: Data structures and business logic
- **Views**: SwiftUI views that observe ViewModels
- **ViewModels**: Combine publishers that handle business logic and state
- **Services**: API clients, managers, and business logic
- **Core**: Shared infrastructure (API client, storage, etc.)

### Project Structure

```
ZimAgriTrust/
├── Models/                    # Data models
│   ├── AuthModels.swift
│   ├── UserModels.swift
│   ├── ListingModels.swift
│   ├── WalletModels.swift
│   ├── TransactionModels.swift
│   └── MarketModels.swift
├── Views/                     # SwiftUI views
│   ├── ContentView.swift
│   ├── LoginView.swift
│   ├── RegisterView.swift
│   ├── TwoFAView.swift
│   ├── ForgotPasswordView.swift
│   ├── ListingsTabView.swift
│   ├── MarketTabView.swift
│   ├── WalletTabView.swift
│   ├── TransactionsTabView.swift
│   ├── ProfileTabView.swift
│   ├── ListingDetailView.swift
│   ├── CreateListingView.swift
│   ├── DocumentScannerView.swift
│   ├── SignatureView.swift
│   ├── MapView.swift
│   └── AnalyticsView.swift
├── ViewModels/                # MVVM ViewModels with Combine
│   ├── AuthViewModel.swift
│   ├── MarketplaceViewModel.swift
│   ├── WalletViewModel.swift
│   ├── TransactionsViewModel.swift
│   ├── ProfileViewModel.swift
│   └── ListingsViewModel.swift
├── Services/                  # Business logic and API clients
│   ├── APIConfig.swift
│   ├── APIClient.swift
│   ├── KeychainManager.swift
│   ├── UserDefaultsManager.swift
│   ├── AuthManager.swift
│   ├── BiometricManager.swift
│   ├── AuthService.swift
│   ├── ListingService.swift
│   ├── WalletService.swift
│   ├── TransactionService.swift
│   ├── MarketService.swift
│   ├── NotificationService.swift
│   ├── DocumentScanner.swift
│   ├── SignatureManager.swift
│   ├── LocationManager.swift
│   ├── MapManager.swift
│   ├── ApplePayManager.swift
│   ├── StoreKitManager.swift
│   ├── CloudKitManager.swift
│   └── SignInWithAppleManager.swift
├── Core/                      # Core infrastructure
│   ├── CoreDataStack.swift
│   ├── Endpoints.swift
│   ├── Constants.swift
│   ├── Extensions.swift
│   └── Helpers.swift
├── MarketSnapshotWidget/      # WidgetKit Extension
│   └── MarketSnapshotWidget.swift
├── OrderStatusWidget/         # WidgetKit Extension
│   └── OrderStatusWidget.swift
├── LiveActivities/            # ActivityKit Extension
│   └── DeliveryLiveActivity.swift
├── AppClip/                   # App Clip Target
│   └── AppClipViewController.swift
├── SiriIntents/               # Siri Shortcuts
│   └── SearchListingsIntent.swift
├── AppleWatch/                # Watch App
│   └── WatchApp.swift
├── Resources/                 # Assets, images, etc.
├── ZimAgriTrust.entitlements  # App entitlements
└── Info.plist                 # App configuration
```

## Setup Instructions

### 1. Create New Xcode Project

1. Open Xcode
2. File → New → Project
3. Select "App" under iOS
4. Product Name: `ZimAgriTrust`
5. Interface: SwiftUI
6. Language: Swift
7. Save to: `c:\Users\MJ\Desktop\Agric\apps\ios-user-app\`

### 2. Import Source Files

After creating the Xcode project:

1. Delete the default `ContentView.swift` (we have our own)
2. Copy all files from the `ZimAgriTrust/` folder into your Xcode project:
   - Select all files in Finder
   - Drag into Xcode project navigator
   - Check "Copy items if needed"
   - Ensure "Create groups" is selected
   - Add to target: ZimAgriTrust

### 3. Configure Info.plist

Add the following to your `Info.plist`:

```xml
<key>NSPhotoLibraryUsageDescription</key>
<string>We need access to your photo library to upload listing images.</string>
<key>NSCameraUsageDescription</key>
<string>We need camera access to take photos for listings.</string>
<key>NSFaceIDUsageDescription</key>
<string>Use Face ID for secure authentication.</string>
```

### 4. Configure API Base URL

Edit `Services/APIConfig.swift` to set your production backend URL:

```swift
#if DEBUG
static let baseURL = "http://localhost:8080/api/v1"
#else
static let baseURL = "https://api.zimagritrust.com/api/v1"  // Change this
#endif
```

### 5. Build and Run

1. Select a simulator or connected device
2. Press Cmd+R to build and run
3. The app will start on the Login screen

## Features Implemented

### Authentication
- Login with phone number and password
- Two-factor authentication (OTP)
- Registration
- Password reset (forgot password)
- Token refresh
- Secure token storage using Keychain
- **Sign in with Apple** (ASAuthorizationAppleIDProvider)
- **Face ID / Touch ID** biometric authentication

### Listings
- Browse all listings with search and filters
- View listing details
- Create new listings with image upload
- Save/favorite listings
- **Map-based listing view** with MapKit
- **Location-based search** using Core Location

### Market
- View current market prices
- Trending crops
- Market news
- Market summary statistics
- **Analytics dashboard** with SwiftUI Charts

### Wallet
- View balance (available, pending, total)
- Deposit funds
- Withdraw funds
- Transaction history
- **Apple Pay integration** for payments

### Transactions
- View transaction history
- Transaction details
- Confirm delivery with code
- Leave reviews
- **Signature capture** using PencilKit for delivery confirmation

### Profile
- View and edit profile
- Settings (notifications, privacy, language)
- Export personal data
- Deactivate account
- Delete account
- Logout
- **ID verification** using VisionKit document scanning

### Advanced Features

#### Widgets (WidgetKit)
- **Market Snapshot Widget**: View current crop prices and trends from home screen
- **Order Status Widget**: Track active deliveries from home screen

#### Live Activities (ActivityKit)
- **Delivery Tracking**: Real-time delivery updates on Dynamic Island and Lock Screen

#### App Clip
- **Quick Listing View**: Browse listings without full app installation

#### Siri Shortcuts (Intents)
- **Search Listings**: "Search for maize listings on ZimAgriTrust"
- **Create Listing**: "Create a new listing on ZimAgriTrust"
- **Check Wallet**: "Check my wallet balance on ZimAgriTrust"

#### Apple Watch Companion App
- View listings on Apple Watch
- Check wallet balance
- Receive notifications

#### CloudKit Integration
- iCloud sync for offline data
- Automatic data backup and sync across devices

#### In-App Purchases (StoreKit)
- Premium subscription (monthly/yearly)
- Featured listing upgrades
- Verification badge purchase

#### Location Services
- **Core Location**: GPS tracking for location-based features
- **MapKit**: Interactive maps for listings and navigation
- **Geofencing**: Notifications for pickup/delivery locations

## API Integration

The app uses the existing ZimAgriTrust backend API:

- Base URL: Configurable in `APIConfig.swift`
- Authentication: Bearer token (stored in Keychain)
- Content-Type: application/json
- Multipart upload for images

## Dependencies

### Standard iOS Frameworks Used
- SwiftUI (UI framework)
- Combine (Reactive programming)
- Foundation (Core functionality)
- UIKit (Interoperability)
- CoreData (Offline storage)
- Security (Keychain access)
- CoreLocation (GPS tracking)
- MapKit (Maps and routing)
- VisionKit (Document scanning)
- PencilKit (Signature capture)
- WidgetKit (Home screen widgets)
- ActivityKit (Live Activities)
- PassKit (Apple Pay)
- StoreKit (In-app purchases)
- CloudKit (iCloud sync)
- UserNotifications (Push notifications)
- PhotosUI (Image picker)
- Intents (Siri Shortcuts)
- Charts (Data visualization)

### Third-Party Dependencies
None required - uses only Apple's native frameworks for maximum performance and security.

## Entitlements

The app requires the following entitlements (configured in `ZimAgriTrust.entitlements`):

- **App Groups**: For sharing data between app and widgets
- **Keychain Access**: For secure token storage
- **Push Notifications**: For remote notifications
- **Sign in with Apple**: For Apple authentication
- **iCloud**: For CloudKit sync
- **In-App Purchase**: For StoreKit
- **Associated Domains**: For Universal Links
- **Background Modes**: For location updates and background fetch
- **Background Location Updates**: For driver tracking

## Testing

### Unit Testing
Test ViewModels and Services:
```swift
// Example: Test AuthViewModel
let viewModel = AuthViewModel()
await viewModel.login(phone: "+263123456789", password: "password")
XCTAssertTrue(viewModel.isAuthenticated)
```

### UI Testing
Test critical user flows:
- Login and registration
- Create listing
- Make offer
- Payment flow
- Delivery confirmation

### Integration Testing
Test API integration:
- Mock API responses
- Test error handling
- Test offline scenarios with CoreData

## Deployment

### App Store Connect Setup

1. **Create App Record**
   - Bundle ID: `com.zimagritrust.ios`
   - SKU: ZIMAGRI-TRUST-001
   - Platform: iOS

2. **Configure Signing**
   - Create development certificate
   - Create distribution certificate
   - Register devices for testing

3. **Push Notifications**
   - Create APNs key
   - Upload to App Store Connect
   - Configure in backend

4. **In-App Purchases**
   - Create product IDs in App Store Connect
   - Configure subscription groups
   - Set pricing tiers

5. **Submit for Review**
   - Upload build via Xcode Organizer
   - Complete app information
   - Submit screenshots
   - Provide demo account

### Environment Configuration

**Development:**
- API URL: `http://localhost:8080/api/v1`
- APNs: Development sandbox
- Sign in with Apple: Development

**Production:**
- API URL: `https://api.zimagritrust.com/api/v1`
- APNs: Production
- Sign in with Apple: Production

## Performance Optimizations

- **Lazy Loading**: Views load data only when needed
- **Image Caching**: AsyncImage with built-in caching
- **CoreData**: Offline storage for faster access
- **Combine**: Efficient reactive state management
- **Background Tasks**: Non-blocking API calls
- **Widget Updates**: Optimized refresh intervals

## Security Features

- **Keychain Storage**: Secure token storage
- **Biometric Auth**: Face ID / Touch ID support
- **SSL/TLS**: Encrypted API communication
- **App Transport Security**: Enforces HTTPS
- **Sign in with Apple**: Secure OAuth flow
- **Apple Pay**: Secure payment processing

## Accessibility

- **VoiceOver**: Full screen reader support
- **Dynamic Type**: Respects user font size preferences
- **Dark Mode**: Automatic dark/light mode support
- **Reduced Motion**: Respects motion preferences
- **High Contrast**: Supports high contrast mode

## Localization

The app is designed for Zimbabwe:
- Currency: USD and ZWL support
- Phone format: Zimbabwe (+263)
- Location: Zimbabwe cities and regions
- Language: English (expandable to other languages)

## Troubleshooting

### Common Issues

**Build Errors:**
- Ensure Xcode 15.0+
- Clean build folder (Cmd+Shift+K)
- Reinstall pods if using CocoaPods

**API Connection Issues:**
- Check API URL in `APIConfig.swift`
- Verify backend is running
- Check network connectivity
- Review SSL certificates

**Widget Not Showing:**
- Add widget to home screen
- Check App Groups configuration
- Verify widget extension is included in target

**Push Notifications Not Working:**
- Verify APNs certificate
- Check device token registration
- Review backend notification service

## Support

For issues or questions:
- Check backend API documentation at `/docs`
- Review console logs in Xcode
- Verify network connectivity
- Check API base URL configuration
- Review entitlements configuration

## License

Proprietary - ZimAgriTrust © 2026
