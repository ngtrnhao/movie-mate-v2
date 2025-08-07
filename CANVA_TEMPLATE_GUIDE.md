# Canva Template Guide - Movie Recommendation System Presentation

## 🎨 Template Setup Instructions

### 1. Khởi tạo Presentation

```
1. Truy cập canva.com
2. Chọn "Create a design" → "Presentation"
3. Search template: "Tech Startup Presentation" hoặc "Modern Business"
4. Chọn template có:
   - Dark background với accent colors
   - Clean, minimal design
   - Tech-oriented layout
```

### 2. Color Palette Setup

```
Primary Colors:
• Navy Blue: #1e3a8a (Chủ đạo - 60%)
• Orange: #ea580c (Nhấn mạnh - 10%)
• Light Gray: #f1f5f9 (Background - 20%)
• Dark Gray: #334155 (Text - 10%)

Usage Guide:
• Headers: Navy Blue
• Highlights: Orange
• Body text: Dark Gray
• Backgrounds: Light Gray hoặc White
```

---

## 📄 SLIDE-BY-SLIDE TEMPLATES

### 🎯 SLIDE 1: Title Slide Template

**Canva Elements to Use:**

```
Background: Dark gradient (Navy → Darker Navy)
Title Area: Center-aligned
  ├── Main Title: "MOVIE RECOMMENDATION SYSTEM"
  │   Font: Montserrat, Bold, 36px, White
  ├── Subtitle: "Hệ Thống Gợi Ý Phim Thông Minh"
  │   Font: Open Sans, Light, 20px, Light Gray
  └── Decorative: Movie reel icon (từ Elements → Icons)

Bottom Section: Key highlights boxes
  ├── Box 1: "2M+ Movies"
  ├── Box 2: "AI-Powered"
  └── Box 3: "Real-time"
```

**Canva Instructions:**

1. Add Rectangle với rounded corners làm background boxes
2. Search "movie reel" trong Elements để add icon
3. Use "Glow" effect cho title text
4. Add subtle "Drop shadow" cho boxes

---

### 🏗️ SLIDE 2: Architecture Diagram Template

**Layout Structure:**

```
┌─────────────────────────────────────────────┐
│              SYSTEM ARCHITECTURE            │
├─────────────┬─────────────┬─────────────────┤
│  FRONTEND   │   BACKEND   │ EXTERNAL APIS   │
│             │             │                 │
│ React 18    │ Django 4.0  │ TMDB API        │
│ Redux       │ PostgreSQL  │ IMDB API        │
│ Tailwind    │ Redis       │ PayPal          │
│ TypeScript  │ Elasticsearch│                │
└─────────────┴─────────────┴─────────────────┘
```

**Canva Elements:**

```
Boxes: Use "Rectangle" với different colors
├── Frontend Box: Light Blue (#dbeafe)
├── Backend Box: Light Orange (#fed7aa)
└── External Box: Light Gray (#f1f5f9)

Icons: Search trong Elements
├── React: "React logo"
├── Django: "Python logo"
├── Database: "Database icon"
└── API: "Cloud connection icon"

Arrows: Use "Line" tool với arrow heads
├── Bidirectional arrows giữa Frontend-Backend
└── Unidirectional arrows từ Backend đến External
```

**Step-by-step:**

1. Create 3 main rectangles với rounded corners
2. Add tech stack text trong mỗi box
3. Search và add relevant icons
4. Connect với arrows using Line tool
5. Add subtle shadows cho depth

---

### 🤝 SLIDE 3: Collaborative Filtering Template

**Visual Layout:**

```
┌──────────────┬────────────────────────────────┐
│   DIAGRAM    │         EXPLANATION            │
│              │                                │
│ User Matrix  │ • User-based similarity        │
│ ┌─────────┐  │ • Cosine similarity formula    │
│ │ A B C   │  │ • MovieLens 25M dataset        │
│ │ 1 4 5 2 │  │ • 95% mapping accuracy         │
│ │ 2 ? 3 4 │  │                                │
│ │ 3 2 5 ? │  │                                │
│ └─────────┘  │                                │
└──────────────┴────────────────────────────────┘
```

**Canva Implementation:**

```
Left Side: User-Item Matrix
├── Create Table using "Table" element
├── Fill with sample ratings (1-5 stars)
├── Highlight missing values với "?"
└── Add color coding: Green (high), Red (low)

Right Side: Algorithm Steps
├── Numbered list với custom icons
├── Formula box với monospace font
├── Dataset statistics trong callout boxes
└── Performance metrics với progress bars
```

**Visual Elements:**

1. **Matrix Table**: Elements → Tables → Grid table
2. **Star Icons**: Elements → Icons → "star rating"
3. **Formula**: Text box với Courier New font
4. **Callouts**: Elements → Shapes → Speech bubbles

---

### 📝 SLIDE 4: Content-Based Filtering Template

**Split Layout Design:**

