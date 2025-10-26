import io
import json
from PIL import Image
import httpx


def make_test_image() -> bytes:
    # Create a simple 64x64 gray PNG
    img = Image.new("RGB", (64, 64), (200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main():
    png_bytes = make_test_image()

    files = {"file": ("test.png", png_bytes, "image/png")}
    data = {
        "project_type": "bathroom",
        "description": "Automated smoke test with synthetic image",
    }

    import os
    url = os.getenv("API_URL", "http://localhost:8000/v1/quotes")

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, files=files, data=data)
            print(f"HTTP {resp.status_code}")
            if resp.status_code != 200:
                print(resp.text)
                return

            data = resp.json()
            # Summarize key fields
            materials = data.get("materials", [])
            labor = data.get("labor", [])
            total_cost = data.get("total_cost")
            timeline = data.get("timeline")

            print("Summary:")
            print(f"  id: {data.get('id')}")
            print(f"  materials: {len(materials)} items")
            print(f"  labor: {len(labor)} items")
            # total_cost schema: { amount, breakdown: { materials, labor, markup } }
            if isinstance(total_cost, dict):
                amount = total_cost.get('amount')
                breakdown = total_cost.get('breakdown', {})
                print(f"  total_cost.amount: ${amount}")
                print(f"    materials: ${breakdown.get('materials', 0)}")
                print(f"    labor: ${breakdown.get('labor', 0)}")
                print(f"    markup: ${breakdown.get('markup', 0)}")
            else:
                print(f"  total_cost: {total_cost}")
            if isinstance(timeline, dict):
                print(f"  timeline.estimated_days: {timeline.get('estimated_days')}")
            else:
                print(f"  timeline: {timeline}")

            # Show a couple of extracted materials
            for m in materials[:3]:
                name = m.get("name")
                qty = m.get("quantity")
                unit = m.get("unit")
                print(f"    - {name}: {qty} {unit}")

    except Exception as e:
        print("Error during smoke test:", e)


if __name__ == "__main__":
    main()
