# Brand Onboarding Implementation

## Overview

This implementation adds a simplified brand onboarding system to PresenceOS with both backend API support and a beautiful frontend wizard component.

## Backend Changes

### 1. Schema Addition (`backend/app/schemas/brand.py`)

Added `BrandOnboardingRequest` schema:

```python
class BrandOnboardingRequest(BaseModel):
    """Simplified onboarding wizard payload."""
    name: str = Field(..., min_length=1, max_length=255)
    business_type: BrandType
    tone_voice: str  # "chaleureux" | "premium" | "fun" | "professionnel" | "inspirant"
    target_audience: str
    website_url: str | None = None
```

### 2. New Endpoint (`backend/app/api/v1/endpoints/brands.py`)

Added `POST /brands/{brand_id}/onboard` endpoint:

**Features:**
- Updates brand name, type, description, and website URL in one call
- Maps friendly tone names to BrandVoice slider values
- Sets target persona from audience description
- Includes custom instructions with target audience
- Returns complete BrandResponse with voice settings

**Tone Mappings:**
- **Chaleureux**: Formal=30, Playful=60, Bold=40, Emotional=80
- **Premium**: Formal=80, Playful=20, Bold=60, Emotional=40
- **Fun**: Formal=10, Playful=90, Bold=70, Emotional=60
- **Professionnel**: Formal=80, Playful=30, Bold=50, Emotional=30
- **Inspirant**: Formal=40, Playful=50, Bold=70, Emotional=80

**Authentication:**
- Uses `CurrentUser` dependency (requires auth token)
- Validates brand ownership via `get_brand` helper

## Frontend Changes

### 1. API Client (`frontend/src/lib/api.ts`)

Added `onboard` method to `brandsApi`:

```typescript
onboard: (id: string, data: any) => api.post(`/brands/${id}/onboard`, data)
```

### 2. Wizard Component (`frontend/src/components/onboarding/BrandOnboardingWizard.tsx`)

A complete 5-step wizard with:

**Step 1: Brand Name**
- Text input for brand name
- Store icon and clear instructions

**Step 2: Business Type**
- Visual grid of business types with emoji icons
- Options: Restaurant, E-commerce, SaaS, Service, Personal

**Step 3: Tone of Voice**
- Selection of 5 tone options with descriptions
- Visual feedback with checkmarks

**Step 4: Target Audience**
- Textarea for detailed audience description
- Placeholder examples

**Step 5: Website URL (Optional)**
- URL input with validation
- Clear indication that it's optional

**Features:**
- Animated transitions with framer-motion
- Progress bar at the top showing completion %
- Back/Next navigation with validation
- Error handling and loading states
- Dark theme compatible
- Responsive design
- Uses PresenceOS design system (glass-card, rounded-2xl, etc.)

## File Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── brands.py                    # Added onboard_brand endpoint
│   └── schemas/
│       └── brand.py                     # Added BrandOnboardingRequest schema

frontend/
├── src/
│   ├── components/onboarding/
│   │   ├── BrandOnboardingWizard.tsx   # Main wizard component
│   │   ├── README.md                    # Component documentation
│   │   └── index.ts                     # Export file
│   ├── app/(dashboard)/test-onboarding/
│   │   └── page.tsx                     # Test page for wizard
│   └── lib/
│       └── api.ts                       # Added onboard API method
```

## Usage Example

### Simple Integration

```tsx
import { BrandOnboardingWizard } from "@/components/onboarding";

function OnboardingPage() {
  const handleComplete = (brandData) => {
    console.log("Brand configured:", brandData);
    router.push("/dashboard");
  };

  return (
    <BrandOnboardingWizard
      brandId="your-brand-uuid"
      onComplete={handleComplete}
    />
  );
}
```

### Replace Chat Onboarding

You can replace the existing chat-based onboarding with this wizard:

```tsx
// In /app/onboarding/page.tsx
{currentStep === 1 && (
  <BrandOnboardingWizard
    brandId={brandId}
    onComplete={(brandData) => {
      setCurrentStep(2);
      localStorage.setItem("onboarding_step", "2");
    }}
  />
)}
```

## Testing

### Backend Testing

```bash
# Test the endpoint with curl
curl -X POST http://localhost:8000/api/v1/brands/{brand_id}/onboard \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Restaurant",
    "business_type": "restaurant",
    "tone_voice": "chaleureux",
    "target_audience": "Familles CSP+ de 30-50 ans",
    "website_url": "https://example.com"
  }'
```

### Frontend Testing

1. Visit `/test-onboarding` page
2. Ensure `brand_id` is set in localStorage
3. Complete the 5-step wizard
4. Verify the brand is updated with proper values

## API Request/Response

### Request

```json
POST /api/v1/brands/{brand_id}/onboard

{
  "name": "Family's Restaurant",
  "business_type": "restaurant",
  "tone_voice": "chaleureux",
  "target_audience": "Familles avec enfants, 30-50 ans, recherchent une cuisine familiale de qualite",
  "website_url": "https://familys-restaurant.fr"
}
```

### Response

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "name": "Family's Restaurant",
  "slug": "familys-restaurant",
  "brand_type": "restaurant",
  "description": "Family's Restaurant - restaurant",
  "website_url": "https://familys-restaurant.fr",
  "target_persona": {
    "name": "Familles avec enfants, 30-50 ans, recherchent une cuisine familiale de qualite",
    "age_range": null,
    "interests": [],
    "pain_points": [],
    "goals": []
  },
  "voice": {
    "id": "uuid",
    "brand_id": "uuid",
    "tone_formal": 30,
    "tone_playful": 60,
    "tone_bold": 40,
    "tone_emotional": 80,
    "custom_instructions": "Cible: Familles avec enfants, 30-50 ans, recherchent une cuisine familiale de qualite",
    ...
  },
  ...
}
```

## Design Decisions

1. **Single Endpoint**: Combined brand + voice updates to avoid multiple API calls from frontend
2. **Friendly Tone Names**: Used French descriptive names instead of technical slider values
3. **Optional Website**: Made website URL optional to reduce friction
4. **Progressive Validation**: Each step validates before allowing progression
5. **Persistent State**: Wizard maintains state during the flow but doesn't auto-save
6. **Dark Theme First**: Designed with dark mode as the primary theme
7. **Accessibility**: Clear labels, focus states, and keyboard navigation support

## Future Enhancements

- [ ] Add ability to go back and edit previous steps
- [ ] Add image upload for brand logo during onboarding
- [ ] Add social media handles input
- [ ] Add location/address input for local businesses
- [ ] Add preview of generated content based on tone selection
- [ ] Add onboarding analytics tracking
- [ ] Add ability to save as draft and resume later
- [ ] Add wizard completion celebration animation

## Notes

- The endpoint uses authentication (`CurrentUser` dependency)
- The wizard assumes a brand already exists (brand_id is required)
- In a full flow, you'd typically create a brand shell first, then onboard it
- The test page (`/test-onboarding`) demonstrates usage but requires setup
- All text is in French to match the existing PresenceOS interface
