# Studio OS - Class Booking & Payment System Design

## 🎯 Overview

This document covers:
1. **Class Booking System** - Browse, book, manage dance classes
2. **Payment Integration** - Razorpay (India) + Stripe (International)

---

## 📅 Part 1: Class Booking System

### Booking Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLASS BOOKING JOURNEY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Step 1: Browse Classes                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  📅 Weekly Schedule View                                             │   │
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐     │   │
│  │  │   Mon   │   Tue   │   Wed   │   Thu   │   Fri   │   Sat   │     │   │
│  │  ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤     │   │
│  │  │ 9:00 AM │         │ 9:00 AM │         │ 9:00 AM │ 10:00AM │     │   │
│  │  │ Salsa   │         │ Salsa   │         │ Salsa   │ Hip-hop │     │   │
│  │  │ Beginner│         │ Beginner│         │ Beginner│ Kids    │     │   │
│  │  │ 5/12 🟢 │         │ 8/12 🟡 │         │ 12/12🔴│ 3/15 🟢 │     │   │
│  │  ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤     │   │
│  │  │ 6:00 PM │ 6:00 PM │ 6:00 PM │ 6:00 PM │ 6:00 PM │ 4:00 PM │     │   │
│  │  │ Contemp │ Salsa   │ Contemp │ Salsa   │ Contemp │ Wedding │     │   │
│  │  │ Inter.  │ Inter.  │ Inter.  │ Inter.  │ Inter.  │ Choreo  │     │   │
│  │  │ 10/15🟡 │ 7/15 🟢 │ 11/15🟡 │ 6/15 🟢 │ 14/15🔴│ 2/8  🟢 │     │   │
│  │  └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘     │   │
│  │                                                                     │   │
│  │  🟢 Available  🟡 Filling Up  🔴 Full (Waitlist)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  Step 2: Select Class                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🎭 Salsa - Beginner Level                                          │   │
│  │  ─────────────────────────────                                       │   │
│  │  📅 Monday, Jan 6, 2025 | 9:00 AM - 10:00 AM                        │   │
│  │  👨‍🏫 Instructor: Maria Rodriguez                                    │   │
│  │  📍 Studio Room A                                                    │   │
│  │  👥 5 spots left (7/12 booked)                                      │   │
│  │  💰 ₹500 per class | ₹4,000/month unlimited                         │   │
│  │                                                                      │   │
│  │  [Book Single Class - ₹500]  [Buy Monthly Pass - ₹4,000]            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  Step 3: Booking Confirmation                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✅ Booking Confirmed!                                               │   │
│  │  ──────────────────────                                              │   │
│  │  Booking ID: #BK-2025-0001                                          │   │
│  │                                                                      │   │
│  │  🎭 Salsa - Beginner Level                                          │   │
│  │  📅 Monday, Jan 6, 2025 | 9:00 AM - 10:00 AM                        │   │
│  │  👨‍🏫 Maria Rodriguez                                                 │   │
│  │  📍 Studio Room A                                                    │   │
│  │                                                                      │   │
│  │  💳 Payment: ₹500 (Paid via Razorpay)                               │   │
│  │                                                                      │   │
│  │  📱 Add to Calendar  |  📄 Download Receipt  |  ❌ Cancel Booking   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Booking Types

| Type | Description | Payment |
|------|-------------|---------|
| **Drop-in** | Single class | Pay per class |
| **Class Pack** | 5, 10, 20 classes | Prepaid, use anytime |
| **Monthly Pass** | Unlimited classes | Monthly subscription |
| **Private Session** | 1-on-1 with instructor | Premium pricing |
| **Trial Class** | First-time student | Free or discounted |

### Waitlist & Cancellation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WAITLIST MANAGEMENT                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  When class is FULL:                                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Class Full! Join Waitlist?                                  │   │
│  │  Current waitlist position: #3                               │   │
│  │  [Join Waitlist] [Get Notified for Similar Classes]         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  When spot opens:                                                    │
│  1. System notifies #1 on waitlist                                  │
│  2. They have 30 minutes to confirm                                 │
│  3. If no response, move to #2                                      │
│  4. Auto-book if user has "auto-book from waitlist" enabled         │
│                                                                      │
│  Cancellation Policy:                                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • 24+ hours before: Full refund / Credit back               │   │
│  │  • 12-24 hours: 50% refund                                   │   │
│  │  • < 12 hours: No refund (class pack credit retained)        │   │
│  │  • No-show: Marked, affects future booking priority          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 💳 Part 2: Payment Integration

