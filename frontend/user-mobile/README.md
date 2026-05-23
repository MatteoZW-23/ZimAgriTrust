# Agritrust User Mobile App

This is the unified mobile application for Agritrust that supports two user roles:
- **Farmers**: Sell crops, manage listings, view orders
- **Buyers**: Browse marketplace, make offers, track orders

## Architecture

The app uses role-based rendering to show different interfaces based on the user's role after login.

### Role-Specific Features

#### Farmer
- Home dashboard with farm overview
- Create and manage crop listings
- View incoming offers
- Track order status
- Wallet management
- Profile and verification status

#### Buyer
- Browse marketplace
- Make offers on listings
- Track order status
- Wallet management
- Profile and verification status

## Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Start with specific platform
npm start --ios
npm start --android
```

## Environment Variables

```env
EXPO_PUBLIC_API_URL=http://localhost:8080/api/v1
```

## Role-Based Navigation

The app uses React Navigation with role-specific tab configurations:
- Farmers see: Home, Orders, Add Listing, Wallet, Profile
- Buyers see: Market, Orders, Wallet, Profile

## API Integration

The app communicates with the backend API at `/api/v1` endpoints for:
- Authentication (login, register)
- Listings (CRUD operations)
- Orders (create, update status)
- Wallet (balance, transactions)
- Profile (user data, verification)

## Note About Drivers

Drivers (transporters) should use the **separate Agritrust Driver Mobile App**. This app is exclusively for farmers and buyers.