```
┌─────────────────┬───────────────────────────────┐
│   MOVIE FEATURES│         SIMILARITY CALC       │
│                 │                               │
│ ┌─────────────┐ │ TF-IDF Vectorization:         │
│ │ Movie A     │ │ ┌─────────────────────────┐   │
│ │ • Action    │ │ │ Movie A: [0.8,0.2,0.5] │   │
│ │ • Nolan     │ │ │ Movie B: [0.7,0.1,0.6] │   │
│ │ │ Batman"   │ │ │ Similarity: 0.94       │   │
│ └─────────────┘ │ └─────────────────────────┘   │
│ ┌─────────────┐ │                               │
│ │ Movie B     │ │ Feature Weights:              │
│ │ • Action    │ │ • Genres: 40%                 │
│ │ │ Nolan     │ │ • Cast: 30%                   │
│ │ │ "Dark"    │ │ • Text: 30%                   │
│ └─────────────┘ │                               │
└─────────────────┴───────────────────────────────┘
```

**Canva Elements:**

```
Movie Cards:
├── Rectangle với rounded corners
├── Movie title trong header
├── Feature bullets với icons
└── Genre tags như small rectangles

Similarity Calculation:
├── Code-style box với monospace font
├── Progress bar cho similarity score
└── Pie chart cho feature weights
```

---

### 🔀 SLIDE 5: Hybrid Approach Template

**Flow Diagram:**

```
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│Collaborative│    │     HYBRID      │    │    Final     │
│ Filtering   │───►│   ENSEMBLE      │───►│Recommendation│
│   Score     │    │                 │    │              │
└─────────────┘    │  α×CF + β×CB   │    └──────────────┘
┌─────────────┐    │     + γ×Pop     │
│Content-Based│───►│                 │
│ Filtering   │    │  Dynamic        │
│   Score     │    │  Weighting      │
└─────────────┘    └─────────────────┘
┌─────────────┐
│ Popularity  │───►
│   Score     │
└─────────────┘
```

**Canva Implementation:**

1. **Boxes**: 3 input boxes + 1 hybrid box + 1 output box
2. **Arrows**: Directional arrows showing flow
3. **Formula**: Mathematical formula trong hybrid box
4. **Weights**: Dynamic weighting examples trong callout
5. **Colors**: Different colors cho mỗi component

---

### 👥 SLIDE 6: Use Cases Template

**Grid Layout (2x3):**

```
┌─────────────┬─────────────┬─────────────┐
│ ANONYMOUS   │ REGISTERED  │  PREMIUM    │
│    USER     │    USER     │    USER     │
│ ┌─────────┐ │ ┌─────────┐ │ ┌─────────┐ │
│ │  Browse │ │ │Personal │ │ │Advanced │ │
│ │  Search │ │ │Reviews  │ │ │Features │ │
│ │Register │ │ │Ratings  │ │ │Priority │ │
│ └─────────┘ │ └─────────┘ │ └─────────┘ │
├─────────────┼─────────────┼─────────────┤
│ MODERATOR   │    ADMIN    │  EXTERNAL   │
│             │             │   SYSTEM    │
│ ┌─────────┐ │ ┌─────────┐ │ ┌─────────┐ │
│ │Moderate │ │ │Analytics│ │ │API Sync │ │
│ │Spoiler  │ │ │Manage   │ │ │Payments │ │
│ │Reports  │ │ │Users    │ │ │Emails   │ │
│ └─────────┘ │ └─────────┘ │ └─────────┘ │
└─────────────┴─────────────┴─────────────┘
```

**Canva Elements:**

```
User Cards:
├── Rectangle với border radius
├── User icon trong header (Elements → Icons → "user")
├── Feature list như bullets
└── Role-based color coding

Icons for each role:
├── Anonymous: "user" icon
├── Registered: "user-check" icon
├── Premium: "crown" icon
├── Moderator: "shield" icon
├── Admin: "settings" icon
└── External: "cloud" icon
```

---

### 🗄️ SLIDE 7: Database Design Template

**Entity Relationship Diagram:**

```
   ┌─────────────┐
   │    User     │
   │─────────────│
   │ id (PK)     │
   │ username    │◄──┐
   │ email       │   │
   │ role        │   │
   └─────────────┘   │
                     │
   ┌─────────────┐   │   ┌─────────────┐
   │   Movie     │   │   │MovieReview  │
   │─────────────│   │   │─────────────│
   │ id (PK)     │◄──┼──►│ id (PK)     │
   │ title       │   │   │ user_id(FK) │
   │ imdb_id     │   │   │ movie_id(FK)│
   │ tmdb_id     │   └───│ rating      │
   └─────────────┘       │ content     │
         │               └─────────────┘
         │
   ┌─────────────┐
   │ MovieRating │
   │─────────────│
   │ id (PK)     │
   │ movie_id(FK)│
   │ imdb_rating │
   │ tmdb_rating │
   └─────────────┘
```

**Canva Implementation:**

