import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "sample_catalog.json"
PRODUCTS_DIR = ROOT / "products"


@dataclass
class Product:
    id: str
    name: str
    description: str
    price: float
    color: str
    style: str
    material: str
    size: str
    brand: str
    product_id: str
    image_url: str
    category: str


def ensure_products_dir() -> None:
    PRODUCTS_DIR.mkdir(exist_ok=True)


def clear_existing_images() -> None:
    if not PRODUCTS_DIR.exists():
        return
    for f in PRODUCTS_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            f.unlink()


def generate_image(product: Product) -> None:
    """Create a simple placeholder image for the product."""
    width, height = 512, 512
    # Simple color palette by theme/category
    base_colors = {
        "beach": (135, 206, 235),      # sky blue
        "summer": (255, 215, 0),       # golden
        "bridal": (245, 245, 245),     # off white
        "office": (200, 200, 210),     # gray
    }

    theme_key = "beach"
    name_lower = product.name.lower()
    if "office" in name_lower or "formal" in name_lower or "blazer" in name_lower or "shirt" in name_lower:
        theme_key = "office"
    elif "bridal" in name_lower or "wedding" in name_lower or "bride" in name_lower:
        theme_key = "bridal"
    elif "summer" in name_lower:
        theme_key = "summer"
    elif "beach" in name_lower or "resort" in name_lower:
        theme_key = "beach"

    bg_color = base_colors.get(theme_key, (220, 220, 220))

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    text = product.name[:40]
    try:
        # Use a default font that should exist; Pillow will fall back if not
        font = ImageFont.load_default()
    except Exception:
        font = None

    text_color = (40, 40, 40)
    # Pillow 10+ removed textsize; use textbbox instead
    if font is not None:
        bbox = draw.textbbox((0, 0), text, font=font)
    else:
        bbox = draw.textbbox((0, 0), text)

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) / 2
    y = (height - text_height) / 2

    draw.text((x, y), text, fill=text_color, font=font)

    out_path = ROOT / product.image_url
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")


