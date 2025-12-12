# Troubleshooting: Vector Store Empty Issue

## Problem
You're seeing "Total Chunks: 3060" but queries return "no information in knowledge base". This means chunks were created but embeddings weren't added to the FAISS index.

## Root Cause
The vector store index is empty (`index.ntotal == 0`) even though chunks exist in memory. This happens when:
1. Embeddings failed to generate (NOMIC_API_KEY issue)
2. The index file is corrupted or empty
3. Embeddings were generated but not saved properly

## Solution Steps

### Step 1: Verify NOMIC_API_KEY is Set

Check your `.env` file in `backend/` directory:
```env
NOMIC_API_KEY=your_actual_api_key_here
```

**Important:** 
- No quotes around the key
- No spaces before/after the `=`
- The key should start with `nk-` (Nomic API keys)

### Step 2: Clear the Corrupted Vector Store

**Option A: Using the API endpoint (recommended)**
```bash
curl -X POST http://localhost:8000/api/v1/reset-vector-store
```

**Option B: Manual deletion**
```bash
# Windows
del backend\data\vector_store\*.index
del backend\data\vector_store\*.json

# Linux/Mac
rm backend/data/vector_store/*.index
rm backend/data/vector_store/*.json
```

### Step 3: Restart Your Backend Server

Stop your current server (Ctrl+C) and restart:
```bash
cd backend
python -m app.main
```

Watch for these log messages:
- ✅ "NOMIC_API_KEY set from configuration"
- ✅ "Embedding model initialized successfully"
- ✅ "Creating new FAISS index"

### Step 4: Re-upload Your Document

1. Go to your frontend: http://localhost:3000
2. Upload your BMW document again
3. **Watch the server logs** - you should see:
   - "Generating embeddings for X texts..."
   - "Successfully generated X embeddings"
   - "Adding embeddings to FAISS index..."
   - "Successfully added X chunks. Total vectors in index: X"

### Step 5: Verify It Works

1. Check the health endpoint:
```bash
curl http://localhost:8000/api/v1/health
```

Look for:
- `"total_vectors"` should be > 0
- `"is_synced": true` means index and chunks match

2. Try a query in the frontend

## Diagnostic Endpoints

### Check Vector Store Status
```bash
curl http://localhost:8000/api/v1/health
```

Response shows:
- `total_vectors`: Actual vectors in FAISS index
- `chunks_count`: Chunks in memory
- `is_synced`: Whether they match

### Reset Vector Store
```bash
curl -X POST http://localhost:8000/api/v1/reset-vector-store
```

## Common Error Messages

### "NOMIC_API_KEY is required but not set"
- **Fix:** Add `NOMIC_API_KEY=your_key` to `.env` file
- **Restart:** Server must be restarted after adding to `.env`

### "You have not configured your Nomic API token"
- **Fix:** Same as above - check `.env` file
- **Verify:** Check logs for "NOMIC_API_KEY set from configuration"

### "Vector store is empty: index has 0 vectors but X chunks in memory"
- **Fix:** Clear vector store and re-upload documents
- **Cause:** Previous upload failed but chunks were counted

### "No vectors were added to the index despite successful chunking"
- **Fix:** Check NOMIC_API_KEY and server logs for embedding errors
- **Action:** Re-upload after fixing API key

## Verification Checklist

- [ ] `.env` file has `NOMIC_API_KEY=your_key`
- [ ] Server restarted after adding API key
- [ ] Vector store cleared (old index deleted)
- [ ] Server logs show "Embedding model initialized successfully"
- [ ] Document re-uploaded
- [ ] Server logs show "Successfully added X chunks. Total vectors in index: X"
- [ ] Health endpoint shows `total_vectors > 0`
- [ ] Query works in frontend

## Still Not Working?

1. **Check server logs** - Look for error messages during ingestion
2. **Verify API key** - Test if your Nomic API key works:
   ```python
   import os
   os.environ["NOMIC_API_KEY"] = "your_key"
   from langchain_nomic import NomicEmbeddings
   embeddings = NomicEmbeddings(model="nomic-embed-text-v1")
   result = embeddings.embed_query("test")
   print(f"Embedding dimension: {len(result)}")
   ```
3. **Check file permissions** - Ensure the app can write to `backend/data/vector_store/`
4. **Review logs** - The enhanced logging will show exactly where it fails

## Expected Behavior After Fix

When working correctly:
- Upload shows: "File 'X.pdf' ingested successfully"
- Stats show: `total_chunks` matches `total_vectors`
- Queries return relevant answers with sources
- Health endpoint shows `is_synced: true`









