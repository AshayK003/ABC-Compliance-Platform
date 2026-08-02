#!/usr/bin/env python3
"""
Seed database with real AWBI-recognized ABC centers from the official PDF
(https://awbi.gov.in/uploads/documents/176243100597List%20of%20%20Granted%20ABC%20Project%20Recognition%20as%20per%20Rule%202023_as_on_06_11_2025.pdf)

Usage (local Docker Postgres is exposed on host port 5433, not 5432):
  DATABASE_URL=postgresql+asyncpg://abc:abc@localhost:5433/abc_dashboard \\
    env -u PYTHONPATH ./.venv/Scripts/python.exe scripts/seed_awbi_centres.py

Also creates an admin user (phone 9999999999 / password admin123).
"""

import asyncio
import hashlib
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.base import Centre, Staff

# State name mapping: AWBI PDF state -> GeoJSON NAME_1
STATE_MAP = {
    "Andhra Pradesh": "Andhra Pradesh",
    "Bihar": "Bihar",
    "Delhi": "Delhi",
    "Gujarat": "Gujarat",
    "Haryana": "Haryana",
    "Jammu and Kashmir": "Jammu and Kashmir",
    "Karnataka": "Karnataka",
    "Kerala": "Kerala",
    "Ladakh": "Ladakh",  # May not be in older GeoJSON - will use Jammu and Kashmir
    "Madhya Pradesh": "Madhya Pradesh",
    "Maharashtra": "Maharashtra",
    "Odisha": "Orissa",  # GeoJSON uses "Orissa"
    "Puducherry": "Puducherry",
    "Punjab": "Punjab",
    "Tamil Nadu": "Tamil Nadu",
    "Telangana": "Telangana",  # May not be in older GeoJSON - will use Andhra Pradesh
    "Uttarakhand": "Uttaranchal",  # GeoJSON uses "Uttaranchal"
}

