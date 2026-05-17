# PMDD Cloud Deployment Guide

This guide outlines the steps to take the PMDD platform from local Docker containers to a distributed cloud architecture.

## 1. Database Provisioning
- **Supabase (PostgreSQL)**: Create a new project. Copy the `DATABASE_URL` (ensure port 5432/6543 connection pooling).
- **Pinecone (Vector DB)**: Create a Serverless index named `pmdd-memory`, dimension 3072, metric `cosine`.
- **Redis (Upstash/Render)**: Provision a Redis cache for Celery task queuing.

## 2. Backend Deployment (Render / Fly.io / Railway)
1. Connect your GitHub repository.
2. Select the `/backend` folder or specify the `infrastructure/docker/backend.Dockerfile`.
3. Add the following Environment Variables:
   - `OPENAI_API_KEY`
   - `PINECONE_API_KEY`
   - `DATABASE_URL`
   - `REDIS_URL`
4. Deploy the FastAPI service. Note the backend public URL (e.g., `https://pmdd-api.onrender.com`).

## 3. Worker Deployment (Render / Fly.io)
1. Deploy a secondary service using the same Dockerfile.
2. Override the startup command: `celery -A backend.workers.celery_app worker --loglevel=info`
3. Ensure it has access to the same `REDIS_URL` and `DATABASE_URL`.

## 4. Frontend Deployment (Vercel)
1. Import the repository into Vercel.
2. Set the Root Directory to `frontend/`.
3. Add Environment Variable: `NEXT_PUBLIC_API_URL` pointing to your backend public URL.
4. Deploy.

## 5. Security Checklist
- Ensure CORS on the backend explicitly allows your Vercel domain.
- Rotate the `SECRET_KEY` in `backend/core/security.py`.
- Enable API rate limiting.