### Payment Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PAYMENT FLOW                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                      CHECKOUT PAGE                                │      │
│  │  ────────────────────────────────────                             │      │
│  │                                                                   │      │
│  │  Order Summary:                                                   │      │
│  │  ┌─────────────────────────────────────────────────────────┐    │      │
│  │  │ 🎭 Monthly Unlimited Pass - January 2025                │    │      │
│  │  │    Includes: All group classes                          │    │      │
│  │  │    Validity: Jan 1 - Jan 31, 2025                       │    │      │
│  │  │                                           ₹4,000.00     │    │      │
│  │  ├─────────────────────────────────────────────────────────┤    │      │
│  │  │ Discount: NEW2025 (-10%)                   -₹400.00     │    │      │
│  │  ├─────────────────────────────────────────────────────────┤    │      │
│  │  │ GST (18%)                                   ₹648.00     │    │      │
│  │  ├─────────────────────────────────────────────────────────┤    │      │
│  │  │ TOTAL                                      ₹4,248.00    │    │      │
│  │  └─────────────────────────────────────────────────────────┘    │      │
│  │                                                                   │      │
│  │  Payment Method:                                                  │      │
│  │  ┌─────────────────────────────────────────────────────────┐    │      │
│  │  │ ○ UPI (GPay, PhonePe, Paytm)                            │    │      │
│  │  │ ○ Credit/Debit Card                                      │    │      │
│  │  │ ○ Net Banking                                            │    │      │
│  │  │ ○ Wallets (Paytm, Amazon Pay)                           │    │      │
│  │  │ ● Use Studio Wallet (Balance: ₹500)                     │    │      │
│  │  └─────────────────────────────────────────────────────────┘    │      │
│  │                                                                   │      │
│  │                    [PAY ₹3,748.00]                                │      │
│  │                                                                   │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                     RAZORPAY CHECKOUT                             │      │
│  │  ┌─────────────────────────────────────────────────────────┐    │      │
│  │  │  ┌─────────────────────────────────────────────────┐   │    │      │
│  │  │  │           🔒 Secure Payment                      │   │    │      │
│  │  │  │                                                  │   │    │      │
│  │  │  │  Dance Studio XYZ                               │   │    │      │
│  │  │  │  Amount: ₹3,748.00                              │   │    │      │
│  │  │  │                                                  │   │    │      │
│  │  │  │  [UPI] [Card] [NetBanking] [Wallet]            │   │    │      │
│  │  │  │                                                  │   │    │      │
│  │  │  │  Enter UPI ID: _________________                │   │    │      │
│  │  │  │                                                  │   │    │      │
│  │  │  │            [PAY NOW]                            │   │    │      │
│  │  │  └─────────────────────────────────────────────────┘   │    │      │
│  │  └─────────────────────────────────────────────────────────┘    │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                   WEBHOOK: payment.captured                       │      │
│  │  • Update payment status                                          │      │
│  │  • Activate pass/booking                                          │      │
│  │  • Send confirmation email                                        │      │
│  │  • Generate invoice                                               │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Supported Payment Providers

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PAYMENT PROVIDERS                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🇮🇳 RAZORPAY (Primary - India)                                     │
│  ──────────────────────────────                                      │
│  • UPI: GPay, PhonePe, Paytm, BHIM                                  │
│  • Cards: Visa, Mastercard, Rupay, Amex                             │
│  • Net Banking: All major banks                                      │
│  • Wallets: Paytm, Amazon Pay, Mobikwik                             │
│  • EMI: Credit card EMI, Cardless EMI                               │
│  • Pay Later: Simpl, LazyPay                                        │
│                                                                      │
│  Fees: 2% per transaction (can be passed to customer)               │
│  Settlement: T+2 days (next-day for premium)                        │
│                                                                      │
│  ────────────────────────────────────────────────                   │
│                                                                      │
│  🌍 STRIPE (International)                                          │
│  ─────────────────────────                                          │
│  • Cards: Visa, Mastercard, Amex, Discover                          │
│  • Digital Wallets: Apple Pay, Google Pay                           │
│  • Bank Debits: ACH (US), SEPA (EU)                                 │
│  • Buy Now Pay Later: Klarna, Afterpay                              │
│                                                                      │
│  Fees: 2.9% + $0.30 per transaction                                 │
│  Settlement: 2 business days                                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Pricing Models

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STUDIO PRICING MODELS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📦 CLASS PACKS                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Pack Name     | Classes | Price   | Per Class | Validity   │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  Starter       | 5       | ₹2,250  | ₹450      | 1 month    │   │
│  │  Regular       | 10      | ₹4,000  | ₹400      | 2 months   │   │
│  │  Pro           | 20      | ₹7,000  | ₹350      | 3 months   │   │
│  │  Unlimited     | ∞       | ₹5,000  | -         | 1 month    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  📅 SUBSCRIPTIONS                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Plan          | Price/Month | Billing   | Benefits         │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  Basic         | ₹3,500      | Monthly   | 8 classes/month  │   │
│  │  Standard      | ₹5,000      | Monthly   | Unlimited group  │   │
│  │  Premium       | ₹8,000      | Monthly   | Group + 2 pvt    │   │
│  │  Annual        | ₹50,000     | Yearly    | Best value!      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  🎫 SPECIAL OFFERINGS                                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Trial Class: ₹199 (First-timers only)                    │   │
│  │  • Private Session: ₹2,000/hour                             │   │
│  │  • Couple's Session: ₹3,000/hour                            │   │
│  │  • Group Booking (5+): 10% discount                         │   │
│  │  • Corporate Package: Custom pricing                        │   │
│  │  • Wedding Choreography: ₹15,000 package                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### Booking Models

