# Style Guide - Lucid Bots Design System

## Design Tokens

### Color Palette

#### Primary Colors (Website Analysis)

**Background System:**
- **Primary Dark Background:** `rgba(18, 18, 20, 1)` - Main page background
- **Glass/Overlay Background:** `rgba(18, 18, 20, 0.80)` - Navigation and overlay elements
- **Backdrop Blur:** 15px blur effect for glass morphism

**Brand Colors (Inferred from Analysis):**
- **Night:** Primary dark color for backgrounds and text
- **Seasalt:** Light/neutral color for contrast elements

#### Mobile App Color System (From Codebase Analysis)

**Interactive States:**
- **White Base:** `#fff` - Primary text and icons
- **White Transparent:** `rgba(255, 255, 255, 0.1)` - Background for interactive elements  
- **White Border:** `rgba(255, 255, 255, 0.2)` - Subtle borders and dividers

**Status Colors:**
- **Error/Stop State:** `#FF0000` - Critical actions and error states
- **Primary Blue:** `#0076FE` - Primary brand color for positive actions
- **Secondary Blue:** `#33E2FF` - Accent color for gradients and highlights

**Neutral Colors:**
- **Black Overlay:** `rgba(0, 0, 0, 0.5)` - Modal backgrounds
- **Glass Background:** `rgba(0, 0, 0, 0.9)` - Panel backgrounds
- **Gray Border:** Border colors for neutral elements (from gray-100 Tailwind class)

### Typography

#### Font Stack (Website)
- Primary font family not explicitly specified in extracted data
- Likely uses system font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`

#### Typography Scale (From Component Analysis)

**Font Sizes:**
- **Small:** `text-xs` (12px) - Secondary information, units
- **Medium:** `text-sm` (14px) - Body text, labels  
- **Base:** `text-md` (16px) - Primary interface text
- **Large:** `text-xl` (20px) - Section headers
- **Extra Large:** Headers and primary navigation

**Font Weights:**
- **Normal:** `font-normal` (400) - Body text
- **Medium:** `font-medium` (500) - Emphasized text
- **Semi-bold:** `font-semibold` (600) - Button labels, important information
- **Bold:** `font-bold` (700) - Section headers

**Line Height:**
- Default line heights follow Tailwind CSS standards
- Optimized for readability in technical interfaces

### Spacing System

#### Base Spacing Scale
Following Tailwind CSS spacing scale (4px base unit):

**Micro Spacing:**
- `0.5` (2px) - Fine adjustments
- `1` (4px) - Minimal spacing
- `2` (8px) - Small gaps between related elements
- `3` (12px) - Standard text spacing
- `4` (16px) - Standard component spacing

**Component Spacing:**
- `5` (20px) - Section spacing
- `6` (24px) - Large component spacing  
- `8` (32px) - Major section separation

**Layout Spacing:**
- `12` (48px) - Major layout sections
- `16` (64px) - Page-level spacing
- `20` (80px) - Extra large sections

#### Specific Measurements (From Component Analysis)

**Button Dimensions:**
- Start/Stop Button: `108px × 50px` (outer), `98px × 42px` (inner)
- Border width: `2px` outer, `1px` inner
- Border radius: `rounded-lg` (8px)

**Water Indicator:**
- Container: `240px` height, `50px` width
- Fill area: `40px` width
- Border radius: `rounded-tl-2xl rounded-bl-2xl` (12px top-left, bottom-left)
- Tick marks: Main ticks `18px` width, minor ticks `8px` width, `2px` height

### Border Radius

**Standard Radius Scale:**
- **Small:** `rounded` (4px) - Input fields, small elements
- **Medium:** `rounded-lg` (8px) - Buttons, cards
- **Large:** `rounded-2xl` (16px) - Modals, large panels
- **Custom:** `rounded-tl-2xl rounded-bl-2xl` - Specialized components like indicators

### Shadows and Effects

**Box Shadows:**
- **Subtle:** For card elevation
- **Modal:** For overlay elements
- **Focus:** For interactive states

**Backdrop Effects:**
- **Blur:** 15px blur for glass morphism effects
- **Overlay:** Semi-transparent backgrounds for modals

### Opacity and Transparency

**Standard Opacity Levels:**
- **10%:** `bg-white/10` - Subtle background tints
- **20%:** `border-white/20` - Subtle borders
- **50%:** `bg-black/50` - Modal overlays  
- **80%:** `rgba(18, 18, 20, 0.80)` - Glass morphism backgrounds
- **90%:** `bg-black/90` - Strong panel backgrounds

## Component Specifications

### Buttons

#### Start/Stop Button Component
```
Container: 108px × 50px
Border: 2px, rgba(255, 255, 255, 0.2)
Border radius: 8px
Padding: 2px

