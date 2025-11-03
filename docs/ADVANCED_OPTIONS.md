# Advanced Options API Reference

## Overview

The `/v1/quotes` endpoint now accepts an `options` parameter (JSON string) that allows users to customize estimate calculations with material quality, profit margins, contingency, and regional labor rates.

## Request Format

```bash
POST /v1/quotes
Content-Type: multipart/form-data

file: <image file>
project_type: "bathroom"
description: "Master bathroom renovation"
options: '{"quality":"premium","contingency_pct":10,"profit_pct":20,"region":"northeast"}'
```

## Options Schema

```json
{
  "quality": "standard" | "premium" | "luxury",
  "contingency_pct": 0-30,
  "profit_pct": 0-50,
  "region": "midwest" | "south" | "northeast" | "west"
}
```

### Material Quality

Controls material pricing multiplier:

- **standard** (default): 1.0x base price
  - Example: Standard ceramic tile, stock cabinets, basic fixtures
  
- **premium**: 1.3x base price
  - Example: Designer tile, semi-custom cabinets, mid-range fixtures
  
- **luxury**: 1.8x base price
  - Example: Natural stone, custom cabinets, high-end fixtures

### Contingency Percentage

Buffer for unexpected costs (0-30%):

- **0%** (default): No contingency
- **5-10%**: Typical for well-defined projects
- **15-20%**: Older homes or uncertain scope
- **20-30%**: Major renovations with potential surprises

Applied to subtotal (materials + labor) before profit.

### Profit Percentage

Contractor profit margin (0-50%):

- **15%** (default): Standard residential markup
- **10-20%**: Competitive residential range
- **20-30%**: Commercial or specialty work
- **30-50%**: High-risk or premium services

Applied to subtotal (materials + labor) before contingency.

### Region

Labor rate adjustment based on geographic market:

- **midwest** (default): 1.0x base rate
  - States: OH, IN, IL, MI, WI, MN, IA, MO, ND, SD, NE, KS
  
- **south**: 0.85x base rate
  - States: TX, OK, AR, LA, MS, AL, TN, KY, WV, VA, NC, SC, GA, FL
  
- **northeast**: 1.25x base rate
  - States: PA, NY, NJ, CT, RI, MA, VT, NH, ME, MD, DE, DC
  
- **west**: 1.35x base rate
  - States: CA, OR, WA, NV, AZ, UT, CO, WY, MT, ID, NM, AK, HI

## Response Format

The response includes the applied options in `options_applied`:

```json
{
  "id": "quote_abc123",
  "total_cost": {
    "currency": "USD",
    "amount": 8450.00,
    "breakdown": {
      "materials": 3200.00,
      "labor": 2800.00,
      "profit": 900.00,
      "contingency": 550.00
    }
  },
  "options_applied": {
    "quality": "premium",
    "contingency_pct": 10.0,
    "profit_pct": 15.0,
    "region": "midwest"
  },
  "materials": [...],
  "labor": [...],
  "timeline": {...}
}
```

## Calculation Flow

1. **Base Material Cost** = Σ(quantity × unit_price) for each material
2. **Adjusted Material Cost** = Base Material Cost × quality_multiplier
3. **Base Labor Cost** = labor_hours × trade_rate
4. **Adjusted Labor Cost** = Base Labor Cost × region_multiplier
5. **Subtotal** = Adjusted Material Cost + Adjusted Labor Cost
6. **Profit** = Subtotal × (profit_pct / 100)
7. **Contingency** = Subtotal × (contingency_pct / 100)
8. **Total** = Subtotal + Profit + Contingency

## Example Use Cases

### Budget-Conscious Homeowner

```json
{
  "quality": "standard",
  "contingency_pct": 5,
  "profit_pct": 10,
  "region": "south"
}
```

Result: Competitive pricing with minimal markup

### High-End Remodel

```json
{
  "quality": "luxury",
  "contingency_pct": 15,
  "profit_pct": 25,
  "region": "west"
}
```

Result: Premium materials with appropriate risk buffer and high-end market rates

### Commercial Project

```json
{
  "quality": "premium",
  "contingency_pct": 20,
  "profit_pct": 30,
  "region": "northeast"
}
```

Result: Commercial-grade pricing with higher margins and risk buffer

## Defaults

If `options` is omitted or empty, the system uses:

```json
{
  "quality": "standard",
  "contingency_pct": 0.0,
  "profit_pct": 15.0,
  "region": "midwest"
}
```

## Frontend Integration

The mobile-index.html page includes UI controls for all options:

1. Material Quality dropdown (standard/premium/luxury)
2. Contingency slider (0-30%)
3. Profit slider (0-50%)
4. Region dropdown (midwest/south/northeast/west)

These are sent as JSON in the `options` form field.

## Validation

- Invalid quality values default to "standard"
- Percentages are clamped to valid ranges (contingency: 0-30, profit: 0-50)
- Invalid region values default to "midwest"
- Non-numeric percentage values default to their respective defaults (0.0 for contingency, 15.0 for profit)

## Testing

Test with curl:

```bash
curl -X POST https://api.estimategenie.net/v1/quotes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@bathroom.jpg" \
  -F "project_type=bathroom" \
  -F "description=Tile shower install" \
  -F 'options={"quality":"premium","contingency_pct":10,"profit_pct":20,"region":"northeast"}'
```

Or with Python:

```python
import requests

files = {'file': open('bathroom.jpg', 'rb')}
data = {
    'project_type': 'bathroom',
    'description': 'Tile shower install',
    'options': json.dumps({
        'quality': 'premium',
        'contingency_pct': 10,
        'profit_pct': 20,
        'region': 'northeast'
    })
}
headers = {'Authorization': f'Bearer {token}'}

response = requests.post(
    'https://api.estimategenie.net/v1/quotes',
    files=files,
    data=data,
    headers=headers
)
```

## Notes

- All options are optional; system uses sensible defaults
- Options are stored in the quote record for audit purposes
- Material and labor line items show the adjusted rates in their details
- The breakdown in `total_cost` clearly separates profit and contingency
