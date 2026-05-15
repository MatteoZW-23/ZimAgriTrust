# ZimAgritrust Transport Payment System - Test Plan

## Overview
This document outlines the comprehensive test plan for the ZimAgritrust Transport Payment System, ensuring the core business rule "WHOEVER REQUESTS TRANSPORT = WHO PAYS FOR TRANSPORT" is enforced across all components.

## Test Environment Setup

### Prerequisites
- Database migration 0030 applied
- All transport services deployed
- Mobile apps updated with new screens
- Test users: Buyer, Farmer, Driver, Admin
- Test payment methods: Stripe, Paynow, Wallet

### Test Data
- Test orders with various states
- Test drivers with different vehicle types
- Test locations (pickup/delivery addresses)
- Test transport fee amounts

---

## Test Scenarios

### 1. Database Migration Tests

#### 1.1 Migration Execution
- [ ] Run migration 0030 successfully
- [ ] Verify all tables created
- [ ] Verify all enums created
- [ ] Verify indexes created
- [ ] Verify triggers created
- [ ] Test rollback functionality

#### 1.2 Schema Validation
- [ ] Verify transport_requests table structure
- [ ] Verify transport_quotes table structure
- [ ] Verify transport_negotiations table structure
- [ ] Verify negotiation_messages table structure
- [ ] Verify driver_assignments table structure
- [ ] Verify deliveries table structure
- [ ] Verify delivery_tracking table structure
- [ ] Verify payment_allocations table structure
- [ ] Verify settlements table structure
- [ ] Verify disputes table structure
- [ ] Verify dispute_evidence table structure
- [ ] Verify notifications table structure
- [ ] Verify audit_logs table structure

#### 1.3 Foreign Key Constraints
- [ ] Test cascade delete on transport_requests
- [ ] Test cascade delete on negotiations
- [ ] Test cascade delete on deliveries
- [ ] Test cascade delete on disputes
- [ ] Test cascade delete on notifications

---

### 2. Transport Pricing Engine Tests

#### 2.1 Base Pricing
- [ ] Test base fee calculation
- [ ] Test per km rate calculation
- [ ] Test weight surcharge calculation
- [ ] Test volume surcharge calculation

#### 2.2 Multiplier Application
- [ ] Test urgency multiplier (STANDARD, URGENT, EXPEDITED)
- [ ] Test weather risk multiplier (LOW, MODERATE, HIGH, SEVERE)
- [ ] Test road accessibility multiplier
- [ ] Test driver availability multiplier
- [ ] Test peak demand multiplier
- [ ] Test combined multiplier calculation

#### 2.3 Vehicle Type Pricing
- [ ] Test motorcycle pricing
- [ ] Test car pricing
- [ ] Test van pricing
- [ ] Test truck pricing
- [ ] Test min/max fee constraints

#### 2.4 Distance Calculation
- [ ] Test Haversine formula accuracy
- [ ] Test distance estimation
- [ ] Test multi-stop distance calculation

#### 2.5 Rural Accessibility
- [ ] Test urban surcharge (0%)
- [ ] Test suburban surcharge (5%)
- [ ] Test rural surcharge (15%)
- [ ] Test remote surcharge (25%)

#### 2.6 Tax Calculation
- [ ] Test 15% VAT calculation
- [ ] Test subtotal + tax = total
- [ ] Test tax rounding

#### 2.7 Edge Cases
- [ ] Test zero distance
- [ ] Test extremely large distance
- [ ] Test zero weight
- [ ] Test extremely large weight
- [ ] Test invalid vehicle type

---

### 3. Business Rule Engine Tests

#### 3.1 Rule 1: Buyer Requested Delivery
- [ ] Test buyer requests platform delivery
- [ ] Verify transport fee payer = BUYER
- [ ] Verify driver assigned automatically
- [ ] Verify payment allocation created
- [ ] Verify notifications sent

