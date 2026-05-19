# ZimAgriTrust Shared Framework

Common code shared between iOS User App and Driver App.

## Overview

This framework contains shared models, utilities, and API client code that is used by both the User App and Driver App to avoid code duplication and ensure consistency.

## Structure

```
SharedFramework/
├── SharedModels.swift       # Common data models
├── SharedAPIClient.swift    # Shared API client
├── SharedUtilities.swift    # Common utilities and helpers
└── README.md               # This file
```

## Components

### SharedModels.swift

Contains common data models used across both apps:

- `User` - User profile data
- `Listing` - Agricultural product listings
- `Transaction` - Transaction records
- `Delivery` - Delivery information
- `Driver` - Driver profile data
- `DriverRegistration` - Driver registration data
- `TransportSurvey` - Transport survey data
- `TransactionStatus` - Transaction status enum
- `DeliveryStatus` - Delivery status enum
- `APIError` - Common error types

### SharedAPIClient.swift

Shared HTTP client for API communication:

- Singleton pattern for consistent API access
- Automatic token management
- Generic GET, POST, PUT, DELETE methods
- Error handling
- Timeout configuration

### SharedUtilities.swift

Common utility functions:

- **Date Utilities**: Date formatting, time ago calculations
- **String Utilities**: Email/phone validation, currency formatting
- **Image Utilities**: Image resizing and compression
- **Validation Utilities**: Input validation helpers
- **Storage Utilities**: UserDefaults wrapper
- **Logging Utilities**: Structured logging with levels

## Usage

### In User App

```swift
import SharedFramework

// Use shared models
let listing = Listing(id: 1, seller_id: 1, crop_name: "Maize", ...)

// Use shared API client
let apiClient = SharedAPIClient.shared
apiClient.setAuthToken(token)
let listings: [Listing] = try await apiClient.get("/listings")

// Use shared utilities
let isValid = Validator.validateEmail(email)
let timeAgo = date.timeAgo()
```

### In Driver App

```swift
import SharedFramework

// Same usage as User App
// Ensures consistency across both apps
```

## Benefits

1. **Code Reuse**: Avoid duplicating models and utilities
2. **Consistency**: Same data structures across apps
3. **Maintainability**: Single source of truth for common code
4. **Type Safety**: Shared models ensure type consistency
5. **Testing**: Easier to test shared code once

## Configuration

The API base URL is configured in `APIConfig`:

- **Debug**: `http://localhost:8080/api/v1`
- **Release**: `https://api.zimagritrust.com/api/v1`

## Adding New Shared Code

1. Add new models to `SharedModels.swift`
2. Add new utilities to `SharedUtilities.swift`
3. Update this README with documentation
4. Ensure both apps import the framework

## Version History

- **1.0.0** - Initial release with core models, API client, and utilities
