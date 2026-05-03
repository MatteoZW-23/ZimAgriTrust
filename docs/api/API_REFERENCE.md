# Complete API Endpoints Reference - ZimAgritrust Platform

**Base URL:** `http://localhost:8080/api/v1` (configurable via `VITE_API_URL` environment variable)

---

## 📋 Table of Contents
1. [Authentication](#authentication)
2. [Admin Management](#admin-management)
3. [WhatsApp Integration](#whatsapp-integration)
4. [Market & Listings](#market--listings)
5. [Transactions & Payments](#transactions--payments)
6. [Disputes](#disputes)
7. [Logistics & Drivers](#logistics--drivers)
8. [Verification](#verification)
9. [Academy & Training](#academy--training)
10. [AI & Predictions](#ai--predictions)
11. [USSD](#ussd)
12. [Public Endpoints](#public-endpoints)
13. [Vision Services](#vision-services)

---

## 🔐 Authentication

### Prefix: `/auth`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/forgot-password` | Request password reset via OTP | No |
| POST | `/auth/reset-password` | Reset password with OTP | No |
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | User login | No |
| POST | `/auth/verify-login-2fa` | Verify 2FA code after login | No |
| POST | `/auth/admin/login` | Admin login | No |
| POST | `/auth/admin/verify-2fa` | Verify admin 2FA code | No |
| POST | `/auth/agent/login` | Agent login | No |
| POST | `/auth/agent/verify-2fa` | Verify agent 2FA code | No |
| POST | `/auth/mfa/setup` | Setup MFA for user | Yes |
| POST | `/auth/mfa/confirm` | Confirm MFA setup | Yes |
| POST | `/auth/driver/login` | Driver login | No |
| POST | `/auth/driver/verify-2fa` | Verify driver 2FA code | No |
| POST | `/auth/refresh` | Refresh access token | Yes |
| POST | `/auth/logout` | Logout user | Yes |
| GET | `/auth/me` | Get current user profile | Yes |
| POST | `/auth/change-pin` | Change user PIN | Yes |
| POST | `/auth/change-password` | Change user password | Yes |
| PATCH | `/auth/profile` | Update user profile | Yes |
| PATCH | `/auth/notifications` | Update notification preferences | Yes |
| POST | `/auth/deactivate` | Deactivate user account | Yes |
| DELETE | `/auth/account` | Delete user account | Yes |

---

## 👨‍💼 Admin Management

### Prefix: `/admin`

#### Admin Users
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/users` | List all users | Admin/Agent |
| POST | `/admin/users/bulk-verify` | Bulk verify users | Admin |
| POST | `/admin/users/{user_id}/verify-reject` | Reject user verification | Admin |
| POST | `/admin/users/{user_id}/reset-password` | Reset user password | Admin |
| PATCH | `/admin/users/{user_id}/role` | Update user role | Admin |
| POST | `/admin/users/enroll` | Enroll new user | Admin |
| DELETE | `/admin/users/{user_id}` | Delete user | Admin |
| POST | `/admin/users/{user_id}/verify` | Verify user | Admin |
| POST | `/admin/users/{user_id}/status` | Update user status | Admin |
| POST | `/admin/users/{user_id}/reinstate` | Reinstate suspended user | Admin |
| POST | `/admin/users/{user_id}/trust` | Adjust user trust score | Admin |

#### Admin Transactions
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/transactions` | List all transactions | Admin |
| GET | `/admin/transactions/{order_id}` | Get transaction details | Admin |
| POST | `/admin/transactions/escrow/{order_id}/force-release` | Force release escrow | Admin |
| POST | `/admin/transactions/escrow/{order_id}/force-refund` | Force refund escrow | Admin |

#### Admin System
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/system/health` | System health check | Admin |
| GET | `/admin/system/logs` | System logs | Admin |
| GET | `/admin/system/risk-watch` | Risk watch alerts | Admin |

#### Admin Management (Multi-Location)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/admin-management/locations` | List all locations | Admin |
| POST | `/admin/admin-management/locations` | Create new location | Admin |
| POST | `/admin/admin-management/create` | Create new admin | Admin |
| POST | `/admin/admin-management/invite` | Invite new admin | Admin |
| GET | `/admin/admin-management/list` | List all admins | Admin |
| GET | `/admin/admin-management/{admin_id}` | Get admin details | Admin |
| PATCH | `/admin/admin-management/{admin_id}/status` | Update admin status | Admin |
| DELETE | `/admin/admin-management/{admin_id}` | Delete admin | Admin |
| POST | `/admin/admin-management/permissions/grant` | Grant permission to admin | Admin |
| POST | `/admin/admin-management/permissions/revoke` | Revoke permission from admin | Admin |
| GET | `/admin/admin-management/{admin_id}/permissions` | List admin permissions | Admin |
| POST | `/admin/admin-management/delegations/create` | Create delegation | Admin |
| POST | `/admin/admin-management/delegations/{delegation_id}/revoke` | Revoke delegation | Admin |
| GET | `/admin/admin-management/delegations` | List delegations | Admin |
| GET | `/admin/admin-management/audit-logs` | List audit logs | Admin |

#### Admin Other
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/overview` | Admin dashboard overview | Admin |
| GET | `/admin/agents` | List agents | Admin |
| GET | `/admin/listings` | Admin listings | Admin |
| GET | `/admin/disputes` | Admin disputes | Admin |
| GET | `/admin/config` | System configuration | Admin |
| GET | `/admin/analytics` | Analytics data | Admin |
| GET | `/admin/ai` | AI model status | Admin |
| GET | `/admin/notifications` | Notification settings | Admin |
| GET | `/admin/scraping` | Scraping status | Admin |
| GET | `/admin/command-center` | Command center | Admin |
| GET | `/admin/academy` | Academy data | Admin |
| GET | `/admin/permissions` | Permission list | Admin |

---

## 📱 WhatsApp Integration

### Prefix: `/whatsapp`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/whatsapp/webhook` | WhatsApp webhook (incoming messages) | No |
| GET | `/whatsapp/webhook` | WhatsApp webhook verification | No |
| GET | `/whatsapp/status` | WhatsApp service status | No |
| POST | `/whatsapp/test-alert` | Send test alert | Admin |
| POST | `/whatsapp/broadcast` | Broadcast message to users | Admin |
| POST | `/whatsapp/alerts/price` | Send price alert | Admin |
| POST | `/whatsapp/alerts/weather` | Send weather alert | Admin |
| POST | `/whatsapp/alerts/harvest` | Send harvest alert | Admin |
| POST | `/whatsapp/reminders/delivery` | Send delivery reminder | Admin |
| POST | `/whatsapp/reminders/payment` | Send payment reminder | Admin |
| POST | `/whatsapp/reminders/verification/{user_id}` | Send verification reminder | Admin |
| POST | `/whatsapp/payment/initiate` | Initiate payment via WhatsApp | Yes |
| POST | `/whatsapp/payment/receipt` | Send payment receipt | Yes |
| POST | `/whatsapp/location/share` | Share location via WhatsApp | Yes |
| POST | `/whatsapp/interactive/listing/{listing_id}` | Interactive listing message | Yes |
| GET | `/whatsapp/analytics/engagement/{user_id}` | Get user engagement analytics | Admin |
| POST | `/whatsapp/analytics/track` | Track analytics event | No |
| POST | `/whatsapp/market/demand` | Report market demand | Yes |
| POST | `/whatsapp/groups/create` | Create WhatsApp group | Admin |
| POST | `/whatsapp/groups/{group_id}/message` | Send message to group | Admin |
| POST | `/whatsapp/translate` | Translate message | Yes |
| POST | `/whatsapp/detect-language` | Detect message language | Yes |

---

## 🌾 Market & Listings

### Prefix: `/market`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/market/news` | Get market news | No |
| GET | `/market/summary` | Market summary | No |
| GET | `/market/analytics/regional` | Regional analytics | Yes |
| GET | `/market/analytics/trends/{crop}` | Crop trends analytics | Yes |
| GET | `/market/demand/{crop}` | Crop demand data | Yes |
| GET | `/market/risk/{target_user_id}` | Risk assessment for user | Admin |
| GET | `/market/fraud-alerts` | Fraud alerts | Admin |
| GET | `/market/pulse` | Market pulse data | No |
| GET | `/market/catalog` | Market catalog | No |

### Prefix: `/listings`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/listings` | Create new listing | Yes |
| GET | `/listings/search` | Search listings | No |
| GET | `/listings` | List all listings | No |
| GET | `/listings/me` | List my listings | Yes |
| POST | `/listings/{listing_id}/offers` | Make offer on listing | Yes |
| GET | `/listings/{listing_id}/offers` | Get offers for listing | Yes |
| POST | `/listings/{listing_id}/offers/{offer_id}/accept` | Accept offer | Yes |
| POST | `/listings/{listing_id}/offers/{offer_id}/reject` | Reject offer | Yes |
| POST | `/listings/{listing_id}/offers/{offer_id}/counter` | Counter offer | Yes |

### Prefix: `/procurement` (Buyer Requests)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/procurement` | Create buyer request | Buyer |
| GET | `/procurement` | List buyer requests | Buyer |
| POST | `/procurement/{request_id}/respond` | Respond to buyer request | Farmer |
| POST | `/procurement/responses/{response_id}/accept` | Accept farmer response | Buyer |

### Prefix: `/trades` (Negotiation)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/trades/{listing_id}/start` | Start trade session | Yes |
| GET | `/trades/sessions` | List trade sessions | Yes |
| POST | `/trades/{session_id}/messages` | Send trade message | Yes |
| GET | `/trades/{session_id}/messages` | Get trade messages | Yes |

---

## 💰 Transactions & Payments

### Prefix: `/transactions`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/transactions` | List orders | Yes |
| GET | `/transactions/{order_id}` | Get order details | Yes |
| POST | `/transactions/{order_id}/confirm-delivery` | Confirm delivery | Yes |
| GET | `/transactions/{order_id}/transactions` | Get order transactions | Yes |
| POST | `/transactions/{order_id}/review` | Submit review | Yes |
| GET | `/transactions/{order_id}/reviews` | Get order reviews | No |
| GET | `/transactions/{order_id}/receipt` | Get order receipt | Yes |
| POST | `/transactions/{order_id}/transport-survey` | Submit transport survey | Yes |

### Prefix: `/payments`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/payments/ecocash/callback` | EcoCash payment callback | No |
| POST | `/payments/onemoney/callback` | OneMoney payment callback | No |
| GET | `/payments/balance` | Get wallet balance | Yes |
| GET | `/payments/fee-preview` | Preview transaction fees | No |
| POST | `/payments/initiate` | Initiate payment | Yes |
| GET | `/payments/status/{payment_ref}` | Get payment status | Yes |
| POST | `/payments/refund/{order_id}` | Refund payment | Admin |
| GET | `/payments/earnings` | Get earnings | Yes |
| GET | `/payments/wallet/transactions` | Get wallet transactions | Yes |
| POST | `/payments/deposit` | Deposit to wallet | Yes |
| POST | `/payments/withdraw` | Withdraw from wallet | Yes |

---

## ⚖️ Disputes

### Prefix: `/disputes`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/disputes` | Create new dispute | Yes |
| GET | `/disputes` | List disputes | Yes |
| POST | `/disputes/{dispute_id}/resolve` | Resolve dispute | Admin |
| POST | `/disputes/{dispute_id}/propose-settlement` | Propose settlement | Admin |
| POST | `/disputes/{dispute_id}/accept-settlement` | Accept settlement | Yes |

---

## 🚚 Logistics & Drivers

### Prefix: `/logistics`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/logistics/trips` | List logistics trips | Yes |
| POST | `/logistics/trips` | Create logistics trip | Yes |
| GET | `/logistics/trips/{trip_id}/manifest` | Get trip manifest | Yes |
| GET | `/logistics/orders/{order_id}/delivery` | Get order delivery info | Yes |
| POST | `/logistics/orders/{order_id}/delivery/method` | Set delivery method | Yes |
| POST | `/logistics/orders/{order_id}/delivery/assign-agent` | Assign delivery agent | Yes |
| POST | `/logistics/orders/{order_id}/delivery/assign-driver` | Assign driver | Yes |
| POST | `/logistics/orders/{order_id}/delivery/pickup-in-progress` | Mark pickup in progress | Yes |
| POST | `/logistics/orders/{order_id}/delivery/confirm-pickup` | Confirm pickup | Yes |
| POST | `/logistics/orders/{order_id}/delivery/delay` | Report delivery delay | Yes |
| POST | `/logistics/orders/{order_id}/delivery/arrived` | Mark as arrived | Yes |
| POST | `/logistics/orders/{order_id}/delivery/confirm-delivery` | Confirm delivery | Yes |
| POST | `/logistics/orders/{order_id}/delivery/confirm-receipt` | Confirm receipt | Yes |

### Prefix: `/drivers`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/drivers/profile` | Update driver profile | Driver |
| POST | `/drivers/documents/upload` | Upload driver documents | Driver |
| POST | `/drivers/submit-verification` | Submit for verification | Driver |
| GET | `/drivers/me` | Get driver profile | Driver |
| POST | `/drivers/availability` | Update availability | Driver |
| POST | `/drivers/location` | Update location | Driver |
| GET | `/drivers/location/{job_id}` | Get job location | Driver |
| GET | `/drivers/jobs/available` | List available jobs | Driver |
| POST | `/drivers/jobs/{job_id}/accept` | Accept job | Driver |
| POST | `/drivers/jobs/{job_id}/pickup` | Confirm pickup | Driver |
| POST | `/drivers/jobs/{job_id}/deliver` | Confirm delivery | Driver |
| POST | `/drivers/jobs/{job_id}/cancel` | Cancel job | Driver |
| GET | `/drivers/jobs/my` | List my jobs | Driver |
| GET | `/drivers/earnings` | Get earnings | Driver |
| GET | `/drivers/reviews` | Get reviews | Driver |
| GET | `/drivers/tier` | Get tier status | Driver |
| GET | `/drivers/earnings/breakdown` | Get earnings breakdown | Driver |
| GET | `/drivers/fare/estimate` | Get fare estimate | Driver |
| POST | `/drivers/jobs/{job_id}/negotiate` | Negotiate fare | Driver |
| POST | `/drivers/farmer/transport` | Request transport for farmer | Driver |
| POST | `/drivers/farmer/departure` | Mark farmer departure | Driver |
| POST | `/drivers/farmer/location` | Update farmer location | Driver |
| GET | `/drivers/admin/pending` | List pending drivers | Admin |
| POST | `/drivers/admin/{driver_id}/approve` | Approve driver | Admin |
| POST | `/drivers/admin/{driver_id}/reject` | Reject driver | Admin |
| GET | `/drivers/admin/all` | List all drivers | Admin |
| POST | `/drivers/admin/jobs/create` | Create driver job | Admin |

---

## ✅ Verification

### Prefix: `/verification`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/verification/types` | Get document types | No |
| POST | `/verification/submit` | Submit verification request | Yes |
| GET | `/verification/my-status` | Get my verification status | Yes |
| GET | `/verification/queue` | Get verification queue | Admin/Agent |
| GET | `/verification/document/{request_id}/{slot}` | Get document | Admin/Agent |
| POST | `/verification/{request_id}/approve` | Approve verification | Admin |
| POST | `/verification/{request_id}/reject` | Reject verification | Admin |

### Prefix: `/verification-workflow`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/verification-workflow/submit` | Submit verification document | Yes |
| GET | `/verification-workflow/my-documents` | Get my documents | Yes |
| GET | `/verification-workflow/my-status` | Get verification status | Yes |
| GET | `/verification-workflow/document-types` | Get document types | No |
| GET | `/verification-workflow/required-for-role` | Get required docs for role | No |
| GET | `/verification-workflow/review-queue` | Get review queue | Admin/Agent |
| POST | `/verification-workflow/assign/{queue_id}` | Assign reviewer | Admin/Agent |
| POST | `/verification-workflow/review/{document_id}` | Review document | Admin/Agent |
| GET | `/verification-workflow/document/{document_id}` | Get document | Admin/Agent |
| GET | `/verification-workflow/file/{document_id}/{file_type}` | Get document file | Admin/Agent |
| GET | `/verification-workflow/stats` | Get verification stats | Admin/Agent |
| GET | `/verification-workflow/users-by-status` | Get users by status | Admin |
| GET | `/verification-workflow/audit-log` | Get audit log | Admin |
| POST | `/verification-workflow/bulk-approve` | Bulk approve | Admin |
| POST | `/verification-workflow/suspend-user-verification` | Suspend verification | Admin |

---

## 🎓 Academy & Training

### Prefix: `/academy`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/academy/login` | Academy login | Yes |
| GET | `/academy/my-progress` | Get my progress | Yes |
| GET | `/academy/modules/{module_number}/content` | Get module content | Yes |
| GET | `/academy/modules/{module_number}/topics/{topic_id}/content` | Get topic content | Yes |
| POST | `/academy/modules/{module_number}/topics/{topic_id}/complete` | Mark topic complete | Yes |
| POST | `/academy/modules/{module_number}/quiz/submit` | Submit module quiz | Yes |
| POST | `/academy/exam/mid/submit` | Submit mid-term exam | Yes |
| GET | `/academy/exam/final/questions` | Get final exam questions | Yes |
| POST | `/academy/exam/final/submit` | Submit final exam | Yes |
| GET | `/academy/certificate` | Get certificate | Yes |

### Prefix: `/onboarding`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/onboarding/contract/{application_id}/sign` | Sign contract | Yes |
| GET | `/onboarding/academy/modules` | Get academy modules | No |
| POST | `/onboarding/academy/{application_id}/quiz` | Submit quiz | Yes |
| POST | `/onboarding/shadowing` | Start shadowing | Admin/Agent |
| POST | `/onboarding/shadowing/{application_id}/evaluate` | Evaluate shadowing | Admin/Agent |
| GET | `/onboarding/exam` | Get exam questions | Yes |
| POST | `/onboarding/exam/submit` | Submit exam | Yes |
| GET | `/onboarding/status/{application_id}` | Get onboarding status | Yes |

### Prefix: `/recruitment`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/recruitment/applications` | List applications | Admin |
| POST | `/recruitment/apply` | Apply as agent | No |
| GET | `/recruitment/my-status/{phone_number}` | Get application status | No |
| POST | `/recruitment/{application_id}/documentation` | Submit documentation | Admin |
| POST | `/recruitment/{application_id}/training/module/{module_id}` | Complete training module | Yes |
| POST | `/recruitment/{application_id}/equipment` | Issue equipment | Admin |
| POST | `/recruitment/{application_id}/practical` | Complete practical | Admin |
| POST | `/recruitment/{application_id}/shadowing` | Start shadowing | Admin/Agent |
| POST | `/recruitment/{application_id}/supervised-task` | Complete supervised task | Admin/Agent |
| POST | `/recruitment/{application_id}/certify` | Certify agent | Admin |

---

## 🤖 AI & Predictions

### Prefix: `/ai`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/ai/models/status` | Get AI model status | Admin |
| POST | `/ai/vision/analyze-crop` | Analyze crop image | Yes |
| POST | `/ai/vision/detect-disease` | Detect crop disease | Yes |
| POST | `/ai/vision/full-analysis` | Full image analysis | Yes |
| GET | `/ai/forecast/market-intelligence` | Market intelligence forecast | Admin |
| GET | `/ai/forecast/demand` | Demand forecast | Admin |
| POST | `/ai/forecast/yield` | Yield prediction | Yes |
| POST | `/ai/match/agent` | Match with agent | Yes |
| GET | `/ai/recommendations/farmer` | Get farmer recommendations | Yes |
| POST | `/ai/train/{model_name}` | Train model | Admin |
| GET | `/ai/nlp/analyze-intent` | Analyze message intent | Yes |
| GET | `/ai/financial/loan-eligibility/{user_id}` | Check loan eligibility | Admin |
| GET | `/ai/research/proof-of-concept` | Research proof of concept | Admin |

### Prefix: `/predictions`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/predictions/price` | Get price predictions | No |
| GET | `/predictions/risk/{user_id}` | Get risk predictions | Admin |

---

## 📞 USSD

### Prefix: `/ussd`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/ussd/session` | USSD session handler | No |

---

## 🌍 Public Endpoints

### Prefix: `/public`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/public/prices/current` | Current prices | No |
| GET | `/public/prices/trending` | Trending prices | No |
| GET | `/public/news` | Market news | No |
| GET | `/public/weather` | Weather data | No |
| GET | `/public/calendar` | Agricultural calendar | No |
| GET | `/public/stats` | Platform statistics | No |
| GET | `/public/listings` | Public listings | No |
| GET | `/public/listings/{listing_id}` | Get listing details | No |
| GET | `/public/fee-preview` | Preview fees | No |

---

## 👁️ Vision Services

### No Prefix

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/analyze-crop` | Analyze crop image | Yes |
| POST | `/verify-listing` | Verify listing image | Yes |
| POST | `/detect-disease` | Detect crop disease | Yes |
| POST | `/process` | Process vision webhook | No |

---

## 📝 Notes

### Authentication Headers
Most authenticated endpoints require:
```
Authorization: Bearer <token>
```

### Content Type
POST/PUT/PATCH requests typically require:
```
Content-Type: application/json
```

### Environment Variables
- `VITE_API_URL`: Base API URL (default: `http://localhost:8080/api/v1`)
- Can be configured in `.env` files

### Rate Limiting
Some endpoints may have rate limiting applied. Check response headers for:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

### Pagination
List endpoints support pagination via query parameters:
- `limit`: Number of items per page (default: 100)
- `offset`: Number of items to skip (default: 0)

### Error Responses
Standard error format:
```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

---

**Last Updated:** May 1, 2026
**API Version:** v1
**Base URL:** `http://localhost:8080/api/v1`