#### 3.2 Rule 2: Farmer Requested Delivery
- [ ] Test farmer requests platform delivery
- [ ] Verify transport fee payer = FARMER
- [ ] Verify driver assigned automatically
- [ ] Verify payment allocation created
- [ ] Verify notifications sent

#### 3.3 Rule 3: Buyer Self Pickup
- [ ] Test buyer selects self pickup
- [ ] Verify transport fee = 0
- [ ] Verify pickup code generated
- [ ] Verify no driver assignment
- [ ] Verify notifications sent

#### 3.4 Rule 4: Farmer Self Delivery
- [ ] Test farmer selects self delivery
- [ ] Verify transport fee = 0
- [ ] Verify no driver assignment
- [ ] Verify notifications sent

#### 3.5 Rule 5: Negotiated Transport
- [ ] Test negotiation initiated
- [ ] Verify 72-hour expiry set
- [ ] Verify initial quote provided
- [ ] Verify notifications sent
- [ ] Test offer submission
- [ ] Test counter-offer
- [ ] Test acceptance by both parties
- [ ] Test payment allocation after agreement
- [ ] Test driver assignment after agreement

#### 3.6 Rule 6: Deferred Decision
- [ ] Test decision deferred
- [ ] Verify 48-hour deadline set
- [ ] Verify counterparty notified
- [ ] Test deadline expiry handling
- [ ] Test auto-assignment on expiry

#### 3.7 Split Payment
- [ ] Test split payment negotiation
- [ ] Verify split ratio validation (must sum to 1.0)
- [ ] Verify payment allocations for both parties
- [ ] Test 50/50 split
- [ ] Test 60/40 split
- [ ] Test custom split ratios

---

### 4. Payment Allocation Service Tests

#### 4.1 Allocation Creation
- [ ] Test goods payment allocation
- [ ] Test transport fee allocation
- [ ] Test platform fee allocation
- [ ] Test refund allocation

#### 4.2 Escrow Hold
- [ ] Test payment held in escrow
- [ ] Test held_at timestamp
- [ ] Test escrow integration

#### 4.3 Payment Release
- [ ] Test payment release to payee
- [ ] Test released_at timestamp
- [ ] Test wallet integration
- [ ] Test payment gateway integration

#### 4.4 Refund Processing
- [ ] Test refund to original payer
- [ ] Test refunded_at timestamp
- [ ] Test refund reason recording
- [ ] Test refund integration

#### 4.5 Transport Fee Allocations
- [ ] Test buyer pays full transport fee
- [ ] Test farmer pays full transport fee
- [ ] Test split payment allocations
- [ ] Verify allocation amounts match quote

#### 4.6 Order-Level Allocations
- [ ] Test all allocations for an order
- [ ] Test total payer amount calculation
- [ ] Test total payee amount calculation
- [ ] Verify allocation status tracking

---

### 5. Settlement Service Tests

#### 5.1 Farmer Settlement Calculation
- [ ] Test farmer payout calculation
- [ ] Verify goods amount included
- [ ] Verify platform fee deducted
- [ ] Verify transport fee deducted (if farmer paid)
- [ ] Verify net amount calculation

#### 5.2 Driver Settlement Calculation
- [ ] Test driver payout calculation
- [ ] Verify transport fee included
- [ ] Verify platform commission deducted
- [ ] Verify net amount calculation

#### 5.3 Buyer Refund Calculation
- [ ] Test buyer refund calculation
- [ ] Verify refund amount
- [ ] Verify refund reason recorded

#### 5.4 Settlement Processing
- [ ] Test settlement status transition (PENDING -> PROCESSING -> COMPLETED)
- [ ] Test payout method execution (wallet, bank transfer, mobile money)
- [ ] Test external transaction ID recording
- [ ] Test failure handling and retry logic

#### 5.5 Order Settlements
- [ ] Test all settlements for an order
- [ ] Test settlement after delivery confirmation
- [ ] Verify all parties paid correctly

#### 5.6 Retry Logic
- [ ] Test failed settlement retry
- [ ] Test exponential backoff calculation
- [ ] Test max retry limit
- [ ] Test next_retry_at scheduling

