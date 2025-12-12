# IRIS Web UI

Modern web interface for the IRIS financial advisor AI application.

## Features

- **Split-screen Layout**: Persistent chat panel + dynamic content area
- **Real-time Chat**: AI-powered financial advice with smooth animations
- **Portfolio Visualization**: Charts, tables, and performance analytics
- **Glassmorphic Design**: Modern dark theme with stunning visuals
- **Fully Responsive**: Works on desktop, tablet, and mobile

## Technology Stack

- **Next.js 14** (App Router)
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **Framer Motion** for animations

## Development

```bash
# Install dependencies
cd web-ui
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## Docker Deployment

Build and run with Docker Compose:

```bash
# From root IRIS directory
make build-web
make up

# Access at http://localhost:3000
```

## Project Structure

```
web-ui/
├── app/                   # Next.js App Router pages
│   ├── layout.tsx        # Root layout
│   ├── page.tsx          # Home page
│   └── globals.css       # Global styles
├── components/           # React components
│   ├── Chat/            # Chat components
│   ├── Portfolio/       # Portfolio visualizations
│   └── Layout/          # Layout components
├── lib/                  # Utilities
│   ├── api.ts           # API client
│   ├── types.ts         # TypeScript types
│   └── mockData.ts      # Mock portfolio data
└── public/              # Static assets
```

## Components

### Chat Components
- `ChatPanel` - Main chat container with history
- `MessageBubble` - Individual chat messages
- `ChatInput` - Input field with send button
- `TypingIndicator` - Loading animation

### Portfolio Components
- `PortfolioSummary` - Total value and P/L display
- `AssetAllocation` - Pie chart of sectors
- `PerformanceChart` - 30-day performance line chart
- `HoldingsTable` - Stock holdings table

### Layout Components
- `Header` - Top navigation bar
- `ContentArea` - Dynamic content renderer

## Styling

Uses a glassmorphic design system with:
- Dark gradient backgrounds
- Frosted glass effects (`backdrop-blur`)
- Blue-purple gradient accents
- Smooth animations and transitions

## API Integration

Connects to `iris-api-gateway` on port 8080:

```typescript
POST /v1/chat
{
  "user_id": "string",
  "prompt": "string"
}

Response:
{
  "response": "string"
}
```

## License

Part of the IRIS project.
