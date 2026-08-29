# ClusterCloud Web UI

Premium customer-facing dashboard for ClusterCloud distributed computing platform.

## Features

- **Landing Page** - Clean, modern hero with product messaging
- **Dashboard** - At-a-glance view of jobs, balance, and network health
- **Build My Cloud** - Guided 3-step workflow for creating workloads
- **Jobs Monitor** - Real-time job tracking with progress indicators
- **Network View** - Available compute nodes and capacity
- **Balance Tracker** - CLSTR economic transactions

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Icon library

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Environment Variables

Copy `.env.local.example` to `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── app/                    # Next.js pages (App Router)
│   ├── page.tsx           # Landing page
│   ├── dashboard/         # Customer dashboard
│   ├── build/             # Workload builder flow
│   ├── jobs/              # Job list and details
│   ├── incidents/         # Incident management
│   ├── network/           # Node network view
│   └── balance/           # Economic ledger
├── components/
│   ├── ui/                # Reusable UI components
│   │   ├── Card.tsx
│   │   ├── Button.tsx
│   │   ├── Badge.tsx
│   │   └── ProgressBar.tsx
│   └── layout/            # Layout components
│       └── DashboardLayout.tsx
└── lib/
    ├── api.ts             # API client
    └── utils.ts           # Utility functions
```

## Design Principles

1. **Premium UX** - Cloud-product quality design
2. **Customer-first** - No technical jargon
3. **Feature-oriented** - Components organized by feature
4. **Real-time** - Live updates via polling
5. **Visual excellence** - Smooth animations, clear hierarchy

## API Integration

The frontend connects to the FastAPI backend at `localhost:8000`. All API calls are typed with TypeScript interfaces.

```typescript
// Example usage
import { api } from '@/lib/api';

const jobs = await api.getJobs();
const balance = await api.getBalance('customer:demo');
```

## Build for Production

```bash
npm run build
npm start
```

## Development Notes

- Auto-refreshes every 3-5 seconds for real-time updates
- Responsive design for mobile/tablet/desktop
- Accessible components with semantic HTML
- Optimistic UI updates where appropriate
