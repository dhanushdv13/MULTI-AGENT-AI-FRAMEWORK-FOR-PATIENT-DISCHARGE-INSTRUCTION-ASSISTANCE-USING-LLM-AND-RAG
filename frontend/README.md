# Discharge Agent Frontend

Modern Next.js application for AI-powered medical discharge summary management.

## Features

✨ **Authentication** - Secure user registration and login
📤 **File Upload** - Drag-and-drop discharge document upload
📁 **File Management** - View and manage all uploaded documents
💬 **AI Chat** - Interactive chat with specialized agents:
  - 🏥 Bill Validator Agent (insurance & billing)
  - 🥗 Diet & Nutrition Agent
  - 💊 Medicine Price Comparison Agent
  - 📋 Discharge Summary Agent (RAG-based)

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Axios** - HTTP client for API calls
- **Framer Motion** - Smooth animations
- **CSS** - Premium glassmorphism design

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Visit `http://localhost:3000`

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── app/                    # Next.js app router pages
│   ├── login/             # Login page
│   ├── register/          # Registration page
│   └── dashboard/         # Protected dashboard
│       ├── upload/        # File upload page
│       └── files/         # File listing & detail pages
├── components/            # Reusable components
│   ├── Sidebar.tsx       # Navigation sidebar
│   └── ProtectedRoute.tsx # Auth guard
├── hooks/                # Custom React hooks
│   └── useAuth.ts       # Authentication logic
├── lib/                  # Utilities
│   └── api.ts          # Axios instance
└── types/              # TypeScript definitions
    └── index.ts
```

## Usage

### 1. Register & Login
- Create an account at `/register`
- Login at `/login`

### 2. Upload Document
- Navigate to **Upload Document**
- Drag & drop or select a file
- Add description and notes
- Submit

### 3. View Files
- Go to **All Files** to see your documents
- Click any file card to view details

### 4. Chat with AI
- In file detail view, use the chat interface
- Ask questions about:
  - Bills and insurance
  - Diet recommendations
  - Medication prices
  - General discharge info

## API Integration

The app connects to FastAPI backend endpoints:

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /uploads/` - Upload file
- `GET /uploads/` - List files
- `GET /uploads/{id}` - Get file details
- `POST /chat/{vector_id}` - Chat with file

## Design System

Premium medical-themed UI with:
- 🎨 Modern color palette (indigo, teal, amber)
- ✨ Glassmorphism effects
- 🎬 Smooth animations
- 📱 Fully responsive
- 🌙 Dark mode optimized

## Development

```bash
# Development
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

---

© 2026 Discharge Agent - AI-powered medical document management