---

### 6. Transport Negotiation Service Tests

#### 6.1 Negotiation Creation
- [ ] Test negotiation initiation
- [ ] Verify 72-hour expiry
- [ ] Verify initial system message
- [ ] Verify notifications sent

#### 6.2 Message Sending
- [ ] Test text message
- [ ] Test offer message
- [ ] Test counter-offer message
- [ ] Test acceptance message
- [ ] Test rejection message
- [ ] Test system message

#### 6.3 Offer Submission
- [ ] Test buyer offer
- [ ] Test farmer offer
- [ ] Test split payment offer
- [ ] Validate split ratio sums to 1.0
- [ ] Test structured offer data

#### 6.4 Offer Acceptance
- [ ] Test single party acceptance
- [ ] Test both parties acceptance
- [ ] Verify agreement detection
- [ ] Verify payment allocation creation
- [ ] Verify driver assignment trigger

#### 6.5 Offer Rejection
- [ ] Test offer rejection
- [ ] Verify status update
- [ ] Verify counterparty notification
- [ ] Test continued negotiation

#### 6.6 Negotiation Cancellation
- [ ] Test negotiation cancellation
- [ ] Verify status update
- [ ] Test deferred decision trigger
- [ ] Verify notifications

#### 6.7 Expiry Handling
- [ ] Test 72-hour expiry
- [ ] Verify status update to EXPIRED
- [ ] Test admin escalation
- [ ] Test deferred decision fallback

#### 6.8 Admin Resolution
- [ ] Test admin escalation
- [ ] Test admin resolution
- [ ] Verify resolution applied
- [ ] Verify notifications

---

### 7. Driver Assignment Service Tests

#### 7.1 Driver Search
- [ ] Test available driver search
- [ ] Test capacity filtering
- [ ] Test vehicle type filtering
- [ ] Test location filtering
- [ ] Test distance calculation
- [ ] Test driver score calculation

#### 7.2 Auto Assignment
- [ ] Test automatic driver assignment
- [ ] Verify best driver selected
- [ ] Verify driver earnings calculation
- [ ] Verify platform commission calculation
- [ ] Verify assignment record created
- [ ] Verify driver notification

#### 7.3 Manual Assignment
- [ ] Test admin manual assignment
- [ ] Verify specific driver assigned
- [ ] Verify assignment_by = ADMIN
- [ ] Verify notifications

#### 7.4 Assignment Acceptance
- [ ] Test driver acceptance
- [ ] Verify within 5-minute window
- [ ] Test timeout rejection
- [ ] Verify status update to ACCEPTED
- [ ] Verify delivery creation

#### 7.5 Assignment Rejection
- [ ] Test driver rejection
- [ ] Verify rejection reason recorded
- [ ] Test reassignment to next driver
- [ ] Test max reassignment attempts
- [ ] Test admin escalation on max attempts

#### 7.6 Assignment Cancellation
- [ ] Test admin cancellation
- [ ] Verify status update to CANCELLED
- [ ] Test reassignment if needed

#### 7.7 Assignment Completion
- [ ] Test assignment completion
- [ ] Verify status update to COMPLETED
- [ ] Test driver payout trigger
- [ ] Verify driver stats update

#### 7.8 Response Timeout Handling
- [ ] Test 5-minute response timeout
- [ ] Verify auto-rejection
- [ ] Verify reassignment
- [ ] Test scheduled job execution

#### 7.9 Driver Earnings
- [ ] Test earnings calculation
- [ ] Test date range filtering
- [ ] Verify completed deliveries count
- [ ] Verify average per delivery

---

### 8. Delivery Tracking Service Tests

#### 8.1 Delivery Creation
- [ ] Test delivery record creation
- [ ] Verify initial status
- [ ] Test geofence creation
- [ ] Test initial ETA calculation

