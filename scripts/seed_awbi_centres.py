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
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from src.database import get_db
from src.models.base import Centre, Staff

# State name constants (single source of truth for STATE_MAP and AWBI_CENTERS)
ANDHRA_PRADESH = "Andhra Pradesh"
BIHAR = "Bihar"
DELHI = "Delhi"
GUJARAT = "Gujarat"
HARYANA = "Haryana"
JAMMU_AND_KASHMIR = "Jammu and Kashmir"
KARNATAKA = "Karnataka"
KERALA = "Kerala"
LADAKH = "Ladakh"
MADHYA_PRADESH = "Madhya Pradesh"
MAHARASHTRA = "Maharashtra"
ODISHA = "Odisha"
PUDUCHERRY = "Puducherry"
PUNJAB = "Punjab"
TAMIL_NADU = "Tamil Nadu"
TELANGANA = "Telangana"
UTTARAKHAND = "Uttarakhand"

# State name mapping: AWBI PDF state -> GeoJSON NAME_1
STATE_MAP = {
    ANDHRA_PRADESH: ANDHRA_PRADESH,
    BIHAR: BIHAR,
    DELHI: DELHI,
    GUJARAT: GUJARAT,
    HARYANA: HARYANA,
    JAMMU_AND_KASHMIR: JAMMU_AND_KASHMIR,
    KARNATAKA: KARNATAKA,
    KERALA: KERALA,
    LADAKH: LADAKH,  # May not be in older GeoJSON - will use Jammu and Kashmir
    MADHYA_PRADESH: MADHYA_PRADESH,
    MAHARASHTRA: MAHARASHTRA,
    ODISHA: "Orissa",  # GeoJSON uses "Orissa"
    PUDUCHERRY: PUDUCHERRY,
    PUNJAB: PUNJAB,
    TAMIL_NADU: TAMIL_NADU,
    TELANGANA: TELANGANA,  # May not be in older GeoJSON - will use Andhra Pradesh
    UTTARAKHAND: "Uttaranchal",  # GeoJSON uses "Uttaranchal"
}

