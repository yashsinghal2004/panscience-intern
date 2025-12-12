# RAG Frontend

Next.js frontend for the RAG Document Q&A application.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.local.example .env.local
```

Edit `.env.local` and set:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Features

- Upload PDF or text files
- Paste text directly
- Ask questions about ingested documents
- View answer with source citations
- See statistics (total chunks)

## Build for Production

```bash
npm run build
npm start
```











