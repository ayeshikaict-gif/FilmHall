# Ceylon Cineplex - Premium Sri Lankan Cinema Booking & Management System

> **"Your Movie. Your Seat. Your Experience."**

**Ceylon Cineplex** is a fully functional, production-style full-stack cinema ticket booking and management platform built specifically with a Sri Lankan context. It delivers a premium visual experience, normalized relational database design, transactional seat locking, digital PDF ticket generation with QR codes, real-time Cashier POS synchronization, and dynamic English & Sinhala bilingual interface support.

---

## 🌟 Key Features

### 🎬 Customer Facing Web App
- **Premium Hero Section & Movie Catalog**: Highlights Sinhala films (*Ginnen Upan Seethala*, *Aloko Udapadi*, *Machan*, *Super Six*, *Komaali Kings*, *Goal*, *Flying Fish*, *Praana*, *Gaadi*) alongside global blockbusters (*Dune: Part Two*, *Oppenheimer*, *Spider-Man*, *Avatar*).
- **Search & Filters**: Filter movies by title, genre, language (Sinhala, English, Tamil), status (*NOW SHOWING*, *COMING SOON*), or sorting.
- **Movie Details & Trailer Embeds**: Detailed metadata, cast, director, age ratings, YouTube trailer modals, date pickers, and hall-specific showtimes.
- **Interactive Seat Map**: Real-time seat grid featuring Standard (850 LKR), Premium (1,200 LKR), and VIP (1,800 LKR) tiers.
- **Anti-Double Booking & 5-Minute Seat Hold**: Server-side transactional seat locking with a 5-minute countdown reservation timer.
- **Checkout & Mock Payment**: Simulates Credit/Debit Card, Online Banking, and Pay at Counter payment methods with LKR formatting.
- **E-Ticket & PDF Generation**: Generates official branded PDF tickets containing booking references, seat assignments, QR code verification, and cinema terms using `reportlab`.
- **Customer Dashboard**: Displays past and upcoming bookings with instant PDF ticket downloads.

### 🎟️ Cashier POS Counter System
- **Real-time Live Seat Sync**: Synchronizes seat maps every 3 seconds. When a customer books seat `F5` online, the cashier POS counter immediately updates `F5` to `BOOKED`. If the cashier sells `F6` over the counter, online users see `F6` as unavailable.
- **Walk-in Booking Desk**: Fast cashier checkout flow for cash/card counter sales.
- **Ticket Printing & Lookup**: Instant printing and booking search by reference ID, phone number, or customer name.

### 🛠️ Executive Admin Management System
- **Real-time Analytics Dashboard**: Tracks today's revenue, bookings, registered customers, active movies, ticket sales source breakdown (Online vs Cashier), and top popular movies.
- **Movie Management**: Create, edit, archive (soft delete), and update statuses (*NOW SHOWING*, *COMING SOON*, *ENDED*).
- **Showtime Scheduling with Overlap Prevention**: Prevents double-booking halls at overlapping time intervals.
- **Halls & Seat Pricing Tiers**: Adjust dynamic base prices for Standard, Premium, and VIP seat tiers.
- **Master Booking Register**: Full inspection and cancellation controls.
- **User Roles & Permissions**: Manage Customer, Cashier, and Admin accounts.
- **Financial Reports**: Daily revenue logs and lifetime movie box office performance.
- **Audit Logs**: Tracks administrative actions, price changes, and security events.

### 🌐 Sinhala & English Bilingual Interface
- Header language switcher (**EN | සිංහල**) with persistent language state.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.14+ / Flask Framework / RESTful endpoints / Flask Session Authentication & Role Authorization
- **Database**: Dual Architecture — MySQL 8.0+ (`database/schema.sql` & `database/seed.sql`) and Zero-Config SQLite fallback (`ceylon_cineplex.db`)
- **Frontend**: HTML5, Vanilla CSS3 (Custom Ceylon Cineplex Design System: Charcoal `#0B0B0F`, Gold `#D4AF6A`, Dark Burgundy `#5B1018`), Vanilla JavaScript
- **PDF Engine**: Python `reportlab` & `qrcode` libraries

---

## 🔑 Demo Accounts

| Role | Email Address | Password | Privileges |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@ceyloncineplex.lk` | `Admin@123` | Full access to Admin Dashboard, Movies, Showtimes, Halls, Pricing, Audit Logs |
| **Cashier** | `cashier@ceyloncineplex.lk` | `Cashier@123` | Access to POS Counter Desk, Walk-in Cash Bookings, Live Seat Grid |
| **Customer** | `kasun.perera@gmail.com` | `Customer@123` | Public browsing, Seat selection, Mock Payment, PDF E-Tickets |

---

## 🚀 Quick Setup & Execution

### 1. Prerequisites
- Python 3.10+ installed
- MySQL (Optional if using default zero-config SQLite mode)

### 2. Setup Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Option A: Zero-Config SQLite (Default - Recommended for Instant Run)
The application automatically creates and seeds `ceylon_cineplex.db` on first startup!

#### Option B: MySQL Database
1. Create database in MySQL:
   ```sql
   CREATE DATABASE ceylon_cineplex_db;
   ```
2. Import Schema & Seed Data:
   ```bash
   mysql -u root -p ceylon_cineplex_db < database/schema.sql
   mysql -u root -p ceylon_cineplex_db < database/seed.sql
   ```
3. Update `.env` file:
   ```env
   DB_TYPE=mysql
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=yourpassword
   MYSQL_DB=ceylon_cineplex_db
   ```

### 5. Run Application
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 📁 Project Directory Structure

```
cinema_booking_system/
├── app.py                      # Flask Application Entry Point
├── config.py                   # Global System Configuration
├── requirements.txt            # Python Package Dependencies
├── .env.example                # Sample Environment Variables
├── database/
│   ├── db.py                   # Unified Dual DB Connector (SQLite/MySQL)
│   ├── schema.sql              # Normalized MySQL Relational Schema
│   └── seed.sql                # Production Seed Data
├── models/
│   ├── user.py                 # User & Role Model
│   ├── movie.py                # Movie Model & Queries
│   ├── hall.py                 # Hall & Seat Layout Model
│   ├── showtime.py             # Showtime Overlap Checker
│   ├── booking.py              # Booking & Seat Map State Engine
│   ├── payment.py              # Payment Record Model
│   └── audit.py                # Audit Logging Model
├── services/
│   ├── booking_service.py      # Core Booking & 5-Min Seat Hold Engine
│   └── ticket_service.py       # PDF Ticket & QR Code Generator
├── routes/
│   ├── auth.py                 # Login, Register, Logout
│   ├── customer.py             # Public Web Pages & Booking Flow
│   ├── cashier.py              # POS Walk-In Counter Desk
│   ├── admin.py                # Admin Dashboard & Management
│   └── api.py                  # REST JSON Endpoints
├── templates/                  # Jinja2 Modular HTML Templates
└── static/                     # CSS Stylesheets, JS Scripts & Assets
```

---

## 📌 Verification & Tested Scenarios

1. **Customer Workflow**: User registers -> Logs in -> Chooses *Ginnen Upan Seethala* -> Selects showtime -> Selects VIP seats -> Pays via Credit Card sandbox -> Receives E-ticket & downloads PDF.
2. **Cashier POS & Real-Time Sync**: Cashier logs into `/cashier` -> Opens same showtime -> Customer's selected seats immediately show as `BOOKED` -> Cashier books adjacent seat -> Seat updates for online customers.
3. **Showtime Overlap Prevention**: Admin attempts to add overlapping showtime in `Hall 01` -> System rejects request with error prompt.