def build_products() -> List[Product]:
    products: List[Product] = []

    sizes = ["S", "M", "L", "XL"]

    # We will create 25 products per category * 4 categories = 100

    # Tops
    top_templates = [
        ("Beach Linen Shirt", "Lightweight linen shirt ideal for seaside walks and beach vacations.", "beach", "linen", "SummerTide"),
        ("Summer Cotton Tee", "Breathable cotton t-shirt perfect for hot summer days.", "summer", "cotton", "SunBreeze"),
        ("Bridal Silk Blouse", "Delicate silk blouse designed to pair with bridal skirts and lehengas.", "bridal", "silk", "BridalAura"),
        ("Office Formal Shirt", "Crisp formal shirt tailored for everyday office wear.", "office", "cotton", "OfficeLine"),
        ("Resort Wrap Top", "Wrap-style top ideal for beach resorts and summer getaways.", "beach", "rayon", "ResortWave"),
    ]

    colors_top = ["white", "ivory", "blue", "coral", "navy", "mint", "beige"]
    idx = 101
    for i in range(25):
        base = top_templates[i % len(top_templates)]
        name, desc, theme, material, brand = base
        color = colors_top[i % len(colors_top)]
        size = sizes[i % len(sizes)]
        style = {
            "beach": "casual",
            "summer": "casual",
            "bridal": "formal",
            "office": "formal",
        }[theme]
        pid = f"top_{idx:03d}"
        products.append(
            Product(
                id=pid,
                name=f"{color.title()} {name}",
                description=f"{desc} Color: {color.title()}. Size: {size}.",
                price=round(39.99 + (i % 8) * 5, 2),
                color=color,
                style=style,
                material=material,
                size=size,
                brand=brand,
                product_id=pid,
                image_url=f"products/{pid}.png",
                category="tops",
            )
        )
        idx += 1

    # Bottoms
    bottom_templates = [
        ("Beach Chino Shorts", "Comfortable chino shorts ideal for beach walks and casual outings.", "beach", "cotton", "CoastLine"),
        ("Summer Linen Trousers", "Relaxed fit linen trousers perfect for tropical climates.", "summer", "linen", "SummerEase"),
        ("Bridal Skirt", "Elegant long skirt designed for bridal functions and receptions.", "bridal", "silk blend", "BridalAura"),
        ("Office Formal Trousers", "Tailored trousers ideal for office formals and meetings.", "office", "wool blend", "BoardRoom"),
        ("Resort Palazzo Pants", "Wide-leg palazzo pants with airy drape for summer getaways.", "beach", "rayon", "ResortWave"),
    ]
    colors_bottom = ["sand", "khaki", "white", "navy", "olive", "taupe", "charcoal"]
    idx = 201
    for i in range(25):
        name, desc, theme, material, brand = bottom_templates[i % len(bottom_templates)]
        color = colors_bottom[i % len(colors_bottom)]
        size = sizes[i % len(sizes)]
        style = {
            "beach": "casual",
            "summer": "casual",
            "bridal": "formal",
            "office": "formal",
        }[theme]
        pid = f"bottom_{idx:03d}"
        products.append(
            Product(
                id=pid,
                name=f"{color.title()} {name}",
                description=f"{desc} Color: {color.title()}. Size: {size}.",
                price=round(49.99 + (i % 8) * 6, 2),
                color=color,
                style=style,
                material=material,
                size=size,
                brand=brand,
                product_id=pid,
                image_url=f"products/{pid}.png",
                category="bottoms",
            )
        )
        idx += 1

    # Dresses
    dress_templates = [
        ("Beach Maxi Dress", "Flowy maxi dress ideal for beach sunsets and resort dinners.", "beach", "chiffon", "CoastElegance"),
        ("Summer Sundress", "Light sundress with breathable fabric for hot summer days.", "summer", "cotton", "SunBloom"),
        ("Bridal Gown", "Full-length bridal gown with lace details for wedding ceremonies.", "bridal", "satin lace", "BridalGrace"),
        ("Office Sheath Dress", "Structured sheath dress ideal for office presentations and meetings.", "office", "polyester blend", "OfficeCurve"),
        ("Resort Wrap Dress", "Wrap-style dress perfect for holiday brunches and summer travel.", "beach", "rayon", "ResortCharm"),
    ]
    colors_dress = ["white", "blush", "aqua", "navy", "peach", "lavender", "emerald"]
    idx = 301
    for i in range(25):
        name, desc, theme, material, brand = dress_templates[i % len(dress_templates)]
        color = colors_dress[i % len(colors_dress)]
        size = sizes[i % len(sizes)]
        style = {
            "beach": "casual",
            "summer": "casual",
            "bridal": "formal",
            "office": "formal",
        }[theme]
        pid = f"dress_{idx:03d}"
        products.append(
            Product(
                id=pid,
                name=f"{color.title()} {name}",
                description=f"{desc} Color: {color.title()}. Size: {size}.",
                price=round(59.99 + (i % 8) * 8, 2),
                color=color,
                style=style,
                material=material,
                size=size,
                brand=brand,
                product_id=pid,
                image_url=f"products/{pid}.png",
                category="dresses",
            )
        )
        idx += 1

    # Shoes
    shoe_templates = [
        ("Beach Slide Sandals", "Easy slide sandals ideal for poolside and sandy beaches.", "beach", "rubber", "ShoreStep"),
        ("Summer Espadrilles", "Lightweight espadrilles perfect for summer strolls.", "summer", "canvas", "SunWalk"),
        ("Bridal Heels", "Elegant high-heel shoes designed for bridal receptions.", "bridal", "satin", "BridalStep"),
        ("Office Loafers", "Classic loafers suitable for daily office formals.", "office", "leather", "DeskStride"),
        ("Resort Wedge Sandals", "Comfortable wedge sandals ideal for resort dinners.", "beach", "synthetic", "ResortStep"),
    ]
    colors_shoes = ["tan", "white", "gold", "silver", "black", "nude", "rose gold"]
    idx = 401
    for i in range(25):
        name, desc, theme, material, brand = shoe_templates[i % len(shoe_templates)]
        color = colors_shoes[i % len(colors_shoes)]
        size = str(6 + (i % 6))
        style = {
            "beach": "casual",
            "summer": "casual",
            "bridal": "formal",
            "office": "formal",
        }[theme]
        pid = f"shoes_{idx:03d}"
        products.append(
            Product(
                id=pid,
                name=f"{color.title()} {name}",
                description=f"{desc} Color: {color.title()}. Size: {size}.",
                price=round(39.99 + (i % 8) * 7, 2),
                color=color,
                style=style,
                material=material,
                size=size,
                brand=brand,
                product_id=pid,
                image_url=f"products/{pid}.png",
                category="shoes",
            )
        )
        idx += 1

    return products


def write_catalog(products: List[Product]) -> None:
    data = {"products": [asdict(p) for p in products]}
    with CATALOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main() -> None:
    ensure_products_dir()
    clear_existing_images()
    products = build_products()
    # Generate images
    for p in products:
        generate_image(p)
    write_catalog(products)
    print(f"Generated {len(products)} products and updated catalog at {CATALOG_PATH}.")


if __name__ == "__main__":
    main()
