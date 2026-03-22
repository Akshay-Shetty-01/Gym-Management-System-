# 🏋️ IronFit Gym API

A FastAPI-based backend system for managing gym memberships, plans, and class bookings.

---

## 🚀 Features

### 🧾 Plans
- View all plans
- Get plan details
- Create, update, delete plans
- Filter, search, sort, and paginate plans

### 👥 Memberships
- Enroll members into plans
- Automatic fee calculation with discounts
- Freeze and reactivate memberships
- Search, sort, and paginate memberships

### 📅 Class Bookings
- Book classes (only if eligible)
- View bookings
- Cancel bookings

---

## 🧠 Business Logic

- 🎯 Discounts:
  - 10% for ≥ 6 months
  - 20% for ≥ 12 months
- 🎟 Referral: Extra 5% off
- 💳 EMI: ₹200 additional fee

---

## 🛠 Tech Stack

- FastAPI
- Pydantic
- Uvicorn

---

## ▶️ How to Run

### 1. Install dependencies

pip install -r requirements.txt
### 2. Run server
uvicorn main:app --reload
### 3. Open API Docs
Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

### 📡 API Endpoints
#### Plans
    GET /plans
    GET /plans/{id}
    POST /plans
    PUT /plans/{id}
    DELETE /plans/{id}
#### Memberships
    POST /memberships
    GET /memberships
    PUT /memberships/{id}/freeze
    PUT /memberships/{id}/reactivate
#### Classes
    POST /classes/book
    GET /classes/bookings
    DELETE /classes/cancel/{id}
### ⚠️ Limitations
Uses in-memory storage (data resets on restart)
No authentication system
No database integration

### 🔮 Future Improvements
Add database (PostgreSQL / SQLite)
Implement authentication (JWT)
Add user roles (Admin / Member)
Membership expiry tracking
Payment integration
