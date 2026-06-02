import os
from datetime import datetime
from app.database import SessionLocal
from app.models import User, UserRole
from app.auth import hash_password

db = SessionLocal()

users = [
    # Admin
    {
        "user_id":  "ADMIN-001",
        "name":     "Admin",
        "email":    "admin@evsu.edu.ph",
        "password": "Admin@1234",
        "role":     UserRole.admin,
    },
    # Students
    {
        "user_id":  "2024-00001",
        "name":     "Juan dela Cruz",
        "email":    "juandelacruz@evsu.edu.ph",
        "password": "Student@1234",
        "role":     UserRole.student,
    },
    {
        "user_id":  "2024-00002",
        "name":     "Maria Santos",
        "email":    "mariasantos@evsu.edu.ph",
        "password": "Student@1234",
        "role":     UserRole.student,
    },
    {
        "user_id":  "2022-3121",
        "name":     "Dave Bangcoyo",
        "email":    "jhinbangcoyo@gmail.com",
        "password": "dave123",
        "role":     UserRole.student,
    },
    {
        "user_id":  "2024-00003",
        "name":     "Carlo Reyes",
        "email":    "carloreyes@evsu.edu.ph",
        "password": "Student@1234",
        "role":     UserRole.student,
    },
    {
        "user_id":  "2024-00004",
        "name":     "Ana Flores",
        "email":    "anaflores@evsu.edu.ph",
        "password": "Student@1234",
        "role":     UserRole.student,
    },
    {
        "user_id":  "2024-00005",
        "name":     "Mark Villanueva",
        "email":    "markvillanueva@evsu.edu.ph",
        "password": "Student@1234",
        "role":     UserRole.student,
    },
    {
        "user_id":  "2021-30875",
        "name":     "Anthony Domasig",
        "email":    "anthony.domasig@evsu.edu.ph",
        "password": "Student@1234",
        "role":     UserRole.student,
    },
]

print("Starting database seeding...")

for u in users:
    existing = db.query(User).filter(User.email == u["email"]).first()
    if not existing:
        user = User(
            user_id    = u["user_id"],
            name       = u["name"],
            email      = u["email"],
            password   = hash_password(u["password"]),
            role       = u["role"],
            is_active  = True,  # Giusab gikan sa 1 ngadto sa True para sa PostgreSQL Boolean field
            created_at = datetime.utcnow(),
            updated_at = datetime.utcnow()
        )
        db.add(user)
        print(f"Created: {u['email']} / {u['password']}")
    else:
        print(f"Already exists: {u['email']}")

try:
    db.commit()
    print("\nDatabase seeding completed successfully. Done.")
except Exception as e:
    db.rollback()
    print(f"\nError during seeding: {e}")
finally:
    db.close()
