# ZimAgriTrust Shared Package

This package contains the core logic and UI components shared across the ZimAgriTrust platform (Web Portal, Mobile App, and Public Website).

## Architecture

- **api/**: Axios client and base configuration.
- **stores/**: Zustand stores for state management.
- **components/**: Common UI components (React).
- **types/**: Shared TypeScript interfaces.
- **utils/**: Common validators and formatters.

## Shared Stores

- `useAuthStore`: Handles authentication, user session, and role management.
- `useListingStore`: Manages marketplace listings and farmer-specific listings.
- `useOfferStore`: Handles making and receiving offers.
- `useOrderStore`: Manages the lifecycle of orders.
- `useWalletStore`: Handles balances and transactions.

## Shared Components

- `Button`: Versatile button with variants and loading states.
- `Input`: Branded input with icons and validation support.
- `Card`: Premium card container with hover effects.
- `Modal`: Clean modal for confirmations and forms.

## Usage

```tsx
import { useAuthStore, Button } from '@agritrust/shared';

const MyComponent = () => {
  const { user } = useAuthStore();
  return <Button>Welcome, {user.full_name}</Button>;
};
```