#### 8.2 Location Updates
- [ ] Test location update submission
- [ ] Verify tracking record created
- [ ] Verify delivery current location updated
- [ ] Test geofence checking
- [ ] Test status updates based on geofence

#### 8.3 Pickup Confirmation
- [ ] Test pickup code verification
- [ ] Test geofence verification
- [ ] Test photo upload
- [ ] Test signature upload
- [ ] Verify status update to PICKED_UP
- [ ] Verify delivery code generation
- [ ] Verify notifications

#### 8.4 Delivery Confirmation
- [ ] Test delivery code verification
- [ ] Test geofence verification
- [ ] Test proof of delivery upload
- [ ] Verify status update to DELIVERED
- [ ] Test settlement trigger
- [ ] Verify notifications

#### 8.5 ETA Calculation
- [ ] Test ETA based on current location
- [ ] Test ETA based on distance and speed
- [ ] Test ETA updates with location updates

#### 8.6 Route Deviation
- [ ] Test route deviation detection
- [ ] Test deviation threshold
- [ ] Test alert on significant deviation

#### 8.7 Tracking History
- [ ] Test tracking history retrieval
- [ ] Test date range filtering
- [ ] Verify chronological order

#### 8.8 Data Cleanup
- [ ] Test old tracking data cleanup
- [ ] Verify retention policy (30 days)
- [ ] Test scheduled job execution

---

### 9. API Endpoint Tests

#### 9.1 Transport Request Endpoints
- [ ] POST /transport/request
- [ ] GET /transport/status/{order_id}
- [ ] POST /transport/accept
- [ ] POST /transport/defer

#### 9.2 Pricing Endpoints
- [ ] POST /transport/calculate
- [ ] GET /transport/vehicles
- [ ] POST /transport/estimate-distance

#### 9.3 Negotiation Endpoints
- [ ] POST /transport/negotiations/start
- [ ] POST /transport/negotiations/offer
- [ ] POST /transport/negotiations/accept
- [ ] GET /transport/negotiations/{negotiation_id}

#### 9.4 Driver Assignment Endpoints
- [ ] POST /transport/drivers/assign
- [ ] GET /transport/drivers/available

#### 9.5 Delivery Endpoints
- [ ] POST /transport/delivery/confirm-pickup
- [ ] POST /transport/delivery/confirm-delivery
- [ ] POST /transport/delivery/dispute

#### 9.6 Tracking Endpoints
- [ ] POST /transport/tracking/location
- [ ] GET /transport/tracking/{delivery_id}

#### 9.7 Authentication & Authorization
- [ ] Test JWT token validation
- [ ] Test role-based access control
- [ ] Test buyer-only endpoints
- [ ] Test farmer-only endpoints
- [ ] Test admin-only endpoints
- [ ] Test driver-only endpoints

#### 9.8 Input Validation
- [ ] Test required field validation
- [ ] Test data type validation
- [ ] Test enum value validation
- [ ] Test range validation
- [ ] Test format validation

#### 9.9 Error Handling
- [ ] Test 400 Bad Request
- [ ] Test 403 Forbidden
- [ ] Test 404 Not Found
- [ ] Test 500 Internal Server Error
- [ ] Test error message format

---

### 10. Mobile App UI Tests

#### 10.1 Transport Selection Screen
- [ ] Test screen loads correctly
- [ ] Test transport mode selection
- [ ] Test address input fields
- [ ] Test vehicle type selection
- [ ] Test urgency selection
- [ ] Test quote calculation
- [ ] Test quote display
- [ ] Test confirm button
- [ ] Test cancel button

#### 10.2 Transport Negotiation Screen
- [ ] Test screen loads correctly
- [ ] Test message display
- [ ] Test message sending
- [ ] Test offer modal
- [ ] Test offer submission
- [ ] Test split payment input
- [ ] Test accept offer button
- [ ] Test reject offer button
- [ ] Test real-time updates

#### 10.3 Navigation Integration
- [ ] Test navigation from order details
- [ ] Test navigation from offer screen
- [ ] Test back button functionality
- [ ] Test deep linking