```
Entity Boxes:
├── Rectangle với solid border
├── Header với entity name (bold)
├── Field list với datatypes
└── Primary Keys highlighted với yellow

Relationships:
├── Lines connecting entities
├── "1" và "N" labels cho cardinality
└── Foreign Key indicators với "FK"

Colors:
├── Entities: Light blue (#dbeafe)
├── Primary Keys: Yellow highlight
└── Foreign Keys: Orange text
```

**Step-by-step:**

1. Create rectangles cho mỗi entity
2. Add text lists cho fields
3. Highlight primary keys với yellow background
4. Draw relationship lines với Line tool
5. Add cardinality labels (1, N)

---

### ✅ SLIDE 8: Summary Template

**Achievement Showcase:**

```
┌─────────────────────────────────────────────────┐
│              COMPLETED FEATURES                 │
├─────────────┬─────────────┬─────────────────────┤
│RECOMMENDATION│  MODERATION │   PERFORMANCE       │
│    ENGINE    │   SYSTEM    │  OPTIMIZATION       │
│              │             │                     │
│ ✅ Collab.   │ ✅ Spoiler  │ ✅ <2s Response     │
│    Filtering │    Detection│ ✅ 2M+ Movies       │
│ ✅ Content   │ ✅ Smart    │ ✅ Real-time        │
│    Based     │    Queue    │    Search           │
│ ✅ Hybrid    │ ✅ Learning │ ✅ Smart Cache      │
│    Approach  │    System   │                     │
└─────────────┴─────────────┴─────────────────────┘

📊 IMPACT METRICS:
• 23% ↑ User Engagement  • 15% ↑ Accuracy
• 75% ↑ Performance      • 90% ↓ Spoiler Issues
```

**Canva Elements:**

```
Progress Cards:
├── 3 column layout với equal spacing
├── Feature lists với checkmark icons
├── Progress bars cho completion status
└── Metric callouts với arrow icons

Visual Indicators:
├── Checkmarks: Elements → Icons → "checkmark"
├── Progress bars: Elements → Charts → Progress bar
├── Arrows: Elements → Icons → "arrow up"
└── Numbers: Large, bold font với accent color
```

---

## 🎯 ANIMATION GUIDE

### Entrance Animations (Subtle & Professional):

```
Text Elements:
├── "Fade in" (duration: 0.5s)
├── "Rise up" for bullet points
└── "Typewriter" for code/formulas

Diagrams:
├── "Draw" for flowcharts
├── "Scale in" for boxes
└── "Slide in" for arrows

Charts/Graphs:
├── "Draw" for progress bars
├── "Pop in" for data points
└── "Wipe" for reveals
```

### Slide Transitions:

```
Recommended:
├── "Slide" (professional)
├── "Fade" (subtle)
└── "Push" (dynamic but not distracting)

Avoid:
├── "Flip" (too flashy)
├── "Cube" (distracting)
└── "Dissolve" (too slow)
```

---

## 📱 EXPORT & SHARING

### Export Settings:

```
Format Options:
├── PDF: Best for consistency across devices
├── PowerPoint: If further editing needed
└── PNG: Individual slides for social media

Quality Settings:
├── Standard: For email sharing (smaller file)
├── HD: For presentation screens
└── Print: For handouts
```

### Presentation Day Checklist:

```
Technical Prep:
□ Test slides on presentation screen
□ Export backup as PDF
□ Download Canva app (offline access)
□ Have presenter notes ready

Design Final Check:
□ All text readable from back of room
□ Images high resolution
□ Animations work smoothly
□ Slide numbers visible
□ Consistent font sizes
```

---

## 🔧 TROUBLESHOOTING

### Common Canva Issues:

```
Slow Loading:
├── Reduce image sizes
├── Limit animations per slide
└── Use Canva's compressed images

Font Problems:
├── Stick to Canva's font library
├── Upload custom fonts if needed
└── Have backup font choices

Export Issues:
├── Check internet connection
├── Try different export formats
└── Download slides individually if bulk fails
```

### Professional Tips:

```
Design Consistency:
├── Create color palette once, reuse
├── Set up master slide với common elements
├── Use grid lines for alignment
└── Maintain consistent spacing

Content Optimization:
├── Maximum 6 lines of text per slide
├── Use high contrast colors
├── Test readability on mobile
└── Include slide numbers for navigation
```

---

## 📚 ADDITIONAL RESOURCES

### Canva Learning Resources:

- Canva Design School: design.canva.com
- Template Marketplace: canva.com/templates
- Color Palette Generator: colors.canva.com
- Icon Library: canva.com/icons

### Tech Presentation Inspiration:

- Apple Keynote styles
- Google I/O presentation designs
- Microsoft Build conference slides
- Tech startup pitch decks

### Professional Presentation Guidelines:

- Guy Kawasaki's 10/20/30 rule
- Nancy Duarte's presentation principles
- Seth Godin's presentation philosophy
- TED Talk design standards
