# ZimAgriDriver iOS App

Native iOS app built with SwiftUI for ZimAgriTrust delivery drivers.

## Prerequisites

- Xcode 15.0 or later
- iOS 16.0 or later deployment target
- Swift 5.9+

## Project Structure

```
ZimAgriDriver/
├── Models/              # Data models
│   └── DriverModels.swift
├── Views/               # SwiftUI views
│   ├── ContentView.swift
│   ├── OTPLoginView.swift
│   ├── DriverRegistrationView.swift
│   ├── DeliveriesTabView.swift
│   ├── DeliveryDetailView.swift
│   └── ProfileTabView.swift
├── Services/            # Business logic and API clients
│   ├── APIConfig.swift
│   ├── APIClient.swift
│   ├── KeychainHelper.swift
│   └── DriverService.swift
└── Resources/           # Assets, images, etc.
```

## Setup Instructions

### 1. Create New Xcode Project

1. Open Xcode
2. File → New → Project
3. Select "App" under iOS
4. Product Name: `ZimAgriDriver`
5. Interface: SwiftUI
6. Language: Swift
7. Save to: `c:\Users\MJ\Desktop\Agric\apps\ios-driver-app\`

### 2. Import Source Files

After creating the Xcode project:

1. Delete the default `ContentView.swift` (we have our own)
2. Copy all files from the `ZimAgriDriver/` folder into your Xcode project
3. Ensure all files are added to the target

### 3. Configure API Base URL

Edit `Services/APIConfig.swift` to set your production backend URL:

```swift
#if DEBUG
static let baseURL = "http://localhost:8080/api/v1"
#else
static let baseURL = "https://api.zimagritrust.com/api/v1"  // Change this
#endif
```

### 4. Build and Run

1. Select a simulator or connected device
2. Press Cmd+R to build and run
3. The app will start on the OTP Login screen

## Features Implemented

### Authentication
- OTP-based login (phone number + OTP)
- Self-registration for new drivers
- Secure token storage using Keychain

### Deliveries
- View assigned deliveries
- Confirm pickup
- Confirm delivery with code
- Submit transport survey
- Delivery status tracking

### Profile
- Driver profile header
- Delivery statistics
- Settings
- Logout

## API Integration

The app uses the existing ZimAgriTrust backend API:

- Base URL: Configurable in `APIConfig.swift`
- Authentication: Bearer token (stored in Keychain)
- Content-Type: application/json

## Driver-Specific Endpoints

- `POST /api/v1/auth/driver/request-otp` - Request OTP
- `POST /api/v1/auth/driver/verify-otp` - Verify OTP and login
- `POST /api/v1/drivers/self-register` - Self-registration
- `GET /api/v1/logistics/orders` - Get assigned deliveries
- `PUT /api/v1/logistics/orders/{id}/status` - Update delivery status
- `POST /api/v1/logistics/orders/{id}/pickup` - Confirm pickup
- `POST /api/v1/logistics/orders/{id}/confirm-delivery` - Confirm delivery
- `POST /api/v1/transactions/{id}/transport-survey` - Submit survey

## Testing

To test the app:

1. Ensure your backend is running on `http://localhost:8080` or update the API URL
2. Request OTP with a phone number
3. Enter OTP to login
4. View assigned deliveries
5. Test pickup and delivery flows
6. Submit transport survey

## Deployment

### App Store Connect

1. Create app in App Store Connect
2. Configure bundle identifier
3. Set up signing certificates
4. Upload build via Xcode Organizer
5. Submit for review

## Known Limitations

- Edit profile functionality not implemented (UI placeholder)
- Settings screen is a placeholder
- No push notifications (can be added similar to user app)
- Limited error handling in some flows

## Next Steps

1. Test all flows with real backend
2. Add unit tests for services and models
3. Implement push notifications
4. Add more comprehensive error handling
5. Implement profile editing
6. Add analytics tracking
7. Implement deep linking

## Support

For issues or questions:
- Check backend API documentation
- Review console logs in Xcode
- Verify network connectivity
- Check API base URL configuration
