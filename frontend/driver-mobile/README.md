# Agritrust Driver Mobile App

Dedicated mobile application for Agritrust drivers (transporters).

## Purpose

This app is exclusively for drivers to manage delivery operations:
- View available delivery jobs
- Accept and manage deliveries
- Track delivery status
- View earnings and payment history
- Manage driver profile

## Architecture

This is a **standalone mobile application** separate from the User Mobile App (farmer/buyer).

### Key Differences from User Mobile App

- **Role-specific**: Only supports `driver` (transporter) role
- **Optimized workflows**: Focus on logistics and delivery operations
- **Simplified navigation**: Driver-specific tabs and screens
- **No marketplace access**: Cannot browse or purchase crops

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

## Driver-Specific Features

### Tabs
- **Jobs**: View available delivery jobs
- **Deliveries**: Active and completed deliveries
- **Earnings**: Payment history and balance
- **Profile**: Driver profile and vehicle information

### Screens
- Login screen (driver-specific)
- Job details
- Delivery tracking
- Earnings breakdown
- Profile management
- Vehicle information

## API Integration

The app communicates with the backend API at `/api/v1` endpoints:
- Authentication (login as driver)
- Jobs (view available delivery jobs)
- Deliveries (manage active deliveries)
- Earnings (view payment history)
- Profile (driver profile management)

## Security

- Drivers can only access driver-specific endpoints
- No access to marketplace, listings, or purchasing features
- Role enforced at both frontend and backend levels
