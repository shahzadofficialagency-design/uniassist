import { createContext, useContext, useEffect, useState } from 'react'

export const translations = {
  en: {
    home: 'Home', programs: 'Programs', compare: 'Compare', feeCalculator: 'Fee Calculator',
    eligibility: 'Eligibility', chat: 'Ask UniAssist', dashboard: 'Dashboard', profile: 'Profile',
    admin: 'Admin', login: 'Login', register: 'Register', logout: 'Logout',
    search: 'Search', searchPlaceholder: 'Search programs, e.g. BS Artificial Intelligence…',
    explorePrograms: 'Explore Programs', askChatbot: 'Ask the Chatbot',
    viewDetails: 'View Details', addToCompare: 'Compare', remove: 'Remove',
    firstSemester: '1st Semester', nextSemesters: 'Next Semesters', perSemester: 'per semester',
    duration: 'Duration', years: 'years', seats: 'Seats', level: 'Level', group: 'Group', shift: 'Shift',
    faculty: 'Faculty', department: 'Department', all: 'All', submit: 'Submit', calculate: 'Calculate',
    checkEligibility: 'Check Eligibility', yourMarks: 'Your Marks (%)', stream: 'Stream / Qualification',
    typeMessage: 'Type your question… e.g. BS AI ki fee kitni hai?',
    send: 'Send', suggestions: 'Suggested questions', sources: 'Sources',
    verifyNote: 'Please verify with the official office.',
    welcome: 'Welcome to UniAssist', tagline: 'Admissions, fees and programs — in English, Urdu and Roman Urdu.',
    announcements: 'Announcements', featured: 'Faculties at IUB', statsPrograms: 'Programs',
    statsFaculties: 'Faculties', statsDepts: 'Departments', noResults: 'No results found.',
    loading: 'Loading…', totalEstimate: 'Estimated Total', semesters: 'Semesters',
    eligiblePrograms: 'Programs you may qualify for', save: 'Save', name: 'Full Name',
    email: 'Email', phone: 'Phone', city: 'City', password: 'Password',
    matricMarks: 'Matric Marks', interMarks: 'Intermediate Marks',
  },
  ur: {
    home: 'ہوم', programs: 'پروگرامز', compare: 'موازنہ', feeCalculator: 'فیس کیلکولیٹر',
    eligibility: 'اہلیت چیک کریں', chat: 'یونی اسسٹ سے پوچھیں', dashboard: 'ڈیش بورڈ', profile: 'پروفائل',
    admin: 'ایڈمن', login: 'لاگ ان', register: 'رجسٹر', logout: 'لاگ آؤٹ',
    search: 'تلاش کریں', searchPlaceholder: 'پروگرام تلاش کریں، مثلاً بی ایس آرٹیفیشل انٹیلیجنس…',
    explorePrograms: 'پروگرامز دیکھیں', askChatbot: 'چیٹ بوٹ سے پوچھیں',
    viewDetails: 'تفصیل دیکھیں', addToCompare: 'موازنہ کریں', remove: 'ہٹائیں',
    firstSemester: 'پہلا سمسٹر', nextSemesters: 'اگلے سمسٹرز', perSemester: 'فی سمسٹر',
    duration: 'دورانیہ', years: 'سال', seats: 'نشستیں', level: 'لیول', group: 'گروپ', shift: 'شفٹ',
    faculty: 'فیکلٹی', department: 'شعبہ', all: 'تمام', submit: 'جمع کریں', calculate: 'حساب کریں',
    checkEligibility: 'اہلیت چیک کریں', yourMarks: 'آپ کے نمبر (%)', stream: 'تعلیمی سلسلہ / قابلیت',
    typeMessage: 'اپنا سوال لکھیں… مثلاً بی ایس اے آئی کی فیس کتنی ہے؟',
    send: 'بھیجیں', suggestions: 'تجویز کردہ سوالات', sources: 'ذرائع',
    verifyNote: 'براہ کرم سرکاری دفتر سے تصدیق کریں۔',
    welcome: 'یونی اسسٹ میں خوش آمدید', tagline: 'داخلہ، فیس اور پروگرامز — انگریزی، اردو اور رومن اردو میں۔',
    announcements: 'اعلانات', featured: 'آئی یو بی کی فیکلٹیز', statsPrograms: 'پروگرامز',
    statsFaculties: 'فیکلٹیز', statsDepts: 'شعبے', noResults: 'کوئی نتیجہ نہیں ملا۔',
    loading: 'لوڈ ہو رہا ہے…', totalEstimate: 'تخمینی کل فیس', semesters: 'سمسٹرز',
    eligiblePrograms: 'وہ پروگرامز جن کے لیے آپ اہل ہو سکتے ہیں', save: 'محفوظ کریں', name: 'پورا نام',
    email: 'ای میل', phone: 'فون', city: 'شہر', password: 'پاس ورڈ',
    matricMarks: 'میٹرک نمبر', interMarks: 'انٹرمیڈیٹ نمبر',
  },
}

const LanguageContext = createContext(null)

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'en')

  useEffect(() => {
    localStorage.setItem('lang', lang)
    document.documentElement.lang = lang === 'ur' ? 'ur' : 'en'
    document.documentElement.dir = lang === 'ur' ? 'rtl' : 'ltr'
  }, [lang])

  const t = (key) => translations[lang]?.[key] || translations.en[key] || key
  const isUrdu = lang === 'ur'

  return (
    <LanguageContext.Provider value={{ lang, setLang, t, isUrdu }}>
      <div className={isUrdu ? 'font-urdu' : ''}>{children}</div>
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider')
  return ctx
}
