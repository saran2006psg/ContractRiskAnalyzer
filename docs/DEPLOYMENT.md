# 🚀 Deployment and Hosting Guide

This guide explains how to host and deploy the **AI Contract Risk Scanner** in a production environment. 

---

## 📋 Production Architecture Overview

In a production environment, the system is split into two main parts:

1.  **Frontend (React/Vite):** Compiled into static HTML/JS/CSS. Can be hosted on any static hosting provider (e.g., Vercel, Netlify, Cloudflare Pages) for free/low cost.
2.  **Backend (FastAPI):** A Python web server that runs the extraction, embedding, and reasoning logic. Because it loads `PyTorch` and `SentenceTransformers` locally, **the hosting server needs at least 2GB of RAM** (4GB recommended). It can be hosted on a VPS (DigitalOcean, AWS EC2) or a PaaS (Render, Railway).

```
[ Client Browser ] 
        │
        ├──► Requests Static Assets ──────► [ Vercel / Netlify (Frontend) ]
        │
        └──► API Requests (HTTPS) ────────► [ Render / VPS (FastAPI Backend) ]
                                                    │
                                                    ├──► Query Vectors ──► [ Pinecone Cloud ]
                                                    ├──► LLM Inference ──► [ Groq API ]
                                                    └──► Chat History ───► [ SQLite / Postgres ]
```

---

## 🐳 Option 1: Dockerized Deployment (Recommended for VPS)

Using a Virtual Private Server (VPS) like **DigitalOcean**, **Linode**, or **AWS EC2** is the most cost-effective method for running PyTorch models.

### 1. Create the Docker Configuration Files

Create these files in your project root:

#### `Dockerfile.backend`
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (required for PyMuPDF/EasyOCR)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY ./backend ./backend
COPY ./data ./data

EXPOSE 8000

CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### `Dockerfile.frontend`
```dockerfile
# Step 1: Build the React application
FROM node:18-alpine AS build
WORKDIR /app
COPY ./frontend/package*.json ./
RUN npm install
COPY ./frontend/ .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Step 2: Serve with Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Copy custom nginx config to handle React SPA routing
COPY ./frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### `frontend/nginx.conf`
```nginx
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
}
```

#### `docker-compose.yml`
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - backend-data:/app/backend/data
    environment:
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GROQ_MODEL=${GROQ_MODEL}
      - OCR_ENABLED=true
    restart: always

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      args:
        - VITE_API_BASE_URL=https://your-backend-domain.com
    ports:
      - "80:80"
    restart: always
    depends_on:
      - backend

volumes:
  backend-data:
```

### 2. Deploy on VPS
1. SSH into your VPS.
2. Install Docker and Docker Compose:
   ```bash
   sudo apt update && sudo apt install docker.io docker-compose -y
   ```
3. Clone your repository.
4. Create a `.env` file with your production API keys.
5. Run the services:
   ```bash
   docker-compose up -d --build
   ```

---

## ☁️ Option 2: Fully Managed Cloud (PaaS)

If you don't want to manage a server, you can use managed cloud services.

### Part A: Deploying the Backend on **Render** (or **Railway**)

> ⚠️ **Important:** Do not use the free tier of Render for the backend. The free tier has 512MB RAM, which will crash when loading the `SentenceTransformers` PyTorch model. Select the **Starter** tier (2GB RAM) or higher.

1. Create a new **Web Service** on [Render](https://render.com/).
2. Connect your GitHub repository.
3. Configure the following settings:
   *   **Runtime:** `Python 3`
   *   **Build Command:** `pip install -r requirements.txt`
   *   **Start Command:** `python -m uvicorn backend.api:app --host 0.0.0.0 --port $PORT`
4. Add a **Persistent Disk** (under the Disk section in Render):
   *   **Mount Path:** `/app/backend/data` (This ensures your SQLite chat database doesn't get wiped out when the server restarts).
5. Add the following **Environment Variables**:
   *   `PINECONE_API_KEY` = `your_pinecone_key`
   *   `GROQ_API_KEY` = `your_groq_key`
   *   `GROQ_MODEL` = `llama-3.3-70b-versatile`
   *   `OCR_ENABLED` = `true`
6. Click **Deploy**. Render will build and host your backend (e.g., `https://contract-analyzer-backend.onrender.com`).

---

### Part B: Deploying the Frontend on **Vercel** (or **Netlify**)

Vercel is free and optimized for hosting React/Vite apps.

1. Sign up on [Vercel](https://vercel.com/) and connect your GitHub repository.
2. Choose **Create New Project** and select your repository.
3. Configure the build:
   *   **Framework Preset:** `Vite`
   *   **Root Directory:** `frontend`
   *   **Build Command:** `npm run build`
   *   **Output Directory:** `dist`
4. Add the **Environment Variable**:
   *   `VITE_API_BASE_URL` = `https://your-backend-url-on-render.com` (Use the URL generated in Part A).
5. Click **Deploy**. Vercel will build and serve your app.

---

## 🔒 Production Security and CORS Configuration

When deploying the backend on a different domain than the frontend, you must configure **CORS (Cross-Origin Resource Sharing)**.

Open [backend/api.py](file:///d:/STUDY/ContractRiskAnalyzer/backend/api.py) and verify the CORS middleware configuration. Ensure it permits requests from your production frontend URL:

```python
# In backend/api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-frontend-domain.vercel.app",  # Add your production domain here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Post-Deployment Ingestion

Once the backend is live, you must populate the production Pinecone database (if you are using a new production Pinecone index):

1. Open a terminal in the production environment.
2. Run the ingestion script:
   ```bash
   python backend/scripts/ingest_pipeline.py
   ```
This will embed and index the 9,447 clauses in your production Pinecone database.
