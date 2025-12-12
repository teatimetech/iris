# IRIS Web UI Implementation Plan

## Goal

Build a modern, performant web UI for the IRIS financial advisor application with:
- **Persistent chat interface** (always visible on left/bottom)
- **Dynamic content area** (portfolio, charts, insights)
- **Modern glassmorphic design** (dark mode, gradients, animations)
- **Real-time AI responses** with streaming
- **Containerized deployment** in Docker ecosystem

## Technology Stack

### Frontend Framework
- **Next.js 14** (App Router) - React framework with SSR/SSG
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations
- **Recharts** - Data visualization for portfolio

### State Management
- **React Hooks** (useState, useEffect, useContext)
- **SWR** - Data fetching and caching

### API Integration
- REST API calls to `iris-api-gateway:8080`
- WebSocket for streaming responses (future enhancement)

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  IRIS Financial Advisor              [Profile] [Theme]  │
├──────────────────┬──────────────────────────────────────┤
│  Chat Panel      │  Content Display Area               │
│  (Left 40%)      │  (Right 60%)                        │
│                  │                                      │
│  [Chat History]  │  📊 Portfolio Overview              │
│                  │  ┌──────────────────────────────┐  │
│  User: Should I  │  │ Total Value: $125,450        │  │
│  buy NVDA?       │  │ Today's P/L: +$2,340 (+1.9%) │  │
│                  │  └──────────────────────────────┘  │
│  AI: Based on... │                                      │
│                  │  [Asset Allocation Chart]            │
│  [Input Box]     │  [Top Holdings Table]                │
│  [Send Button]   │  [Performance Graph]                 │
│                  │                                      │
└──────────────────┴──────────────────────────────────────┘
```

## Component Structure

```
/web-ui
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home page (dashboard)
│   │   └── globals.css         # Global styles
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatPanel.tsx        # Main chat container
│   │   │   ├── MessageBubble.tsx    # Individual messages
│   │   │   ├── ChatInput.tsx        # Input with send button
│   │   │   └── TypingIndicator.tsx  # "AI is thinking..."
│   │   ├── Portfolio/
│   │   │   ├── PortfolioSummary.tsx   # Total value, P/L
│   │   │   ├── AssetAllocation.tsx    # Pie chart
│   │   │   ├── HoldingsTable.tsx      # Top holdings list
│   │   │   └── PerformanceChart.tsx   # Line chart
│   │   ├── Layout/
│   │   │   ├── Header.tsx           # Top navigation
│   │   │   ├── SplitView.tsx        # Chat + Content layout
│   │   │   └── ContentArea.tsx      # Dynamic content renderer
│   │   └── ui/
│   │       ├── Card.tsx             # Glassmorphic card
│   │       ├── Button.tsx           # Animated button
│   │       └── LoadingSpinner.tsx   # Loading states
│   ├── lib/
│   │   ├── api.ts              # API client for gateway
│   │   └── types.ts            # TypeScript interfaces
│   └── hooks/
│       ├── useChat.ts          # Chat state management
│       └── usePortfolio.ts     # Portfolio data fetching
├── public/
│   └── assets/                 # Icons, images
├── Dockerfile
├── package.json
├── tsconfig.json
└── tailwind.config.ts
```

## Implementation Steps

### Phase 1: Project Setup
- [x] Create Next.js project with TypeScript
- [x] Configure Tailwind CSS with custom theme
- [x] Set up project structure
- [x] Add Framer Motion for animations

### Phase 2: Core Components
- [ ] Build ChatPanel with message history
- [ ] Create MessageBubble with animations
- [ ] Implement ChatInput with send functionality
- [ ] Add TypingIndicator for AI responses

### Phase 3: Portfolio Components
- [ ] PortfolioSummary (total value, P/L)
- [ ] AssetAllocation pie chart
- [ ] HoldingsTable with sorting
- [ ] PerformanceChart (7d, 30d, 1y views)

### Phase 4: Layout & Navigation
- [ ] Header with branding
- [ ] SplitView responsive layout
- [ ] ContentArea dynamic rendering
- [ ] Mobile responsive design

### Phase 5: API Integration
- [ ] API client for /v1/chat endpoint
- [ ] Chat state management hook
- [ ] Portfolio data mock/API
- [ ] Error handling and loading states

### Phase 6: Styling & Polish
- [ ] Glassmorphic design system
- [ ] Dark mode theme
- [ ] Smooth animations and transitions
- [ ] Responsive breakpoints

### Phase 7: Containerization
- [ ] Dockerfile for production build
- [ ] Add to docker-compose.yml
- [ ] Nginx reverse proxy setup
- [ ] Update Kubernetes manifests

## Design System

### Colors
```typescript
colors: {
  primary: {
    50: '#f0f9ff',
    500: '#3b82f6',  // Blue
    900: '#1e3a8a',
  },
  success: '#10b981',   // Green
  danger: '#ef4444',    // Red
  neutral: '#6b7280',   // Gray
}
```

### Typography
- **Headings**: Inter font, bold
- **Body**: Inter font, regular
- **Monospace**: JetBrains Mono (for numbers)

### Effects
- **Glassmorphism**: `backdrop-blur-md bg-white/10`
- **Shadows**: Soft, elevated shadows
- **Gradients**: Subtle blue-purple gradients
- **Animations**: Smooth 200-300ms transitions

## API Endpoints

### Gateway API
```typescript
POST /v1/chat
Request: { user_id: string, prompt: string }
Response: { response: string }
```

### Mock Portfolio Data (for now)
```typescript
interface Portfolio {
  totalValue: number;
  todayPL: number;
  todayPLPercent: number;
  holdings: Holding[];
  performance: PerformanceData[];
}
```

## Responsive Breakpoints

- **Mobile** (< 768px): Stacked layout, chat bottom sheet
- **Tablet** (768-1024px): 50/50 split
- **Desktop** (> 1024px): 40/60 split (chat/content)

## Performance Optimizations

1. **Code Splitting**: Dynamic imports for heavy components
2. **Image Optimization**: Next.js Image component
3. **Data Caching**: SWR for portfolio data
4. **Lazy Loading**: Charts only when visible
5. **Memoization**: React.memo for expensive renders

## Deployment

### Docker
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
RUN npm ci --production
EXPOSE 3000
CMD ["npm", "start"]
```

### Docker Compose
```yaml
iris-web-ui:
  build:
    context: ./web-ui
  ports:
    - "3000:3000"
  environment:
    - NEXT_PUBLIC_API_URL=http://iris-api-gateway:8080
  depends_on:
    - iris-api-gateway
```

## Success Criteria

✅ Clean, modern UI with glassmorphic design  
✅ Persistent chat interface  
✅ Real-time AI responses  
✅ Dynamic portfolio visualization  
✅ Fully responsive (mobile, tablet, desktop)  
✅ < 3s initial page load  
✅ Smooth 60fps animations  
✅ Containerized and integrated with existing services
