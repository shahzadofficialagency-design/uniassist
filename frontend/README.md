# UniAssist Frontend

React + Vite + Tailwind CSS v3 (JavaScript) frontend for UniAssist — the multilingual student portal + AI admissions & fee chatbot for The Islamia University of Bahawalpur.

## Run

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173 — /api is proxied to http://localhost:8000
npm run build   # production build in dist/
```

The FastAPI backend must be running on port 8000 (see project root README / docker-compose.yml).

## Theme

Derived from the IUB logo: navy `#180F43`, navy-light `#2A2160`, gold `#C9A227`, gold-light `#D5BB8B`, background `#F7F6FB`. Dark mode via the `class` strategy (toggle in the navbar). English UI uses Inter; Urdu mode switches `document.dir` to `rtl` and uses Noto Nastaliq Urdu.
