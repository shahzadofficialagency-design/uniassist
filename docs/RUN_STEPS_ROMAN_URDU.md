# UniAssist chalane ke asaan steps (Roman Urdu)

Ye steps bilkul asaan rakhe hain — ek step mein sirf ek kaam hai.

## Pehle kya chahiye
1. Computer mein **Python** hona chahiye (python.org se download hota hai).
2. Computer mein **Node.js** hona chahiye (nodejs.org se download hota hai).
3. Project ka folder `uniassist` apne computer par rakhein.

## Backend chalana (pehla hissa)
1. VS Code kholein.
2. Upar menu se **File → Open Folder** karke `uniassist` folder kholein.
3. VS Code mein **Terminal → New Terminal** kholein (neeche ek khana khul jayega).
4. Terminal mein ye likh kar Enter dabayein:
   `cd backend`
5. Phir ye likh kar Enter dabayein (ye sirf pehli baar karna hai):
   `python -m venv .venv`
6. Phir ye likhein (Windows ke liye):
   `.venv\Scripts\activate`
7. Phir ye likhein (sirf pehli baar — thora time lagega):
   `pip install -r requirements.txt`
8. Ab server chalane ke liye ye likhein:
   `uvicorn app.main:app --reload --port 8000`
9. Jab `Uvicorn running` likha aaye to samjhein backend chal gaya.
   Browser mein `http://localhost:8000/docs` khol kar dekh sakte hain.

## Frontend chalana (dusra hissa)
1. VS Code mein ek **naya terminal** kholein (Terminal → New Terminal).
   Purana wala band na karein — wo chalta rahega.
2. Naye terminal mein ye likhein:
   `cd frontend`
3. Phir (sirf pehli baar):
   `npm install`
4. Phir ye likhein:
   `npm run dev`
5. Browser mein ye address kholein: `http://localhost:5173`
6. UniAssist ki website khul jayegi. 

## Login karke dekhna
- **Student:** email `student@demo.iub.edu.pk`, password `Student@123`
- **Admin:** email `admin@iub.edu.pk`, password `Admin@123`

## Chatbot se pooch kar dekhna
- `BS AI ki fee kitni hai?`
- `What is the fee of BS Computer Science?`
- `بی ایس نرسنگ کی فیس کتنی ہے؟`
- `Mere 70% marks hain, kya mein BS mein dakhla le sakta hoon?`

## Band karna ho to
- Har terminal mein ja kar **Ctrl + C** dabayein. Server band ho jayega.

## Docker wala tareeqa (agar Docker install hai)
1. Project folder mein terminal kholein.
2. Ye ek hi command likhein: `docker compose up --build`
3. Website `http://localhost:5173` par khul jayegi.
