# @agritrust/shared

Shared utilities, types, and API clients for Agritrust applications.

## Installation

```bash
npm install
```

## Build

```bash
npm run build
```

## Watch mode

```bash
npm run watch
```

## Contents

- **types**: TypeScript type definitions for User, Listing, Order, Transaction, etc.
- **api**: Axios-based API client with authentication
- **utils**: Authentication and permission utilities
- **constants**: Shared constants (routes, roles, status, etc.)

## Usage

```typescript
import { getApiClient, USER_ROLES } from '@agritrust/shared';

const api = getApiClient();
const user = await api.getCurrentUser();
```
