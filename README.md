# Karnataka Electoral Notice Checker

A modern, high-performance web application designed for citizens to instantly check their Voter ID / EPIC number against published electoral notice records released by the **Chief Electoral Officer (CEO), Karnataka**.

---

## ✨ Features

- ⚡ **Instant EPIC Verification**: Fast, indexed database lookup (< 1s response time) covering statewide notice records.
- 📋 **Comprehensive Record Details**: Automatically extracts and displays:
  - Elector Name & Relative/Parent Name
  - Age & Gender
  - District, Assembly Constituency, Sub-district / Taluk
  - Part Number & Serial Number
  - Official Notice Category & Reason (with plain-language explanations)
- 📄 **Direct Source Link**: Direct link to the official CEO Karnataka PDF document and page number for verification.
- 🧹 **Automatic Deduplication**: Clean single-reference display for duplicate database listings.
- 📱 **Responsive & Modern UI**: Built with a clean aesthetic, accessible search input, and dark-mode ready design tokens.

---

## 🛠️ Technology Stack

- **Frontend**: React 18, Vite, Lucide Icons, Vanilla CSS
- **Backend API**: Python FastAPI, SQLAlchemy, SQLite Database Engine
- **Data Engine**: Automated PDF crawler & document parser with PyPDF2 / OCR processing

---

## 🚀 Local Development Setup

### 1. Prerequisites
- Node.js v18+
- Python 3.10+

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start FastAPI dev server
uvicorn app.main:app --reload --port 8000
```
Backend API interactive docs will be available at: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend application will run on `http://localhost:3000` (proxying `/api` requests to backend at port 8000).

---

## 📦 Building for Production

### Frontend Bundle
```bash
cd frontend
npm run build
```
The production bundle will be generated in `frontend/dist/`.

---

## 🌐 Deployment Guidelines

- **Frontend (Vercel / Netlify)**:
  - Root directory: `frontend`
  - Build command: `npm run build`
  - Output directory: `dist`

- **Backend (Render / Railway / Docker)**:
  - Deploy `backend/` as a Python Web Service.
  - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## ⚖️ Disclaimer

*This application is an independent public information lookup tool and is not officially affiliated with or operated by the Election Commission of India or the Chief Electoral Officer, Karnataka. It indexes publicly published notice documents to assist voters in verification. For official confirmation, please consult the CEO Karnataka website.*