# Real AWBI centers data (name, district, state_from_pdf, approval_date, valid_upto)
AWBI_CENTERS = [
    ("Universal Animal Welfare Society (Wadaki)", "Wadaki", MAHARASHTRA, "2023-07-28", "2026-07-27"),
    ("Universal Animal Welfare Society (Katraj)", "Katraj", MAHARASHTRA, "2023-07-28", "2026-07-27"),
    ("Jeeva Karunya Animal Welfare Charitable Trust", "Kanyakumari", TAMIL_NADU, "2023-09-19", "2026-09-18"),
    ("Kannur District Panchayath", "Kannur", KERALA, "2023-09-19", "2026-09-18"),
    ("Kollam Municipal Corporation", "Kollam", KERALA, "2023-09-19", "2026-09-18"),
    ("Thrissur Municipal Corporation", "Thrissur", KERALA, "2023-09-19", "2026-09-18"),
    ("Ernakulam Veterinary Polyclinic Mulanthuruthy", "Ernakulam", KERALA, "2023-09-19", "2026-09-18"),
    ("Ernakulam Veterinary Hospital Kolencherry", "Ernakulam", KERALA, "2023-09-19", "2026-09-18"),
    ("Compassion for Animals Welfare Association (Mohali)", "Mohali", PUNJAB, "2023-09-28", "2026-09-27"),
    ("Compassion for Animals Welfare Association (Patiala)", "Patiala", PUNJAB, "2023-09-28", "2026-09-27"),
    ("Animal Welfare Charitable Trust Amritsar", "Amritsar", PUNJAB, "2024-02-23", "2027-02-22"),
    ("Animal Care Foundation Bhopal", "Bhopal", MADHYA_PRADESH, "2024-02-23", "2027-02-22"),
    ("Maa Bagulamukhi Sewa Samiti Jabalpur", "Jabalpur", MADHYA_PRADESH, "2024-02-23", "2027-02-22"),
    ("Sneh Animal Welfare Society Srikakulam", "Srikakulam", ANDHRA_PRADESH, "2024-02-23", "2027-02-22"),
    ("Yash Domestic Research Center Surat", "Surat", GUJARAT, "2024-04-03", "2027-04-02"),
    ("Blue Cross of Hyderabad", "Hyderabad", TELANGANA, "2024-04-03", "2027-04-02"),
    ("Santulan Jeev Kalyan Srinagar", "Srinagar", JAMMU_AND_KASHMIR, "2024-04-03", "2027-04-02"),
    ("Yash Domestic Research Center Gandhinagar", "Gandhinagar", GUJARAT, "2024-05-21", "2027-05-20"),
    ("Vets Society for Animal Welfare Bengaluru", "Bengaluru", KARNATAKA, "2024-09-10", "2027-09-09"),
    ("Yash Domestic Research Center Junagadh", "Junagadh", GUJARAT, "2024-09-19", "2027-09-18"),
    ("The Care of Animals Bathinda", "Bathinda", PUNJAB, "2024-09-19", "2027-09-18"),
    ("Compassion Unlimited Plus Action (CUPA) Bengaluru", "Anekal", KARNATAKA, "2024-09-19", "2027-09-18"),
    ("Navodaya Vet Society Vijayawada", "Vijayawada", ANDHRA_PRADESH, "2024-09-19", "2027-09-18"),
    ("Animal Husbandry Dept Leh", "Leh", LADAKH, "2024-09-19", "2027-09-18"),
    ("Animal Husbandry Dept Kargil", "Kargil", LADAKH, "2024-09-19", "2027-09-18"),
    ("Greater Chennai Corp Pulianthope", "Chennai", TAMIL_NADU, "2024-09-19", "2027-09-18"),
    ("Greater Chennai Corp Meenambakkam", "Chennai", TAMIL_NADU, "2024-09-19", "2027-09-18"),
    ("Greater Chennai Corp Sholinganallur", "Chennai", TAMIL_NADU, "2024-09-19", "2027-09-18"),
    ("Greater Chennai Corp Kanamapettai", "Chennai", TAMIL_NADU, "2024-09-25", "2027-09-24"),
    ("Sneh Animal Welfare Society Vizianagaram", "Vizianagaram", ANDHRA_PRADESH, "2024-10-30", "2027-10-29"),
    ("Humane Society International Rudrapur", "Rudrapur", UTTARAKHAND, "2024-10-30", "2027-10-29"),
    ("Spandana Animal Welfare Bengaluru", "Hosakote", KARNATAKA, "2024-11-04", "2027-11-03"),
    ("All About Them Mumbai", "Mumbai", MAHARASHTRA, "2024-12-18", "2027-12-17"),
    ("The Care of Animals Indore", "Indore", MADHYA_PRADESH, "2025-03-12", "2028-03-11"),
    ("Santulan Jeev Kalyan Anantapur", "Anantapur", ANDHRA_PRADESH, "2025-03-12", "2028-03-11"),
    ("Navodaya Vet Society Kurnool", "Kurnool", ANDHRA_PRADESH, "2025-03-12", "2028-03-11"),
    ("Navsamaj Nirman Sanstha Solapur", "Solapur", MAHARASHTRA, "2025-03-12", "2028-03-11"),
    ("Humane Society International Dehradun", "Dehradun", UTTARAKHAND, "2025-03-12", "2028-03-11"),
    ("Kanichukulangara ABC Centre Alappuzha", "Alappuzha", KERALA, "2025-03-12", "2028-03-11"),
    ("Veterinary Polyclinic Sulthan Bathery", "Wayanad", KERALA, "2025-05-06", "2028-05-05"),
    ("Yash Domestic Research Center Ahmedabad", "Ahmedabad", GUJARAT, "2025-05-06", "2028-05-05"),
    ("Yash Domestic Research Center Bela Road Delhi", "Delhi", DELHI, "2025-07-21", "2028-07-20"),
    ("Yash Domestic Research Center Tuglakabad Delhi", "Delhi", DELHI, "2025-07-21", "2028-07-20"),
    ("Sneh Animal Welfare Society Usmanpur Delhi", "Delhi", DELHI, "2025-07-21", "2028-07-20"),
    ("Sneh Animal Welfare Society Dwarka Delhi", "Delhi", DELHI, "2025-07-21", "2028-07-20"),
    ("Friendicoes SECA Kotla Delhi", "Delhi", DELHI, "2025-07-21", "2028-07-20"),
    ("Friendicoes SECA Bijwasan Delhi", "Delhi", DELHI, "2025-07-21", "2028-07-20"),
    ("Ruth Cowell Foundation Delhi", "Delhi", DELHI, "2025-07-21", "2028-07-20"),
    ("Animal Care Trust Mangalore", "Mangalore", KARNATAKA, "2025-07-21", "2028-07-20"),
    ("Sonadi Charitable Trust Delhi", "Delhi", DELHI, "2025-08-29", "2028-08-28"),
    ("Companion Animal Welfare Society Delhi", "Delhi", DELHI, "2025-08-29", "2028-08-28"),
    ("Santulan Jeev Kalyan Patna", "Patna", BIHAR, "2025-08-29", "2028-08-28"),
    ("Vets Society for Animal Welfare Bhubaneswar", "Bhubaneswar", ODISHA, "2025-08-29", "2028-08-28"),
    ("Captains Animal Care Trust Manipal", "Udupi", KARNATAKA, "2025-08-29", "2028-08-28"),
    ("Spandana Animal Welfare Bengaluru (Sadarmangala)", "Bangalore", KARNATAKA, "2025-08-29", "2028-08-28"),
    ("Vets Society for Animal Welfare Pondicherry", "Pondicherry", PUDUCHERRY, "2025-09-01", "2028-08-31"),
    ("Sneh Animal Welfare Society Guntur", "Guntur", ANDHRA_PRADESH, "2025-09-01", "2028-08-31"),
    ("Sneh Animal Welfare Society Mangalgiri", "Mangalgiri", ANDHRA_PRADESH, "2025-10-17", "2028-10-16"),
    ("Santulan Jeev Kalyan Hisar", "Hisar", HARYANA, "2025-10-17", "2028-10-16"),
    ("Sonadi Charitable Trust Delhi (Nagli)", "Delhi", DELHI, "2025-10-17", "2028-10-16"),
    ("Yash Domestic Research Center Palanpur", "Palanpur", GUJARAT, "2025-10-17", "2028-10-16"),
    ("Siddhi Animal Welfare Society Dwarka", "Delhi", DELHI, "2025-10-17", "2028-10-16"),
    ("ABC Centre Tripunithura Ernakulam", "Ernakulam", KERALA, "2025-10-17", "2028-10-16"),
    ("Friendicoes SECA Ghazipur Delhi", "Delhi", DELHI, "2025-10-22", "2028-10-21"),
    ("Nain Foundation Kasaragod", "Kasaragod", KERALA, "2025-10-22", "2028-10-21"),
    ("ABC Balussery Kozhikode", "Kozhikode", KERALA, "2025-10-22", "2028-10-21"),
]


async def seed_centres():
    async for db in get_db():
        # Check if centres already exist
        existing = await db.execute(select(Centre))
        if existing.scalars().first():
            print("Centres already exist, skipping seed")
            return

        now = datetime.now(UTC).replace(tzinfo=None)

        for name, district, pdf_state, _approval_str, _valid_str in AWBI_CENTERS:
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