#### 10.4 State Management
- [ ] Test form state persistence
- [ ] Test loading states
- [ ] Test error states
- [ ] Test success states

---

### 11. Notification Tests

#### 11.1 Template Rendering
- [ ] Test all notification templates
- [ ] Test variable substitution
- [ ] Test template validation
- [ ] Test missing key handling

#### 11.2 Push Notifications
- [ ] Test push notification delivery
- [ ] Test push notification payload
- [ ] Test push notification click handling

#### 11.3 SMS Notifications
- [ ] Test SMS delivery
- [ ] Test SMS content formatting
- [ ] Test SMS character limits

#### 11.4 Email Notifications
- [ ] Test email delivery
- [ ] Test email subject
- [ ] Test email body formatting
- [ ] Test email HTML rendering

#### 11.5 In-App Notifications
- [ ] Test in-app notification display
- [ ] Test notification read status
- [ ] Test notification clearing

#### 11.6 Notification Channels
- [ ] Test channel selection
- [ ] Test multi-channel delivery
- [ ] Test channel fallback

---

### 12. Dispute Handling Tests

#### 12.1 Dispute Creation
- [ ] Test dispute submission
- [ ] Test dispute type selection
- [ ] Test evidence upload
- [ ] Test disputed amount validation
- [ ] Test priority calculation

#### 12.2 Evidence Management
- [ ] Test photo evidence upload
- [ ] Test document evidence upload
- [ ] Test evidence validation
- [ ] Test evidence display

#### 12.3 Dispute Escalation
- [ ] Test manual escalation
- [ ] Test automatic escalation
- [ ] Test escalation level tracking

#### 12.4 Dispute Resolution
- [ ] Test full refund resolution
- [ ] Test partial refund resolution
- [ ] Test no refund resolution
- [ ] Test driver penalty resolution
- [ ] Test split cost resolution

#### 12.5 Dispute Closure
- [ ] Test dispute withdrawal
- [ ] Test admin closure
- [ ] Test payment release on closure

#### 12.6 Deadline Handling
- [ ] Test response deadline expiry
- [ ] Test resolution deadline expiry
- [ ] Test auto-resolution on expiry

---

### 13. End-to-End Workflow Tests

#### 13.1 Buyer-Requested Delivery Workflow
1. Buyer creates order
2. Buyer requests platform delivery
3. System calculates transport fee
4. Buyer confirms transport fee
5. System assigns driver
6. Driver accepts assignment
7. Driver confirms pickup
8. Driver confirms delivery
9. Buyer confirms receipt
10. System releases payments
11. Driver receives payout
12. Farmer receives settlement

#### 13.2 Farmer-Requested Delivery Workflow
1. Farmer creates listing
2. Buyer accepts offer
3. Farmer requests platform delivery
4. System calculates transport fee
5. Farmer confirms transport fee
6. System assigns driver
7. Driver accepts assignment
8. Driver confirms pickup
9. Driver confirms delivery
10. Buyer confirms receipt
11. System releases payments
12. Driver receives payout
13. Farmer receives settlement (minus transport fee)

#### 13.3 Self Pickup Workflow
1. Buyer creates order
2. Buyer selects self pickup
3. System generates pickup code
4. Buyer receives pickup code
5. Buyer collects from farmer
6. Farmer verifies pickup code
7. Buyer confirms receipt
8. System releases payment to farmer

#### 13.4 Self Delivery Workflow
1. Farmer creates listing
2. Buyer accepts offer
3. Farmer selects self delivery
4. Farmer delivers to buyer
5. Buyer confirms receipt
6. System releases payment to farmer

#### 13.5 Negotiated Transport Workflow
1. Buyer creates order
2. Buyer selects negotiated transport
3. System initiates negotiation
4. Buyer submits initial offer
5. Farmer submits counter-offer
6. Buyer accepts counter-offer
7. System creates payment allocations
8. System assigns driver
9. Driver accepts assignment
10. Driver confirms pickup
11. Driver confirms delivery
12. Buyer confirms receipt
13. System releases payments according to split

