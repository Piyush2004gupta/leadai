# LeadAgent SaaS — Deploy Guide

## Structure
```
saas/
├── backend/          → Railway pe deploy
│   ├── main.py       ← FastAPI server
│   ├── agents.py     ← Scraper + Analyzer + Writer
│   ├── requirements.txt
│   ├── Procfile
│   └── nixpacks.toml
│
└── frontend/         → Vercel pe deploy
    ├── src/
    │   ├── App.jsx
    │   ├── pages/RunPage.jsx
    │   ├── pages/LeadsPage.jsx
    │   ├── pages/StatsPage.jsx
    │   └── hooks/api.js
    ├── package.json
    └── vite.config.js
```

---

## STEP 1 — Backend: Railway Deploy

1. railway.app pe jaao → New Project → Deploy from GitHub
2. `saas/backend/` folder ko GitHub repo mein push karo
3. Railway automatically `nixpacks.toml` detect karega
4. Environment variables set karo (Railway dashboard → Variables):
   ```
   PORT=8000
   ```
5. Deploy hone ke baad Railway ek URL dega:
   ```
   https://your-app.railway.app
   ```
   Is URL ko note karo.

---

## STEP 2 — Frontend: Vercel Deploy

1. vercel.com pe jaao → New Project → GitHub se import karo
2. `saas/frontend/` folder select karo
3. Build settings:
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Dir: `dist`
4. Environment Variables add karo:
   ```
   VITE_API_URL = https://your-app.railway.app
   ```
   (Railway wala URL yahan paste karo)
5. Deploy!

---

## STEP 3 — Local Test (before deploy)

```bash
# Backend
cd saas/backend
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --port 8000

# Frontend (alag terminal)
cd saas/frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

---

## Flow (Production)

1. User browser mein Vercel URL kholta hai
2. Category + Location + WA number dalta hai
3. "RUN AGENT" dabata hai → API call Railway backend pe jaati hai
4. Backend Google Maps scrape karta hai, TinyLlama se analyze + message write karta hai
5. `wa_sender.py` generate hoti hai
6. User `wa_sender.py` download karke apne LOCAL PC pe chalata hai
7. WhatsApp window khulti hai → QR scan → 10s delay ke saath sab ko message

## NOTE: WhatsApp
Railway (server) pe WhatsApp Web nahi chal sakta — display nahi hota.
Isliye backend sirf scrape + analyze + write karta hai.
`wa_sender.py` user ke local machine pe chalta hai jahan WhatsApp Web chal sakti hai.