Inner button: 98px × 42px  
Background: rgba(255, 255, 255, 0.1)
Border: 1px solid (white for START, #FF0000 for STOP)
Border radius: 8px

Icon: 28px
Text: font-semibold, text-md
Active opacity: 0.7
```

#### Button States
- **Default:** White border, white text/icon
- **Stop State:** Red border (#FF0000), red text/icon  
- **Pressed:** 0.7 opacity
- **Disabled:** Reduced opacity, non-interactive

### Data Visualization

#### Water Indicator Component
```
Container: 240px height, 50px width
Border: 1.5px, gray-100
Border radius: Top-left and bottom-left 16px
Padding: 16px (top/bottom), 8px (left)

Fill gradient: Linear from #0076FE to #33E2FF
Fill area: 40px width
Fill radius: 12px (bottom-left), conditional top-left

Tick marks: 25 total
- Major ticks (every 5th): 18px width
- Minor ticks: 8px width  
- All ticks: 2px height, gray-100 color
```

#### Stats Overlay Component
```
Overlay: Full screen, rgba(0, 0, 0, 0.5)
Panel: Top 80px, left/right 16px, max-width 448px
Background: rgba(0, 0, 0, 0.9)
Border: 1px rgba(255, 255, 255, 0.2)
Border radius: 16px
Padding: 24px

Header: 24px font size, bold, white
Stats items: Border-bottom rgba(255, 255, 255, 0.1)
Labels: text-sm, gray-400
Values: text-sm, font-medium, white
Units: text-xs, gray-400
```

### Animation and Transitions

#### Website Animations (From Analysis)
- **Navigation hover:** 0.4s ease-in-out
- **Marquee scroll:** 70s linear infinite
- **Dropdown rotation:** 180 degrees
- **Button hover:** 4px horizontal translation

#### Mobile App Interactions
- **Button press:** activeOpacity 0.7
- **Modal transitions:** Standard iOS/Android modal animations
- **Data updates:** 1-second intervals for real-time stats

### Accessibility

#### Color Contrast
- All text maintains WCAG AA compliance
- Critical actions (START/STOP) use high contrast ratios
- Status colors provide sufficient contrast against dark backgrounds

#### Touch Targets
- Minimum 44px touch targets for mobile interfaces
- Adequate spacing between interactive elements
- Clear focus states for navigation

#### Typography
- Minimum 14px font sizes for body text
- Clear hierarchy with sufficient size differences
- High contrast between text and backgrounds

## Layout System

### Grid System
- Based on CSS Flexbox and CSS Grid
- Responsive breakpoints following standard mobile-first approach
- Consistent gutters and spacing throughout

### Breakpoints (From Website Analysis)
- **Mobile:** 479px and below
- **Mobile Landscape:** 480px - 767px  
- **Tablet:** 768px - 991px
- **Desktop:** 992px and above

### Component Layout Patterns
- **Card-based layouts** for modular content organization  
- **Overlay systems** for additional information and controls
- **Progressive disclosure** to manage information complexity
- **Responsive component sizing** for cross-platform compatibility

This style guide provides the technical foundation for implementing consistent design patterns across all Lucid Bots applications and touchpoints.