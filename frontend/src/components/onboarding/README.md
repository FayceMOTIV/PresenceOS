# Brand Onboarding Wizard

A simplified 5-step wizard component for brand onboarding in PresenceOS.

## Component: BrandOnboardingWizard

### Features

- 5-step wizard with progress tracking
- Collects essential brand information:
  - Brand name
  - Business type (restaurant, ecommerce, saas, service, personal)
  - Tone of voice (chaleureux, premium, fun, professionnel, inspirant)
  - Target audience
  - Website URL (optional)
- Beautiful UI with animations (framer-motion)
- Dark theme compatible
- Single API call to update both brand and voice settings

### Usage

```tsx
import { BrandOnboardingWizard } from "@/components/onboarding/BrandOnboardingWizard";

function MyOnboardingPage() {
  const handleComplete = (brandData) => {
    console.log("Brand onboarding complete:", brandData);
    // Navigate to dashboard or next step
    router.push("/dashboard");
  };

  return (
    <BrandOnboardingWizard
      brandId="your-brand-uuid-here"
      onComplete={handleComplete}
    />
  );
}
```

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `brandId` | `string` | Yes | The UUID of the brand to onboard |
| `onComplete` | `(brandData: any) => void` | Yes | Callback function called when onboarding is complete with the updated brand data |

### Backend Integration

The wizard uses the new `/brands/{brand_id}/onboard` endpoint which:

1. Updates brand name, type, description, and website URL
2. Maps the selected tone to appropriate voice slider values
3. Sets target persona from the audience description
4. Updates custom instructions on the brand voice
5. Returns the complete updated brand with voice settings

### Tone Mappings

The wizard maps friendly tone names to specific voice configurations:

- **Chaleureux**: Formal=30, Playful=60, Bold=40, Emotional=80
- **Premium**: Formal=80, Playful=20, Bold=60, Emotional=40
- **Fun**: Formal=10, Playful=90, Bold=70, Emotional=60
- **Professionnel**: Formal=80, Playful=30, Bold=50, Emotional=30
- **Inspirant**: Formal=40, Playful=50, Bold=70, Emotional=80

### Example: Replace Existing Onboarding Step

You can use this wizard as a replacement for the chat-based onboarding:

```tsx
// In /app/onboarding/page.tsx
import { BrandOnboardingWizard } from "@/components/onboarding/BrandOnboardingWizard";

// Replace the chat step with:
{currentStep === 1 && (
  <BrandOnboardingWizard
    brandId={brandId}
    onComplete={(brandData) => {
      // Move to next step (e.g., platforms)
      setCurrentStep(2);
      localStorage.setItem("onboarding_step", "2");
    }}
  />
)}
```

### Styling

The wizard uses the PresenceOS design system:
- `glass-card` for the main container
- `bg-background`, `text-foreground` for theming
- `bg-primary`, `text-muted-foreground` for accents
- Consistent with other dashboard components
