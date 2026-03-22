from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

# -------------------- DATA --------------------

plans = [
    {"id": 1, "name": "Basic", "duration_months": 1, "price": 1000, "includes_classes": False, "includes_trainer": False},
    {"id": 2, "name": "Standard", "duration_months": 3, "price": 2500, "includes_classes": True, "includes_trainer": False},
    {"id": 3, "name": "Premium", "duration_months": 6, "price": 4500, "includes_classes": True, "includes_trainer": True},
    {"id": 4, "name": "Elite", "duration_months": 12, "price": 8000, "includes_classes": True, "includes_trainer": True},
    {"id": 5, "name": "Starter", "duration_months": 1, "price": 800, "includes_classes": False, "includes_trainer": False}
]

memberships = []
membership_counter = 1

class_bookings = []
class_counter = 1

# -------------------- MODELS --------------------

class EnrollRequest(BaseModel):
    member_name: str = Field(..., min_length=2)
    plan_id: int = Field(..., gt=0)
    phone: str = Field(..., min_length=10)
    start_month: str = Field(..., min_length=3)
    payment_mode: str = "cash"
    referral_code: str = ""

class NewPlan(BaseModel):
    name: str = Field(..., min_length=2)
    duration_months: int = Field(..., gt=0)
    price: int = Field(..., gt=0)
    includes_classes: bool = False
    includes_trainer: bool = False

# -------------------- HELPERS --------------------

def find_plan(plan_id: int):
    return next((p for p in plans if p["id"] == plan_id), None)

def calculate_membership_fee(base_price, duration, payment_mode, referral_code=""):
    discount = 0
    breakdown = []

    if duration >= 12:
        discount += 0.20
        breakdown.append("20% long-term discount")
    elif duration >= 6:
        discount += 0.10
        breakdown.append("10% mid-term discount")

    price = base_price * (1 - discount)

    if referral_code:
        price *= 0.95
        breakdown.append("5% referral discount")

    fee = 200 if payment_mode.lower() == "emi" else 0
    if fee:
        breakdown.append("₹200 EMI fee")

    return round(price + fee, 2), breakdown

# -------------------- BASIC --------------------

@app.get("/")
def home():
    return {"message": "Welcome to IronFit Gym"}

@app.get("/plans")
def get_plans():
    prices = [p["price"] for p in plans]
    return {"plans": plans, "total": len(plans), "min_price": min(prices), "max_price": max(prices)}

@app.get("/plans/summary")
def summary():
    cheapest = min(plans, key=lambda x: x["price"])
    expensive = max(plans, key=lambda x: x["price"])

    return {
        "total_plans": len(plans),
        "includes_classes": sum(p["includes_classes"] for p in plans),
        "includes_trainer": sum(p["includes_trainer"] for p in plans),
        "cheapest": cheapest,
        "most_expensive": expensive
    }

@app.get("/plans/{plan_id}")
def get_plan(plan_id: int):
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    return plan

@app.get("/memberships")
def get_memberships():
    return {"memberships": memberships, "total": len(memberships)}

# -------------------- MEMBERSHIPS --------------------