#### 13.6 Deferred Decision Workflow
1. Buyer creates order
2. Buyer defers transport decision
3. System notifies farmer
4. Farmer selects platform delivery
5. System calculates transport fee
6. Farmer confirms transport fee
7. System assigns driver
8. Driver accepts assignment
9. Driver confirms pickup
10. Driver confirms delivery
11. Buyer confirms receipt
12. System releases payments

#### 13.7 Dispute Resolution Workflow
1. Delivery completed
2. Buyer raises dispute (damaged goods)
3. Buyer uploads evidence
4. System holds payment in escrow
5. Admin reviews dispute
6. Admin resolves with partial refund
7. System processes refund to buyer
8. System releases partial payment to farmer
9. Notifications sent to all parties

---

### 14. Performance Tests

#### 14.1 API Response Times
- [ ] Test pricing calculation < 500ms
- [ ] Test driver search < 1s
- [ ] Test location update < 200ms
- [ ] Test notification send < 1s

#### 14.2 Database Performance
- [ ] Test tracking data insertion rate
- [ ] Test large history query performance
- [ ] Test geospatial query performance
- [ ] Test index effectiveness

#### 14.3 Concurrent Operations
- [ ] Test multiple simultaneous transport requests
- [ ] Test concurrent location updates
- [ ] Test concurrent driver assignments
- [ ] Test concurrent negotiations

---

### 15. Security Tests

#### 15.1 Authentication
- [ ] Test unauthorized access blocked
- [ ] Test expired token rejected
- [ ] Test invalid token rejected

#### 15.2 Authorization
- [ ] Test role-based access control
- [ ] Test cross-user data access blocked
- [ ] Test admin-only endpoints protected

#### 15.3 Input Sanitization
- [ ] Test SQL injection prevention
- [ ] Test XSS prevention
- [ ] Test path traversal prevention

#### 15.4 Data Encryption
- [ ] Test sensitive data encryption at rest
- [ ] Test data encryption in transit (TLS)
- [ ] Test pickup/delivery code security

#### 15.5 Audit Logging
- [ ] Test all actions logged
- [ ] Test audit trail completeness
- [ ] Test audit log immutability

---

### 16. Integration Tests

#### 16.1 Payment Gateway Integration
- [ ] Test Stripe integration
- [ ] Test Paynow integration
- [ ] Test webhook handling
- [ ] Test refund processing

#### 16.2 Maps API Integration
- [ ] Test Google Maps Distance Matrix
- [ ] Test geocoding
- [ ] Test route calculation
- [ ] Test geofencing

#### 16.3 WebSocket Integration
- [ ] Test real-time location updates
- [ ] Test real-time negotiation messages
- [ ] Test connection handling
- [ ] Test reconnection logic

#### 16.4 Notification Service Integration
- [ ] Test push notification service
- [ ] Test SMS service
- [ ] Test email service
- [ ] Test in-app notification service

---

## Test Execution

### Test Environment
- **Development**: Local testing with mock data
- **Staging**: Pre-production with real payment gateways (test mode)
- **Production**: Smoke tests only

### Test Automation
- Unit tests: pytest
- API tests: pytest + requests
- Mobile UI tests: Detox / Appium
- Load tests: Locust

### Test Reporting
- Generate test reports after each run
- Track test coverage
- Log all failures with screenshots
- Notify team of critical failures

---

## Success Criteria

All tests must pass before production deployment:
- [ ] All unit tests pass (100%)
- [ ] All API tests pass (100%)
- [ ] All critical end-to-end workflows pass (100%)
- [ ] Code coverage > 80%
- [ ] Performance benchmarks met
- [ ] Security scan passes
- [ ] Manual QA sign-off

---

## Rollback Plan

If critical issues found during testing:
1. Rollback database migration
2. Revert API changes
3. Revert mobile app updates
4. Notify users of delay
5. Schedule fix deployment