```python
# Class Schedule & Sessions
class ClassSchedule(db.Model):
    """Recurring class schedule template"""
    id = db.Column(db.Integer, primary_key=True)
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    
    # Class details
    name = db.Column(db.String(100))  # "Salsa Beginner"
    description = db.Column(db.Text)
    class_type = db.Column(db.String(50))  # salsa, hip-hop, contemporary
    level = db.Column(db.String(20))  # beginner, intermediate, advanced
    
    # Schedule
    day_of_week = db.Column(db.Integer)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time)
    duration_minutes = db.Column(db.Integer, default=60)
    
    # Capacity
    max_capacity = db.Column(db.Integer, default=15)
    min_capacity = db.Column(db.Integer, default=3)
    
    # Instructor & Location
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id'))
    room = db.Column(db.String(50))
    
    # Pricing
    drop_in_price = db.Column(db.Numeric(10, 2))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    

class ClassSession(db.Model):
    """Individual class instance (generated from schedule)"""
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('class_schedule.id'))
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    
    # Date/Time
    date = db.Column(db.Date)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    # Capacity tracking
    booked_count = db.Column(db.Integer, default=0)
    waitlist_count = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.Enum('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'))
    
    # Substitute instructor (if different from schedule)
    substitute_instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id'))
    
    # Notes
    notes = db.Column(db.Text)


class Booking(db.Model):
    """Individual class booking"""
    id = db.Column(db.Integer, primary_key=True)
    booking_number = db.Column(db.String(20), unique=True)  # BK-2025-0001
    
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    session_id = db.Column(db.Integer, db.ForeignKey('class_session.id'))
    
    # Booking details
    status = db.Column(db.Enum('CONFIRMED', 'WAITLIST', 'CANCELLED', 'NO_SHOW', 'ATTENDED'))
    waitlist_position = db.Column(db.Integer, nullable=True)
    
    # Payment reference
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'))
    payment_method = db.Column(db.String(20))  # drop_in, class_pack, subscription
    
    # If using class pack
    class_pack_id = db.Column(db.Integer, db.ForeignKey('class_pack_purchase.id'))
    
    # Timestamps
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    checked_in_at = db.Column(db.DateTime, nullable=True)
    
    # Cancellation
    cancellation_reason = db.Column(db.String(255))
    refund_amount = db.Column(db.Numeric(10, 2))


class Waitlist(db.Model):
    """Waitlist for full classes"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('class_session.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    
    position = db.Column(db.Integer)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # 30 min to respond
    
    status = db.Column(db.Enum('WAITING', 'NOTIFIED', 'CONVERTED', 'EXPIRED', 'CANCELLED'))
    auto_book = db.Column(db.Boolean, default=False)  # Auto-book when spot opens
```