@app.post("/memberships")
def create_membership(data: EnrollRequest):
    global membership_counter

    plan = find_plan(data.plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    total_fee, breakdown = calculate_membership_fee(
        plan["price"],
        plan["duration_months"],
        data.payment_mode,
        data.referral_code
    )

    membership = {
        "membership_id": membership_counter,
        "member_name": data.member_name,
        "plan_name": plan["name"],
        "duration_months": plan["duration_months"],
        "monthly_cost": round(total_fee / plan["duration_months"], 2),
        "total_fee": total_fee,
        "discounts": breakdown,
        "status": "active"
    }

    memberships.append(membership)
    membership_counter += 1
    return membership

@app.put("/memberships/{membership_id}/freeze")
def freeze(membership_id: int):
    for m in memberships:
        if m["membership_id"] == membership_id:
            m["status"] = "frozen"
            return m
    raise HTTPException(404, "Not found")

@app.put("/memberships/{membership_id}/reactivate")
def reactivate(membership_id: int):
    for m in memberships:
        if m["membership_id"] == membership_id:
            m["status"] = "active"
            return m
    raise HTTPException(404, "Not found")

# -------------------- PLAN CRUD --------------------

@app.post("/plans", status_code=201)
def create_plan(plan: NewPlan):
    if any(p["name"].lower() == plan.name.lower() for p in plans):
        raise HTTPException(400, "Duplicate plan")

    new = {**plan.dict(), "id": len(plans) + 1}
    plans.append(new)
    return new

@app.put("/plans/{plan_id}")
def update_plan(plan_id: int, price: int = None, includes_classes: bool = None, includes_trainer: bool = None):
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Not found")

    if price is not None:
        plan["price"] = price
    if includes_classes is not None:
        plan["includes_classes"] = includes_classes
    if includes_trainer is not None:
        plan["includes_trainer"] = includes_trainer

    return plan

@app.delete("/plans/{plan_id}")
def delete_plan(plan_id: int):
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Not found")

    if any(m["plan_name"] == plan["name"] and m["status"] == "active" for m in memberships):
        raise HTTPException(400, "Active memberships exist")

    plans.remove(plan)
    return {"message": "Deleted"}

# -------------------- CLASS BOOKINGS --------------------

@app.post("/classes/book")
def book_class(member_name: str, class_name: str, class_date: str):
    global class_counter

    valid = False
    for m in memberships:
        if m["member_name"].lower() == member_name.lower() and m["status"] == "active":
            plan = next(p for p in plans if p["name"] == m["plan_name"])
            if plan["includes_classes"]:
                valid = True

    if not valid:
        raise HTTPException(400, "Not eligible")

    booking = {"booking_id": class_counter, "member_name": member_name, "class_name": class_name, "class_date": class_date}
    class_bookings.append(booking)
    class_counter += 1
    return booking

@app.get("/classes/bookings")
def get_bookings():
    return {"bookings": class_bookings}

@app.delete("/classes/cancel/{booking_id}")
def cancel_booking(booking_id: int):
    for b in class_bookings:
        if b["booking_id"] == booking_id:
            class_bookings.remove(b)
            return {"message": "Cancelled"}
    raise HTTPException(404, "Not found")

# -------------------- SEARCH / FILTER / SORT --------------------

@app.get("/plans/filter")
def filter_plans(max_price: int = None, max_duration: int = None, includes_classes: bool = None, includes_trainer: bool = None):
    result = plans
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    if max_duration is not None:
        result = [p for p in result if p["duration_months"] <= max_duration]
    if includes_classes is not None:
        result = [p for p in result if p["includes_classes"] == includes_classes]
    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer]

    return {"plans": result}

@app.get("/plans/search")
def search_plans(keyword: str):
    k = keyword.lower()
    result = [
        p for p in plans
        if k in p["name"].lower()
        or (k == "classes" and p["includes_classes"])
        or (k == "trainer" and p["includes_trainer"])
    ]
    return {"matches": result, "total": len(result)}

@app.get("/plans/sort")
def sort_plans(sort_by: str = "price"):
    return sorted(plans, key=lambda x: x[sort_by])

@app.get("/plans/page")
def paginate(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    return plans[start:start + limit]

# -------------------- MEMBERSHIP ADVANCED --------------------

@app.get("/memberships/search")
def search_memberships(name: str):
    return [m for m in memberships if name.lower() in m["member_name"].lower()]

@app.get("/memberships/sort")
def sort_memberships(sort_by: str = "total_fee"):
    return sorted(memberships, key=lambda x: x[sort_by])

@app.get("/memberships/page")
def paginate_members(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    return memberships[start:start + limit]

# -------------------- FINAL COMBINED --------------------

@app.get("/plans/browse")
def browse(keyword: str = None, includes_classes: bool = None, includes_trainer: bool = None,
           sort_by: str = "price", order: str = "asc", page: int = 1, limit: int = 2):

    result = plans

    if keyword:
        k = keyword.lower()
        result = [
            p for p in result
            if k in p["name"].lower()
            or (k == "classes" and p["includes_classes"])
            or (k == "trainer" and p["includes_trainer"])
        ]

    if includes_classes is not None:
        result = [p for p in result if p["includes_classes"] == includes_classes]

    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer]

    reverse = (order == "desc")
    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    start = (page - 1) * limit
    return result[start:start + limit]