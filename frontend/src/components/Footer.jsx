import { Link } from 'react-router-dom'
import { useLanguage } from '../context/LanguageContext'

export default function Footer() {
  const { t } = useLanguage()
  return (
    <footer className="mt-16 bg-navy text-white">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 md:grid-cols-2 lg:grid-cols-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="grid h-12 w-12 place-items-center overflow-hidden rounded-full bg-white">
              <img src="/assets/iub-logo.jpg" alt="IUB" className="h-11 w-11 object-contain" />
            </span>
            <div>
              <p className="font-extrabold">UniAssist</p>
              <p className="text-xs text-gold-light">The Islamia University of Bahawalpur</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-white/70">
            A multilingual student portal with an AI admissions &amp; fee chatbot. Fee data: Revised Fee Structure, Fall 2025 (new intake only). Always verify with the official office.
          </p>
        </div>
        <div>
          <h4 className="font-bold text-gold-light">Quick Links</h4>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li><Link className="hover:text-white" to="/programs">{t('programs')}</Link></li>
            <li><Link className="hover:text-white" to="/fee-calculator">{t('feeCalculator')}</Link></li>
            <li><Link className="hover:text-white" to="/eligibility">{t('eligibility')}</Link></li>
            <li><Link className="hover:text-white" to="/compare">{t('compare')}</Link></li>
            <li><Link className="hover:text-white" to="/chat">{t('chat')}</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="font-bold text-gold-light">About IUB</h4>
          <img src="/images/iub-convocation.jpg" alt="IUB Convocation" className="mt-3 h-28 w-full rounded-xl object-cover" />
          <p className="mt-2 text-xs text-white/60">Main Campus, Baghdad-ul-Jadeed Campus, Bahawalpur, Punjab, Pakistan.</p>
        </div>
        <div>
          <h4 className="font-bold text-gold-light">Contact for Inquiries</h4>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li>📞 <a className="hover:text-white" href="tel:+923086827684">0308 6827684</a></li>
            <li>✉️ <a className="hover:text-white" href="mailto:saimkhan64786@gmail.com">saimkhan64786@gmail.com</a></li>
          </ul>
          <h4 className="mt-5 font-bold text-gold-light">Official Admission Queries</h4>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li>✉️ <a className="hover:text-white" href="mailto:pg.admission@iub.edu.pk">pg.admission@iub.edu.pk</a> (PG admissions)</li>
            <li>✉️ <a className="hover:text-white" href="mailto:admission@iub.edu.pk">admission@iub.edu.pk</a></li>
            <li>📞 062-9255484 · 062-9255885 (Academics)</li>
            <li>📞 IUB Helpline: 0346-9255555 · 0347-9255555 · 062-9255580</li>
            <li>🌐 <a className="hover:text-white" href="https://www.iub.edu.pk" target="_blank" rel="noreferrer">www.iub.edu.pk</a></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10 py-4 text-center text-xs text-white/50">
        UniAssist — Final Year Project · Data sources: IUB Revised Fee Structure Fall 2025 · Eligibility &amp; deadlines: iub.edu.pk · {t('verifyNote')}
      </div>
    </footer>
  )
}