### Payment Models

```python
class Payment(db.Model):
    """Payment transaction record"""
    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(20), unique=True)  # PAY-2025-0001
    
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    
    # Amount
    amount = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(3), default='INR')
    
    # Tax
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    tax_rate = db.Column(db.Numeric(5, 2), default=18)  # GST
    
    # Discount
    discount_code = db.Column(db.String(20))
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Final amount
    total_amount = db.Column(db.Numeric(10, 2))
    
    # Payment provider
    provider = db.Column(db.Enum('RAZORPAY', 'STRIPE', 'WALLET', 'CASH', 'BANK_TRANSFER'))
    provider_payment_id = db.Column(db.String(100))  # razorpay_payment_id
    provider_order_id = db.Column(db.String(100))    # razorpay_order_id
    
    # Payment method details
    payment_method = db.Column(db.String(20))  # upi, card, netbanking, wallet
    payment_method_details = db.Column(db.JSON)  # {"bank": "HDFC", "last4": "1234"}
    
    # Status
    status = db.Column(db.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED'))
    
    # What was purchased
    purchase_type = db.Column(db.Enum('DROP_IN', 'CLASS_PACK', 'SUBSCRIPTION', 'PRIVATE_SESSION', 'MERCHANDISE'))
    purchase_id = db.Column(db.Integer)  # Reference to the purchased item
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Invoice
    invoice_number = db.Column(db.String(20))
    invoice_url = db.Column(db.String(255))


class ClassPack(db.Model):
    """Class pack product definition"""
    id = db.Column(db.Integer, primary_key=True)
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    
    name = db.Column(db.String(100))  # "10 Class Pack"
    description = db.Column(db.Text)
    
    # Pack details
    class_count = db.Column(db.Integer)  # Number of classes
    price = db.Column(db.Numeric(10, 2))
    validity_days = db.Column(db.Integer)  # Valid for X days after purchase
    
    # Restrictions
    class_types = db.Column(db.JSON)  # ["salsa", "hip-hop"] or null for all
    
    is_active = db.Column(db.Boolean, default=True)


class ClassPackPurchase(db.Model):
    """Purchased class pack instance"""
    id = db.Column(db.Integer, primary_key=True)
    
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    class_pack_id = db.Column(db.Integer, db.ForeignKey('class_pack.id'))
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'))
    
    # Usage tracking
    classes_total = db.Column(db.Integer)
    classes_used = db.Column(db.Integer, default=0)
    classes_remaining = db.Column(db.Integer)
    
    # Validity
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    status = db.Column(db.Enum('ACTIVE', 'EXHAUSTED', 'EXPIRED', 'REFUNDED'))


class Subscription(db.Model):
    """Recurring subscription"""
    id = db.Column(db.Integer, primary_key=True)
    
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    
    # Plan details
    plan_name = db.Column(db.String(100))
    plan_type = db.Column(db.Enum('BASIC', 'STANDARD', 'PREMIUM', 'ANNUAL'))
    
    # Pricing
    amount = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(3), default='INR')
    billing_cycle = db.Column(db.Enum('MONTHLY', 'QUARTERLY', 'YEARLY'))
    
    # Provider subscription ID
    provider = db.Column(db.Enum('RAZORPAY', 'STRIPE'))
    provider_subscription_id = db.Column(db.String(100))
    
    # Dates
    started_at = db.Column(db.DateTime)
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    # Status
    status = db.Column(db.Enum('ACTIVE', 'PAUSED', 'CANCELLED', 'PAST_DUE', 'EXPIRED'))
    
    # Auto-renewal
    auto_renew = db.Column(db.Boolean, default=True)


class Wallet(db.Model):
    """Studio wallet for credits/refunds"""
    id = db.Column(db.Integer, primary_key=True)
    
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), unique=True)
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    
    balance = db.Column(db.Numeric(10, 2), default=0)
    currency = db.Column(db.String(3), default='INR')


class WalletTransaction(db.Model):
    """Wallet credit/debit history"""
    id = db.Column(db.Integer, primary_key=True)
    
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'))
    
    type = db.Column(db.Enum('CREDIT', 'DEBIT'))
    amount = db.Column(db.Numeric(10, 2))
    balance_after = db.Column(db.Numeric(10, 2))
    
    description = db.Column(db.String(255))  # "Refund for cancelled class"
    reference_type = db.Column(db.String(50))  # "booking", "payment", "manual"
    reference_id = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## 🔌 API Endpoints

### Booking Endpoints

```
GET    /api/classes                    # List all class schedules
GET    /api/classes/schedule           # Get weekly schedule view
GET    /api/classes/:id                # Get class details
GET    /api/sessions                   # List upcoming sessions
GET    /api/sessions/:id               # Get session details with availability

