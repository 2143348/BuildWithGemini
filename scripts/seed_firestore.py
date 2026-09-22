import os
from google.cloud import firestore

# Hardcode the project ID string to avoid project number issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-01-d2704f34ae2b"

def seed_database():
    print(f"Connecting to Firestore with project ID: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    catalog_ref = db.collection("catalog")

    items = [
        {
            "product_id": "blazer-001",
            "name": "Autumn Velvet Blazer",
            "category": "blazers",
            "fabrics": ["Cotton Velvet", "Viscose Lining"],
            "colors": ["Navy", "Emerald", "Burgundy"],
            "price": 180.0,
            "vibe": "chic",
            "in_stock": True,
            "description": "Luxurious cotton velvet structured blazer with gold buttons."
        },
        {
            "product_id": "blazer-002",
            "name": "Oversized Linen Blazer",
            "category": "blazers",
            "fabrics": ["100% Organic Linen"],
            "colors": ["Sand", "Off-White"],
            "price": 150.0,
            "vibe": "effortless",
            "in_stock": True,
            "description": "Lightweight breathable organic linen blazer perfect for layering."
        },
        {
            "product_id": "dress-001",
            "name": "Silk Evening Slip Dress",
            "category": "dresses",
            "fabrics": ["100% Mulberry Silk"],
            "colors": ["Champagne", "Midnight"],
            "price": 210.0,
            "vibe": "evening",
            "in_stock": True,
            "description": "Elegant bias-cut mulberry silk slip dress with adjustable straps."
        },
        {
            "product_id": "active-001",
            "name": "Verve Sculpt Leggings & Bra Set",
            "category": "activewear",
            "fabrics": ["Nylon", "Spandex"],
            "colors": ["Charcoal", "Sage"],
            "price": 110.0,
            "vibe": "bold",
            "in_stock": True,
            "description": "Four-way stretch high-waisted sculpt set built for movement and comfort."
        }
    ]

    for item in items:
        doc_ref = catalog_ref.document(item["product_id"])
        doc_ref.set(item)
        print(f"Seeded document: {item['product_id']} ({item['name']})")

    print("Firestore seeding complete!")

if __name__ == "__main__":
    seed_database()