# Real AWBI centers data (name, district, state_from_pdf, approval_date, valid_upto)
AWBI_CENTERS = [
    ("Universal Animal Welfare Society (Wadaki)", "Wadaki", "Maharashtra", "2023-07-28", "2026-07-27"),
    ("Universal Animal Welfare Society (Katraj)", "Katraj", "Maharashtra", "2023-07-28", "2026-07-27"),
    ("Jeeva Karunya Animal Welfare Charitable Trust", "Kanyakumari", "Tamil Nadu", "2023-09-19", "2026-09-18"),
    ("Kannur District Panchayath", "Kannur", "Kerala", "2023-09-19", "2026-09-18"),
    ("Kollam Municipal Corporation", "Kollam", "Kerala", "2023-09-19", "2026-09-18"),
    ("Thrissur Municipal Corporation", "Thrissur", "Kerala", "2023-09-19", "2026-09-18"),
    ("Ernakulam Veterinary Polyclinic Mulanthuruthy", "Ernakulam", "Kerala", "2023-09-19", "2026-09-18"),
    ("Ernakulam Veterinary Hospital Kolencherry", "Ernakulam", "Kerala", "2023-09-19", "2026-09-18"),
    ("Compassion for Animals Welfare Association (Mohali)", "Mohali", "Punjab", "2023-09-28", "2026-09-27"),
    ("Compassion for Animals Welfare Association (Patiala)", "Patiala", "Punjab", "2023-09-28", "2026-09-27"),
    ("Animal Welfare Charitable Trust Amritsar", "Amritsar", "Punjab", "2024-02-23", "2027-02-22"),
    ("Animal Care Foundation Bhopal", "Bhopal", "Madhya Pradesh", "2024-02-23", "2027-02-22"),
    ("Maa Bagulamukhi Sewa Samiti Jabalpur", "Jabalpur", "Madhya Pradesh", "2024-02-23", "2027-02-22"),
    ("Sneh Animal Welfare Society Srikakulam", "Srikakulam", "Andhra Pradesh", "2024-02-23", "2027-02-22"),
    ("Yash Domestic Research Center Surat", "Surat", "Gujarat", "2024-04-03", "2027-04-02"),
    ("Blue Cross of Hyderabad", "Hyderabad", "Telangana", "2024-04-03", "2027-04-02"),
    ("Santulan Jeev Kalyan Srinagar", "Srinagar", "Jammu and Kashmir", "2024-04-03", "2027-04-02"),
    ("Yash Domestic Research Center Gandhinagar", "Gandhinagar", "Gujarat", "2024-05-21", "2027-05-20"),
    ("Vets Society for Animal Welfare Bengaluru", "Bengaluru", "Karnataka", "2024-09-10", "2027-09-09"),
    ("Yash Domestic Research Center Junagadh", "Junagadh", "Gujarat", "2024-09-19", "2027-09-18"),
    ("The Care of Animals Bathinda", "Bathinda", "Punjab", "2024-09-19", "2027-09-18"),
    ("Compassion Unlimited Plus Action (CUPA) Bengaluru", "Anekal", "Karnataka", "2024-09-19", "2027-09-18"),
    ("Navodaya Vet Society Vijayawada", "Vijayawada", "Andhra Pradesh", "2024-09-19", "2027-09-18"),
    ("Animal Husbandry Dept Leh", "Leh", "Ladakh", "2024-09-19", "2027-09-18"),
    ("Animal Husbandry Dept Kargil", "Kargil", "Ladakh", "2024-09-19", "2027-09-18"),
    ("Greater Chennai Corp Pulianthope", "Chennai", "Tamil Nadu", "2024-09-19", "2027-09-18"),
    ("Greater Chennai Corp Meenambakkam", "Chennai", "Tamil Nadu", "2024-09-19", "2027-09-18"),
    ("Greater Chennai Corp Sholinganallur", "Chennai", "Tamil Nadu", "2024-09-19", "2027-09-18"),
    ("Greater Chennai Corp Kanamapettai", "Chennai", "Tamil Nadu", "2024-09-25", "2027-09-24"),
    ("Sneh Animal Welfare Society Vizianagaram", "Vizianagaram", "Andhra Pradesh", "2024-10-30", "2027-10-29"),
    ("Humane Society International Rudrapur", "Rudrapur", "Uttarakhand", "2024-10-30", "2027-10-29"),
    ("Spandana Animal Welfare Bengaluru", "Hosakote", "Karnataka", "2024-11-04", "2027-11-03"),
    ("All About Them Mumbai", "Mumbai", "Maharashtra", "2024-12-18", "2027-12-17"),
    ("The Care of Animals Indore", "Indore", "Madhya Pradesh", "2025-03-12", "2028-03-11"),
    ("Santulan Jeev Kalyan Anantapur", "Anantapur", "Andhra Pradesh", "2025-03-12", "2028-03-11"),
    ("Navodaya Vet Society Kurnool", "Kurnool", "Andhra Pradesh", "2025-03-12", "2028-03-11"),
    ("Navsamaj Nirman Sanstha Solapur", "Solapur", "Maharashtra", "2025-03-12", "2028-03-11"),
    ("Humane Society International Dehradun", "Dehradun", "Uttarakhand", "2025-03-12", "2028-03-11"),
    ("Kanichukulangara ABC Centre Alappuzha", "Alappuzha", "Kerala", "2025-03-12", "2028-03-11"),
    ("Veterinary Polyclinic Sulthan Bathery", "Wayanad", "Kerala", "2025-05-06", "2028-05-05"),
    ("Yash Domestic Research Center Ahmedabad", "Ahmedabad", "Gujarat", "2025-05-06", "2028-05-05"),
    ("Yash Domestic Research Center Bela Road Delhi", "Delhi", "Delhi", "2025-07-21", "2028-07-20"),
    ("Yash Domestic Research Center Tuglakabad Delhi", "Delhi", "Delhi", "2025-07-21", "2028-07-20"),
    ("Sneh Animal Welfare Society Usmanpur Delhi", "Delhi", "Delhi", "2025-07-21", "2028-07-20"),
    ("Sneh Animal Welfare Society Dwarka Delhi", "Delhi", "Delhi", "2025-07-21", "2028-07-20"),
    ("Friendicoes SECA Kotla Delhi", "Delhi", "Delhi", "2025-07-21", "2028-07-20"),
    ("Friendicoes SECA Bijwasan Delhi", "Delhi", "Delhi", "2025-07-21", "2028-07-20"),
    ("Ruth Cowell Foundation Delhi", "Delhi", "Delhi", "2025-07-21", "2028-07-20"),
    ("Animal Care Trust Mangalore", "Mangalore", "Karnataka", "2025-07-21", "2028-07-20"),
    ("Sonadi Charitable Trust Delhi", "Delhi", "Delhi", "2025-08-29", "2028-08-28"),
    ("Companion Animal Welfare Society Delhi", "Delhi", "Delhi", "2025-08-29", "2028-08-28"),
    ("Santulan Jeev Kalyan Patna", "Patna", "Bihar", "2025-08-29", "2028-08-28"),
    ("Vets Society for Animal Welfare Bhubaneswar", "Bhubaneswar", "Odisha", "2025-08-29", "2028-08-28"),
    ("Captains Animal Care Trust Manipal", "Udupi", "Karnataka", "2025-08-29", "2028-08-28"),
    ("Spandana Animal Welfare Bengaluru (Sadarmangala)", "Bangalore", "Karnataka", "2025-08-29", "2028-08-28"),
    ("Vets Society for Animal Welfare Pondicherry", "Pondicherry", "Puducherry", "2025-09-01", "2028-08-31"),
    ("Sneh Animal Welfare Society Guntur", "Guntur", "Andhra Pradesh", "2025-09-01", "2028-08-31"),
    ("Sneh Animal Welfare Society Mangalgiri", "Mangalgiri", "Andhra Pradesh", "2025-10-17", "2028-10-16"),
    ("Santulan Jeev Kalyan Hisar", "Hisar", "Haryana", "2025-10-17", "2028-10-16"),
    ("Sonadi Charitable Trust Delhi (Nagli)", "Delhi", "Delhi", "2025-10-17", "2028-10-16"),
    ("Yash Domestic Research Center Palanpur", "Palanpur", "Gujarat", "2025-10-17", "2028-10-16"),
    ("Siddhi Animal Welfare Society Dwarka", "Delhi", "Delhi", "2025-10-17", "2028-10-16"),
    ("ABC Centre Tripunithura Ernakulam", "Ernakulam", "Kerala", "2025-10-17", "2028-10-16"),
    ("Friendicoes SECA Ghazipur Delhi", "Delhi", "Delhi", "2025-10-22", "2028-10-21"),
    ("Nain Foundation Kasaragod", "Kasaragod", "Kerala", "2025-10-22", "2028-10-21"),
    ("ABC Balussery Kozhikode", "Kozhikode", "Kerala", "2025-10-22", "2028-10-21"),
]