POST   /api/bookings                   # Create new booking
GET    /api/bookings                   # List user's bookings
GET    /api/bookings/:id               # Get booking details
PUT    /api/bookings/:id/cancel        # Cancel booking
PUT    /api/bookings/:id/checkin       # Check-in for class

POST   /api/waitlist                   # Join waitlist
DELETE /api/waitlist/:id               # Leave waitlist
GET    /api/waitlist/position          # Check waitlist position
```

### Payment Endpoints

```
POST   /api/payments/create-order      # Create Razorpay order
POST   /api/payments/verify            # Verify payment signature
POST   /api/payments/webhook           # Razorpay webhook
GET    /api/payments                   # List payment history
GET    /api/payments/:id               # Get payment details
GET    /api/payments/:id/invoice       # Download invoice

GET    /api/class-packs                # List available class packs
POST   /api/class-packs/purchase       # Purchase a class pack
GET    /api/class-packs/my-packs       # List user's class packs

GET    /api/subscriptions/plans        # List subscription plans
POST   /api/subscriptions              # Create subscription
GET    /api/subscriptions/:id          # Get subscription details
PUT    /api/subscriptions/:id/cancel   # Cancel subscription
PUT    /api/subscriptions/:id/pause    # Pause subscription

GET    /api/wallet                     # Get wallet balance
GET    /api/wallet/transactions        # List wallet transactions
POST   /api/wallet/add-funds           # Add funds to wallet
```

---

## 🔐 Razorpay Integration

### Setup Requirements

```bash
# Environment variables
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxx
```

### Payment Flow Code

```python
# backend/app/services/payment_service.py

import razorpay
from app import db
from app.models import Payment, Booking

class RazorpayService:
    def __init__(self):
        self.client = razorpay.Client(
            auth=(
                current_app.config['RAZORPAY_KEY_ID'],
                current_app.config['RAZORPAY_KEY_SECRET']
            )
        )
    
    def create_order(self, amount: int, currency: str = 'INR', receipt: str = None, notes: dict = None):
        """Create a Razorpay order"""
        order_data = {
            'amount': amount * 100,  # Razorpay expects amount in paise
            'currency': currency,
            'receipt': receipt,
            'notes': notes or {}
        }
        
        order = self.client.order.create(data=order_data)
        return order
    
    def verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str):
        """Verify payment signature"""
        try:
            self.client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
    
    def capture_payment(self, payment_id: str, amount: int):
        """Capture an authorized payment"""
        return self.client.payment.capture(payment_id, amount * 100)
    
    def refund_payment(self, payment_id: str, amount: int = None):
        """Refund a payment (full or partial)"""
        refund_data = {}
        if amount:
            refund_data['amount'] = amount * 100
        
        return self.client.payment.refund(payment_id, refund_data)
    
    def create_subscription(self, plan_id: str, customer_id: str, total_count: int = None):
        """Create a recurring subscription"""
        subscription_data = {
            'plan_id': plan_id,
            'customer_id': customer_id,
            'total_count': total_count or 12,  # 12 months by default
            'customer_notify': 1
        }
        
        return self.client.subscription.create(data=subscription_data)
