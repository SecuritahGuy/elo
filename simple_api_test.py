#!/usr/bin/env python3
"""
Simple API test to verify FastAPI is working
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="NFL Elo API Test")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "NFL Elo API Test", "status": "running"}

@app.get("/api/test")
async def test():
    return {"message": "API test endpoint working", "status": "success"}

if __name__ == "__main__":
    print("🚀 Starting simple API test server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