async def seed_centres():
    async for db in get_db():
        # Check if centres already exist
        existing = await db.execute(select(Centre))
        if existing.scalars().first():
            print("Centres already exist, skipping seed")
            return

        now = datetime.now(UTC).replace(tzinfo=None)

        for name, district, pdf_state, approval_str, valid_str in AWBI_CENTERS:
            # Map state name to GeoJSON
            geojson_state = STATE_MAP.get(pdf_state, pdf_state)

            # Generate a clean unique code from name (base + short hash to avoid collisions)
            base = "".join(c.upper() for c in name if c.isalnum())[:12]
            code = (base + hashlib.md5(name.encode()).hexdigest()[:4].upper())[:15]

            centre = Centre(
                id=str(uuid4()),
                name=name,
                code=code,
                district=district,
                state=geojson_state,
                capacity=50,  # Default capacity
                status="active",
                created_at=now,
            )
            db.add(centre)

        await db.commit()
        print(f"Seeded {len(AWBI_CENTERS)} centres")

        # Also create a default admin staff user for testing
        from src.auth.deps import hash_password
        admin = Staff(
            id=str(uuid4()),
            centre_id=None,
            name="System Admin",
            role="admin",
            phone="9999999999",
            password_hash=hash_password("admin123"),
            active=True,
        )
        db.add(admin)
        await db.commit()
        print("Created admin user: phone=9999999999, password=admin123")


if __name__ == "__main__":
    asyncio.run(seed_centres())