```

### Webhook Handler

```python
# backend/app/routes/payments.py

@payments_bp.route('/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    """Handle Razorpay webhooks"""
    payload = request.get_data()
    signature = request.headers.get('X-Razorpay-Signature')
    
    # Verify webhook signature
    webhook_secret = current_app.config['RAZORPAY_WEBHOOK_SECRET']
    
    try:
        razorpay_client.utility.verify_webhook_signature(
            payload.decode('utf-8'),
            signature,
            webhook_secret
        )
    except razorpay.errors.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    event = request.json
    event_type = event['event']
    
    if event_type == 'payment.captured':
        handle_payment_captured(event['payload']['payment']['entity'])
    
    elif event_type == 'payment.failed':
        handle_payment_failed(event['payload']['payment']['entity'])
    
    elif event_type == 'refund.created':
        handle_refund_created(event['payload']['refund']['entity'])
    
    elif event_type == 'subscription.charged':
        handle_subscription_charged(event['payload']['subscription']['entity'])
    
    elif event_type == 'subscription.cancelled':
        handle_subscription_cancelled(event['payload']['subscription']['entity'])
    
    return jsonify({'status': 'ok'})


def handle_payment_captured(payment_data):
    """Process successful payment"""
    payment = Payment.query.filter_by(
        provider_order_id=payment_data['order_id']
    ).first()
    
    if payment:
        payment.status = 'COMPLETED'
        payment.provider_payment_id = payment_data['id']
        payment.payment_method = payment_data['method']
        payment.completed_at = datetime.utcnow()
        
        # Activate the booking/pack/subscription
        if payment.purchase_type == 'DROP_IN':
            booking = Booking.query.get(payment.purchase_id)
            booking.status = 'CONFIRMED'
        
        elif payment.purchase_type == 'CLASS_PACK':
            pack_purchase = ClassPackPurchase.query.get(payment.purchase_id)
            pack_purchase.status = 'ACTIVE'
        
        # Send confirmation email
        send_payment_confirmation.delay(payment.id)
        
        db.session.commit()
```

---

## 📱 Frontend Components

### Key Components Needed

```
frontend/src/pages/
├── BookingPage.tsx          # Browse & book classes
├── SchedulePage.tsx         # Weekly schedule view
├── MyBookingsPage.tsx       # User's bookings
├── CheckoutPage.tsx         # Payment checkout
├── PackagesPage.tsx         # View & buy class packs
├── SubscriptionPage.tsx     # Manage subscription

frontend/src/components/
├── booking/
│   ├── ClassCard.tsx        # Class preview card
│   ├── ScheduleGrid.tsx     # Weekly schedule grid
│   ├── SessionDetail.tsx    # Session details modal
│   ├── BookingForm.tsx      # Booking form
│   ├── WaitlistButton.tsx   # Join waitlist
│   └── BookingConfirmation.tsx
├── payment/
│   ├── CheckoutForm.tsx     # Checkout summary
│   ├── RazorpayButton.tsx   # Pay with Razorpay
│   ├── PackageCard.tsx      # Class pack card
│   ├── SubscriptionCard.tsx # Subscription plan
│   ├── WalletBalance.tsx    # Wallet display
│   └── PaymentHistory.tsx   # Transaction list
```

---

## 🚀 Implementation Priority

### Phase 1: Core Booking (Week 1)
- [ ] Database models for booking
- [ ] Class schedule CRUD
- [ ] Session generation
- [ ] Basic booking flow

### Phase 2: Payment Integration (Week 2)
- [ ] Razorpay integration
- [ ] Checkout flow
- [ ] Webhook handling
- [ ] Invoice generation

### Phase 3: Advanced Features (Week 3)
- [ ] Class packs
- [ ] Subscriptions
- [ ] Wallet system
- [ ] Waitlist management

### Phase 4: Polish (Week 4)
- [ ] Email notifications
- [ ] Calendar integration
- [ ] Cancellation/refund flow
- [ ] Analytics & reporting
