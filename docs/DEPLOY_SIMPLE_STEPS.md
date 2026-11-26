# UniAssist ko internet par live karna — asaan steps (Roman Urdu)

**Pehle ek baat samajh lo:** website ke 2 hisse hain.
- **Frontend** (jo screen par dikhta hai) → ye **Netlify** par jayega.
- **Backend** (chatbot ka dimagh + fees ka data) → ye Netlify par **nahi** chal sakta. Ye **Render** par jayega. Dono free hain.

Agar sirf frontend Netlify par daal dein to site khul jayegi lekin chatbot aur
fees wala data **nahi chalega**. Is liye dono karna zaroori hai.
Order ye hai: **pehle GitHub repo → phir Render (backend) → phir Netlify (frontend).**

---

## Step A — GitHub par repo banana (sirf tumhara kaam, 2 minute)
1. github.com par jao (tumhara account pehle se bana hua hai: shahzadofficialagency-design).
2. Upar right corner par **+** wala nishan → **New repository**.
3. Name mein likho: `uniassist`
4. **Public** select karo.
5. Neeche "Add a README file" wala tick **OFF** rakho (bilkul khaali repo banana hai).
6. **Create repository** dabao.
7. Muse ko bas itna bolo: **"repo bana diya"** — baaki saari files main upload kar dunga.

## Step B — Backend ko Render par lagana
1. render.com par jao.
2. **Get Started / Sign In** → **GitHub** wala button dabao aur apne GitHub se login karo.
   (Password kabhi Muse ko mat dena — login tum khud apne browser mein karoge.)
3. Render puche to **New → Blueprint** select karo → apna `uniassist` repo select karo.
4. Render khud `render.yaml` file parh lega aur backend banana shuru kar dega.
5. Jab "Live" likha aaye to wahan ek link hoga jaisa: `https://uniassist-backend.onrender.com`
6. **Wo link copy karke Muse ko bhej dena** — agla step main bata dunga.
   (Note: free plan par backend 15 minute khaali rehne par so jata hai; pehla
   sawal 30–50 second le sakta hai, phir normal speed ho jati hai.)

## Step C — Frontend ko Netlify par lagana
1. netlify.com par jao → **Sign up / Log in** → **GitHub** se login karo.
2. **Add new site → Import an existing project** → GitHub → `uniassist` repo select karo.
3. Build settings Netlify khud `netlify.toml` se parh lega — kuch change nahi karna.
4. **Site settings → Environment variables** mein ek cheez add karni hai:
   - Key: `VITE_API_BASE_URL`
   - Value: Step B wala Render link + `/api` — maslan `https://uniassist-backend.onrender.com/api`
   (Ye mujhe link bhejne ke baad main dobara confirm kar dunga.)
5. **Deploy site** dabao. 1–2 minute mein tumhara Netlify link tayyar hoga,
   jaisa: `https://uniassist-xxxx.netlify.app` — **yehi link sab ko bhejna hai.** 🎉

## Masla aaye to?
Jis step par atko, usi screen ka screenshot Muse ko bhejo — wahi step theek kar dunga.
