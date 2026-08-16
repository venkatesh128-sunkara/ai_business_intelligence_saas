"""Seed the database with an admin user, a demo user and a rich sample sales dataset."""
import random
from datetime import date, timedelta

import pandas as pd

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import Dataset, UsageRecord, User, Workspace
from app.services.data_processor import DataProcessor

PRODUCTS = [
    ("Wireless Headphones", 89, 42, "Electronics"),
    ("Laptop Stand", 39, 58, "Accessories"),
    ("Mechanical Keyboard", 129, 35, "Electronics"),
    ("USB-C Dock", 99, 30, "Electronics"),
    ("Desk Lamp", 45, 50, "Home"),
    ("Ergonomic Chair", 249, 25, "Furniture"),
    ("Standing Desk", 429, 18, "Furniture"),
    ("Webcam HD", 79, 33, "Electronics"),
    ("Noise-cancelling Mic", 149, 22, "Electronics"),
    ("Monitor 27in", 299, 40, "Electronics"),
    ("Cable Organizer", 15, 65, "Accessories"),
    ("Desk Mat", 29, 48, "Accessories"),
    ("Smart Speaker", 119, 38, "Electronics"),
    ("Power Bank", 49, 44, "Accessories"),
    ("Fitness Tracker", 139, 29, "Electronics"),
]

REGIONS = ["North America", "Europe", "Asia Pacific", "South America", "Middle East"]
CHANNELS = ["Online", "Retail", "Partner", "Wholesale"]
CUSTOMERS = [f"Cust_{i:04d}" for i in range(1, 41)]


def generate_sales(start: date, end: date, n: int) -> pd.DataFrame:
    random.seed(42)
    rows = []
    days = (end - start).days
    for _ in range(n):
        day = start + timedelta(days=random.randint(0, days))
        product, price, margin, category = random.choice(PRODUCTS)
        qty = random.randint(1, 25)
        channel = random.choice(CHANNELS)
        region = random.choice(REGIONS)
        customer = random.choice(CUSTOMERS)
        rows.append({
            "order_date": day,
            "product": product,
            "category": category,
            "region": region,
            "channel": channel,
            "customer": customer,
            "quantity": qty,
            "unit_price": price,
            "revenue": round(qty * price * (random.uniform(0.85, 1.15)), 2),
            "cost": round(qty * price * (1 - margin / 100), 2),
        })
    return pd.DataFrame(rows)


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter_by(email=settings.ADMIN_EMAIL).first()
        if admin is None:
            admin = User(
                email=settings.ADMIN_EMAIL,
                name="Platform Admin",
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
                plan="pro",
            )
            db.add(admin)
            db.flush()
            db.add(Workspace(name="Admin Workspace", description="Platform admin workspace", owner_id=admin.id))
            print("Created admin user:", settings.ADMIN_EMAIL)
        else:
            print("Admin user already exists")

        demo = db.query(User).filter_by(email="demo@insightiq.dev").first()
        if demo is None:
            demo = User(
                email="demo@insightiq.dev",
                name="Demo User",
                hashed_password=hash_password("demo123"),
                role="member",
                plan="free",
            )
            db.add(demo)
            db.flush()
            db.add(Workspace(name="Demo User's Workspace", description="Personal workspace", owner_id=demo.id))
            print("Created demo user: demo@insightiq.dev / demo123")
        else:
            print("Demo user already exists")

        db.flush()
        db.commit()

        existing = db.query(Dataset).filter_by(name="Sample Sales Data").first()
        if existing is None:
            today = date(2024, 1, 1)
            start = today - timedelta(days=540)
            df = generate_sales(start, today, 3000)
            bytes_io = df.to_csv(index=False).encode("utf-8")
            processor = DataProcessor()
            result = processor.process(bytes_io, "sample_sales.csv", "Sample Sales Data")
            ws = db.query(Workspace).filter_by(owner_id=demo.id).first()
            ds = Dataset(
                workspace_id=ws.id,
                name="Sample Sales Data",
                filename="sample_sales.csv",
                table_name=result["table_name"],
                source_type="csv",
                status="ready",
                row_count=result["row_count"],
                column_count=result["column_count"],
                file_size=result["file_size"],
                storage_path=result["storage_path"],
                profile_json=result["profile_json"],
                schema_json=result["schema_json"],
                created_by=demo.id,
            )
            db.add(ds)
            print("Created sample sales dataset with", result["row_count"], "rows")
        else:
            print("Sample dataset already exists")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
