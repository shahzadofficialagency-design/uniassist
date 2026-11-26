"""Chat orchestration: router -> SQL tools / RAG -> answer in the user's language.

Hard rules (from the brief):
- Fees, seats, eligibility and deadlines come from the structured DB only.
- If information is not in the data, say so honestly (in the user's language)
  and point to the official office. Never invent a number or a date.
- Every factual answer carries a source citation + verification note.
"""
from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    ChatMessage, ChatSession, Deadline, PolicyDocument, Program, QueryLog,
    SpecialFeeSchedule,
)
from ..nlp.language import detect_language
from ..nlp.router import ProgramIndex, classify
from ..rag.retriever import retriever
from . import llm

VERIFY = {
    "en": "Please verify with the official university office.",
    "roman_ur": "Meharbani karke official university office se tasdeeq kar lein.",
    "mixed": "Please official university office se verify kar lein.",
    "ur": "براہ کرم یونیورسٹی کے دفتر سے تصدیق کر لیں۔",
}
NOT_FOUND = {
    "en": "Sorry, this information is not available in the data provided to me. "
          "Please contact the official university office for confirmed details.",
    "roman_ur": "Maazrat, ye maloomat mere paas mojood data mein available nahi hain. "
                "Baraye meharbani confirmed details ke liye university office se rabta karein.",
    "mixed": "Sorry, ye information mere available data mein nahi hai. "
             "Please confirmed details ke liye university office se contact karein.",
    "ur": "معذرت، یہ معلومات میرے پاس موجود ڈیٹا میں دستیاب نہیں ہیں۔ "
          "تصدیق شدہ تفصیلات کے لیے براہ کرم یونیورسٹی کے دفتر سے رابطہ کریں۔",
}
GROUP_CAVEAT = {
    "en": "Note: The official fee PDF does not define Group-A/Group-B — please confirm what each group means with the university office.",
    "roman_ur": "Note: Official fee PDF mein Group-A/Group-B ki tareef nahi di gayi — office se confirm kar lein ke har group se kya murad hai.",
    "mixed": "Note: Official fee PDF mein Group-A/Group-B define nahi hai — please office se confirm kar lein.",
    "ur": "نوٹ: سرکاری فیس پی ڈی ایف میں گروپ اے/گروپ بی کی تعریف نہیں دی گئی — براہ کرم دفتر سے تصدیق کریں۔",
}
SUGGESTIONS = {
    "en": ["What is the fee of BS Artificial Intelligence?",
           "What is the fee of BS Computer Science?",
           "Am I eligible for BS programs with 70% marks?",
           "Compare BS Computer Science and BS Software Engineering",
           "What are the AC charges?"],
    "roman_ur": ["BS AI ki fee kitni hai?",
                 "BS Computer Science ki fee kitni hai?",
                 "Mere 70% marks hain, kya mein BS mein dakhla le sakta hoon?",
                 "BS CS aur BS SE mein kya farq hai?",
                 "AC charges kitne hain?"],
    "mixed": ["BS AI ki fee kitni hai?",
              "BS Software Engineering fee please",
              "Mere 65% marks hain, eligible hoon?",
              "BS IT vs BS CS compare karein",
              "Admission ki last date kya hai?"],
    "ur": ["بی ایس آرٹیفیشل انٹیلیجنس کی فیس کتنی ہے؟",
           "بی ایس کمپیوٹر سائنس کی فیس کتنی ہے؟",
           "میرے 70 فیصد نمبر ہیں، کیا میں داخلے کے اہل ہوں؟",
           "اے سی چارجز کتنے ہیں؟"],
}


def _rs(n: int) -> str:
    return f"Rs {n:,}"


def _fee_table(program: Program) -> dict | None:
    if program.fee is None:
        return None
    f = program.fee
    return {
        "program": program.name,
        "department": program.department.name,
        "tuition_fee": f.tuition_fee,
        "other_dues": f.other_dues,
        "total_first_semester": f.total_first_semester,
        "total_next_semesters": f.total_next_semesters,
        "currency": f.currency,
        "session": f.session,
        "intake": f.intake,
        "basis": program.fee_basis,
    }


def _source_for(program: Program) -> str:
    page = program.fee.source_page if program.fee else None
    return f"Revised Fee Structure Fall 2025 (New Intake Only), IUB" + (f", p.{page}" if page else "")


def _special_notes(db: Session, program: Program) -> list[str]:
    notes = []
    base = program.name.lower()
    for sched in db.scalars(select(SpecialFeeSchedule)).all():
        targets = [t.strip().lower() for t in sched.applies_to.replace(":", ",").split(",")]
        if any(t and t in base for t in targets) or "bioinformatics" in base and "bioinformatics" in sched.applies_to.lower():
            notes.append(sched.note)
    return notes


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        programs = db.scalars(select(Program).where(Program.is_active.is_(True))).all()
        self.index = ProgramIndex(programs)

    # ---------- helpers ----------
    def _history(self, session_id: int) -> list[ChatMessage]:
        return list(self.db.scalars(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.desc()).limit(10)
        ).all())[::-1]

    def _last_program(self, history: list[ChatMessage]) -> Program | None:
        for msg in reversed(history):
            if msg.program_id:
                return self.db.get(Program, msg.program_id)
        return None

    # ---------- main entry ----------
    def handle(self, message: str, session_id: int | None, user_id: int | None) -> dict:
        start = time.perf_counter()
        if session_id is None or self.db.get(ChatSession, session_id) is None:
            session = ChatSession(user_id=user_id)
            self.db.add(session)
            self.db.flush()
            session_id = session.id
        history = self._history(session_id)
        language = detect_language(message)
        route = classify(message, self.index)

        # Follow-up resolution ("us ka deadline?", "aur is ki fee?"): reuse last program.
        context_program = self._last_program(history)
        if not route.programs and context_program is not None and route.intent in {
            "fee", "deadline", "eligibility", "program_info", "comparison",
        }:
            route.programs = [context_program]

        handler = {
            "fee": self._answer_fee,
            "deadline": self._answer_deadline,
            "eligibility": self._answer_eligibility,
            "comparison": self._answer_comparison,
            "policy": self._answer_policy,
            "program_info": self._answer_program_info,
            "greeting": self._answer_greeting,
            "out_of_scope": self._answer_out_of_scope,
        }[route.intent]
        answer, sources, fee_table, answered, program_id = handler(route, language)

        # Optional LLM rephrase (facts unchanged); templates remain the fallback.
        if answered and route.intent not in {"out_of_scope"}:
            polished = llm.rephrase(message, answer)
            if polished:
                answer = polished

        latency_ms = int((time.perf_counter() - start) * 1000)
        self.db.add(ChatMessage(session_id=session_id, role="user", content=message,
                                language=language, intent=route.intent, program_id=program_id))
        assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=answer,
                                    language=language, intent=route.intent,
                                    program_id=program_id, sources_json=sources)
        self.db.add(assistant_msg)
        self.db.add(QueryLog(user_id=user_id, question=message, language=language,
                             intent=route.intent, answered=answered, latency_ms=latency_ms))
        if program_id:
            prog = self.db.get(Program, program_id)
            if prog:
                prog.view_count += 1
        self.db.commit()
        return {
            "answer": answer, "language": language, "intent": route.intent,
            "sources": sources, "fee_table": fee_table, "session_id": session_id,
            "message_id": assistant_msg.id, "answered": answered,
            "suggestions": SUGGESTIONS[language],
        }

    # ---------- intent handlers ----------
    def _answer_greeting(self, route, language):
        text = {
            "en": "Assalam-o-Alaikum! I am UniAssist for the Islamia University of Bahawalpur. "
                  "Ask me about program fees, admissions or policies.",
            "roman_ur": "Assalam-o-Alaikum! Mein UniAssist hoon — Islamia University Bahawalpur ka "
                        "assistant. Aap mujh se kisi bhi program ki fee, dakhla ya policy ke baray "
                        "mein pooch sakte hain.",
            "mixed": "Assalam-o-Alaikum! Mein UniAssist hoon, IUB ka assistant. "
                     "Aap fee, admission ya policy ke baray mein pooch sakte hain.",
            "ur": "السلام علیکم! میں یونی اسسٹ ہوں — اسلامیہ یونیورسٹی بہاولپور کا اسسٹنٹ۔ "
                  "آپ مجھ سے کسی بھی پروگرام کی فیس، داخلے یا پالیسی کے بارے میں پوچھ سکتے ہیں۔",
        }[language]
        return text, [], None, True, None

    def _answer_out_of_scope(self, route, language):
        base = {
            "en": "I can only help with Islamia University Bahawalpur admissions, program fees and "
                  "policies. ",
            "roman_ur": "Mein sirf Islamia University Bahawalpur ke dakhle, program fees aur "
                        "policies ke baray mein madad kar sakta hoon. ",
            "mixed": "I can only help with IUB admissions, fees aur policies. ",
            "ur": "میں صرف اسلامیہ یونیورسٹی بہاولپور کے داخلوں، پروگرام فیس اور پالیسیوں کے "
                  "بارے میں مدد کر سکتا ہوں۔ ",
        }[language]
        return base + NOT_FOUND[language], [], None, False, None

    def _answer_fee(self, route, language):
        programs = [p for p in route.programs if p.fee is not None]
        if not programs:
            return NOT_FOUND[language], [], None, False, None
        if route.group_hint:
            hinted = [p for p in programs if p.group_label == route.group_hint]
            if hinted:
                programs = hinted
        primary = programs[0]
        lines: list[str] = []
        for p in programs:
            f = p.fee
            if language == "ur":
                unit = "فی پروفیشنل سال" if p.fee_basis == "professional" else "فی سمسٹر"
            else:
                unit = "per year (Prof.)" if p.fee_basis == "professional" else "per semester"
            if language == "ur":
                lines.append(
                    f"{p.name} — پہلا سمسٹر: {_rs(f.total_first_semester)} "
                    f"(ٹیوشن {_rs(f.tuition_fee)} + دیگر واجبات {_rs(f.other_dues)})، "
                    f"اگلے سمسٹرز: {_rs(f.total_next_semesters)} ({unit})۔"
                )
            elif language == "en":
                lines.append(
                    f"{p.name}: First semester {_rs(f.total_first_semester)} "
                    f"(Tuition {_rs(f.tuition_fee)} + Other dues {_rs(f.other_dues)}), "
                    f"later semesters {_rs(f.total_next_semesters)} {unit}."
                )
            else:  # roman_ur / mixed
                lines.append(
                    f"{p.name}: Pehla semester {_rs(f.total_first_semester)} "
                    f"(Tuition {_rs(f.tuition_fee)} + Other dues {_rs(f.other_dues)}), "
                    f"baad wale semesters {_rs(f.total_next_semesters)} {unit}."
                )
        if primary.group_label:
            lines.append(GROUP_CAVEAT[language])
        for note in _special_notes(self.db, primary):
            lines.append(("Note: " if language == "en" else "Note: ") + note)
        lines.append(VERIFY[language])
        sources = [_source_for(primary)]
        return "\n".join(lines), sources, _fee_table(primary), True, primary.id

    def _answer_deadline(self, route, language):
        rows = self.db.scalars(select(Deadline).order_by(Deadline.id)).all()
        if rows:
            parts = []
            for d in rows:
                when = ""
                if d.closes_on:
                    when = f" — last date: {d.closes_on.isoformat()}"
                parts.append(f"{d.title} ({d.session}){when}")
            tail = VERIFY[language]
            return "; ".join(parts) + f"\n{tail}", [f"Deadline record: {r.source}" for r in rows], None, True, \
                (route.programs[0].id if route.programs else None)
        # No deadline exists in the provided source data — answer honestly.
        extra = {
            "en": "The fee structure document (Fall 2025) does not contain admission deadlines. ",
            "roman_ur": "Fee structure document (Fall 2025) mein admission ki deadlines mojood nahi hain. ",
            "mixed": "Fee structure document (Fall 2025) mein admission deadlines mojood nahi hain. ",
            "ur": "فیس اسٹرکچر دستاویز (فال 2025) میں داخلے کی آخری تاریخیں موجود نہیں ہیں۔ ",
        }[language]
        pid = route.programs[0].id if route.programs else None
        return extra + NOT_FOUND[language], [], None, False, pid

    def _answer_eligibility(self, route, language):
        programs = route.programs
        marks = route.marks_pct
        if programs:
            p = programs[0]
            req = p.requirement
            parts = []
            if language == "ur":
                parts.append(f"{p.name} کے لیے بنیادی اہلیت: {req.prior_qualification if req else '—'}۔")
            elif language == "en":
                parts.append(f"For {p.name}, the basic prior qualification is: "
                             f"{req.prior_qualification if req else 'not recorded'}.")
            else:
                parts.append(f"{p.name} ke liye basic prior qualification: "
                             f"{req.prior_qualification if req else 'not recorded'}.")
            if req and req.min_marks_pct is not None:
                ok = (marks is None) or (marks >= req.min_marks_pct)
                parts.append(
                    f"Minimum marks required: {req.min_marks_pct:g}%."
                    + ("" if marks is None else
                       f" Your marks {marks:g}% — {'you meet this requirement.' if ok else 'you do not meet this requirement.'}")
                )
            else:
                parts.append({
                    "en": "The minimum marks percentage for this program is not available in the "
                          "provided data, so I cannot confirm marks-based eligibility.",
                    "roman_ur": "Is program ke liye minimum marks percentage mere data mein mojood "
                                "nahi hai, is liye marks ki bunyaad par eligibility confirm nahi ho sakti.",
                    "mixed": "Is program ke minimum marks percentage available data mein nahi hai, "
                             "so marks-based eligibility confirm nahi ho sakti.",
                    "ur": "اس پروگرام کے لیے کم از کم نمبروں کی شرح میرے ڈیٹا میں موجود نہیں ہے، "
                          "اس لیے نمبروں کی بنیاد پر اہلیت کی تصدیق نہیں ہو سکتی۔",
                }[language])
            if req and req.seats is not None:
                parts.append(f"Seats: {req.seats}.")
            else:
                parts.append({
                    "en": "Seat numbers for this program are not available in the provided data.",
                    "roman_ur": "Is program ki seats ki tadaad mere data mein mojood nahi hai.",
                    "mixed": "Is program ki seats information available data mein nahi hai.",
                    "ur": "اس پروگرام کی نشستوں کی تعداد میرے ڈیٹا میں موجود نہیں ہے۔",
                }[language])
            parts.append(VERIFY[language])
            return "\n".join(parts), [_source_for(p)], None, True, p.id

        if marks is not None:
            # Portal general rule (admin-set): BS admission needs >= 70% in
            # Intermediate (11th + 12th combined). Official programme-wise
            # criteria still apply on top — see each program's page.
            count = self.db.scalar(
                __import__("sqlalchemy").select(__import__("sqlalchemy").func.count())
                .select_from(Program).where(Program.level == "BS/Undergraduate")
            ) or 0
            if marks >= 70:
                text = {
                    "en": f"With {marks:g}% marks you meet this portal's general BS rule "
                          f"(minimum 70% in Intermediate, 11th + 12th combined), so by "
                          f"education level you can apply to undergraduate (BS) programs — "
                          f"this university offers {count} such programs. Programme-wise "
                          f"official criteria may differ per program; please confirm the "
                          f"exact merit with the university office. Use the Eligibility "
                          f"Checker page to browse them.",
                    "roman_ur": f"{marks:g}% marks ke saath aap is portal ke general BS rule "
                                f"(Intermediate — 11th + 12th mila kar — kam az kam 70%) ko "
                                f"poora karte hain, is liye education level ke hisab se aap "
                                f"undergraduate (BS) programs mein apply kar sakte hain — "
                                f"university mein aisay {count} programs hain. Har program ke "
                                f"official criteria mukhtalif ho sakte hain; exact merit "
                                f"office se confirm karein. Eligibility Checker page par "
                                f"programs dekhein.",
                    "mixed": f"{marks:g}% marks ke saath aap portal ke general BS rule "
                             f"(minimum 70% in Intermediate) ko meet karte hain — BS "
                             f"programs ke liye apply kar sakte hain, university mein "
                             f"{count} aisay programs hain. Programme-wise official "
                             f"criteria differ ho sakte hain, office se exact merit "
                             f"confirm karein.",
                    "ur": f"{marks:g} فیصد نمبروں کے ساتھ آپ اس پورٹل کے عمومی بی ایس اصول "
                          f"(انٹرمیڈیٹ — گیارہویں اور بارہویں ملا کر — کم از کم 70 فیصد) کو "
                          f"پورا کرتے ہیں، اس لیے تعلیمی درجے کے حساب سے آپ انڈرگریجویٹ (بی ایس) "
                          f"پروگراموں میں درخواست دے سکتے ہیں — یونیورسٹی میں ایسے {count} "
                          f"پروگرام ہیں۔ ہر پروگرام کے سرکاری معیار مختلف ہو سکتے ہیں؛ براہ کرم "
                          f"دفتر سے تصدیق کریں۔",
                }[language]
            else:
                text = {
                    "en": f"With {marks:g}% marks you do NOT meet this portal's general BS "
                          f"rule: BS admission requires at least 70% marks in Intermediate "
                          f"(11th + 12th combined). On this rule, admission to a BS/bachelor "
                          f"program is not possible with {marks:g}%. Official programme-wise "
                          f"criteria are listed on each program page — please also confirm "
                          f"with the university office.",
                    "roman_ur": f"{marks:g}% marks ke saath aap is portal ke general BS rule "
                                f"ko poora nahi karte: BS admission ke liye Intermediate "
                                f"(11th + 12th mila kar) mein kam az kam 70% marks lazmi "
                                f"hain. Is rule ke tehet {marks:g}% par BS/bachelor mein "
                                f"admission nahi ho sakta. Har program ke official criteria "
                                f"us ki page par diye gaye hain — office se bhi confirm "
                                f"kar lein.",
                    "mixed": f"{marks:g}% marks ke saath aap portal ke general BS rule ko "
                             f"meet nahi karte: BS admission ke liye Intermediate mein "
                             f"minimum 70% marks lazmi hain. Is rule ke tehet {marks:g}% "
                             f"par BS mein admission nahi ho sakta. Official criteria "
                             f"program pages par hain; office se confirm karein.",
                    "ur": f"{marks:g} فیصد نمبروں کے ساتھ آپ اس پورٹل کے عمومی بی ایس اصول کو "
                          f"پورا نہیں کرتے: بی ایس داخلے کے لیے انٹرمیڈیٹ (گیارہویں اور بارہویں "
                          f"ملا کر) میں کم از کم 70 فیصد نمبر لازمی ہیں۔ اس اصول کے تحت "
                          f"{marks:g} فیصد پر بی ایس/بیچلر میں داخلہ نہیں ہو سکتا۔ ہر پروگرام "
                          f"کے سرکاری معیار اس کے پیج پر موجود ہیں — براہ کرم دفتر سے بھی "
                          f"تصدیق کریں۔",
                }[language]
            return text + "\n" + VERIFY[language], [], None, True, None

        # General eligibility question without a specific program or marks:
        # answer with the portal's general rules (BS 70% · PhD CGPA 3.7) or
        # the official MPhil general criteria — but ONLY when the question is
        # really about marks/CGPA/criteria (a documents question, which also
        # lands here via the word "admission", must stay unanswered as before).
        n = route.normalized or ""
        hay = n + " " + (route.raw or "").lower()
        if not any(k in hay for k in ["eligib", "criteria", "marks", "percent",
                                      "cgpa", "فیصد", "نمبر", "اہلیت", "شرائط",
                                      "required", "requirement"]):
            return NOT_FOUND[language], [], None, False, None
        if "phd" in n:
            text = {
                "en": "For PhD admission, this portal's general rule requires a CGPA of "
                      "at least 3.7 in your MS/MPhil, along with the university entry "
                      "test. Programme-wise official criteria are listed on each PhD "
                      "program page.",
                "roman_ur": "PhD admission ke liye is portal ke general rule ke mutabiq "
                            "aap ke MS/MPhil mein kam az kam 3.7 CGPA hona chahiye, is ke "
                            "saath university ka entry test bhi hota hai. Har PhD program "
                            "ke official criteria us ki page par diye gaye hain.",
                "mixed": "PhD admission ke liye portal ke general rule ke mutabiq MS/MPhil "
                         "mein minimum 3.7 CGPA chahiye, saath entry test bhi hota hai. "
                         "Official criteria program pages par hain.",
                "ur": "پی ایچ ڈی داخلے کے لیے اس پورٹل کے عمومی اصول کے مطابق آپ کے ایم ایس/"
                      "ایم فل میں کم از کم 3.7 سی جی پی اے ہونا چاہیے، اس کے ساتھ یونیورسٹی "
                      "کا انٹری ٹیسٹ بھی ہوتا ہے۔ ہر پی ایچ ڈی پروگرام کے سرکاری معیار اس "
                      "کے پیج پر موجود ہیں۔",
            }[language]
            return text + "\n" + VERIFY[language], [], None, True, None
        if "mphil" in n or " ms " in f" {n} " or "master" in n:
            text = {
                "en": "For MS/MPhil admission the official general criteria are: a "
                      "16-year degree with at least 2nd division (annual system) or "
                      "CGPA 2.0 (semester system), plus a valid GRE/HAT/IUB entry test "
                      "with at least 50%. Programme-wise criteria are on each program page.",
                "roman_ur": "MS/MPhil admission ke official general criteria ye hain: "
                            "16 saal ki degree kam az kam 2nd division (annual) ya CGPA "
                            "2.0 (semester) ke saath, aur valid GRE/HAT/IUB entry test "
                            "mein kam az kam 50%. Har program ke criteria us ki page par "
                            "hain.",
                "mixed": "MS/MPhil ke official general criteria: 16-year degree with at "
                         "least 2nd division ya CGPA 2.0, plus entry test (GRE/HAT/IUB) "
                         "mein minimum 50%. Programme-wise criteria program pages par hain.",
                "ur": "ایم ایس/ایم فل داخلے کے سرکاری عمومی معیار یہ ہیں: 16 سالہ ڈگری کم از "
                      "کم سیکنڈ ڈویژن (سالانہ) یا سی جی پی اے 2.0 (سیمسٹر) کے ساتھ، اور "
                      "درست GRE/HAT/IUB انٹری ٹیسٹ میں کم از کم 50 فیصد۔ ہر پروگرام کے "
                      "معیار اس کے پیج پر موجود ہیں۔",
            }[language]
            return text + "\n" + VERIFY[language], [], None, True, None
        text = {
            "en": "This portal's general rule for BS/bachelor admission: at least 70% "
                  "marks in Intermediate (11th + 12th combined) — below 70%, BS admission "
                  "is not possible under this rule. For PhD, a CGPA of at least 3.7 in "
                  "MS/MPhil is required. Official programme-wise criteria may differ and "
                  "are listed on each program page; you can also test your own marks on "
                  "the Eligibility Checker page.",
            "roman_ur": "Is portal ka general rule BS/bachelor admission ke liye ye hai: "
                        "Intermediate (11th + 12th mila kar) mein kam az kam 70% marks — "
                        "70% se kam par is rule ke tehet BS admission nahi hota. PhD ke "
                        "liye MS/MPhil mein kam az kam 3.7 CGPA chahiye. Har program ke "
                        "official criteria mukhtalif ho sakte hain aur us ki page par "
                        "diye gaye hain; apne marks Eligibility Checker page par test "
                        "bhi kar sakte hain.",
            "mixed": "Portal ka general rule: BS/bachelor admission ke liye Intermediate "
                     "mein minimum 70% marks (11th + 12th combined) — is se kam par BS "
                     "admission nahi hota. PhD ke liye MS/MPhil mein minimum 3.7 CGPA "
                     "chahiye. Official programme-wise criteria program pages par hain; "
                     "Eligibility Checker page par apne marks test kar sakte hain.",
            "ur": "اس پورٹل کا عمومی اصول بی ایس/بیچلر داخلے کے لیے یہ ہے: انٹرمیڈیٹ "
                  "(گیارہویں اور بارہویں ملا کر) میں کم از کم 70 فیصد نمبر — اس سے کم پر "
                  "اس اصول کے تحت بی ایس داخلہ نہیں ہوتا۔ پی ایچ ڈی کے لیے ایم ایس/ایم فل "
                  "میں کم از کم 3.7 سی جی پی اے چاہیے۔ ہر پروگرام کے سرکاری معیار مختلف "
                  "ہو سکتے ہیں اور اس کے پیج پر موجود ہیں؛ اپنے نمبر Eligibility Checker "
                  "پیج پر بھی جانچ سکتے ہیں۔",
        }[language]
        return text + "\n" + VERIFY[language], [], None, True, None

    def _answer_comparison(self, route, language):
        variants = route.programs
        if len(variants) < 2:
            return NOT_FOUND[language], [], None, False, None
        # Compare two DISTINCT programs (not Group-A vs Group-B of the same one).
        def base_name(p):
            return p.name_normalized.replace("group a", "").replace("group b", "").strip()
        a = variants[0]
        b = next((p for p in variants[1:] if base_name(p) != base_name(a)), variants[1])
        if a.fee is None or b.fee is None:
            return NOT_FOUND[language], [], None, False, None
        fa, fb = a.fee, b.fee
        diff = fa.total_first_semester - fb.total_first_semester
        cheaper = a.name if diff < 0 else b.name if diff > 0 else "both are equal"
        if language == "en":
            text = (
                f"Comparison:\n"
                f"• {a.name}: 1st semester {_rs(fa.total_first_semester)}, later {_rs(fa.total_next_semesters)}"
                f", duration ~{a.duration_years:g} years, {a.department.name}.\n"
                f"• {b.name}: 1st semester {_rs(fb.total_first_semester)}, later {_rs(fb.total_next_semesters)}"
                f", duration ~{b.duration_years:g} years, {b.department.name}.\n"
                f"Cheaper first semester: {cheaper} (difference {_rs(abs(diff))}).\n" + VERIFY[language]
            )
        elif language == "ur":
            text = (
                f"موازنہ:\n"
                f"• {a.name}: پہلا سمسٹر {_rs(fa.total_first_semester)}، بعد میں {_rs(fa.total_next_semesters)}، "
                f"دورانیہ تقریباً {a.duration_years:g} سال، {a.department.name}۔\n"
                f"• {b.name}: پہلا سمسٹر {_rs(fb.total_first_semester)}، بعد میں {_rs(fb.total_next_semesters)}، "
                f"دورانیہ تقریباً {b.duration_years:g} سال، {b.department.name}۔\n"
                f"پہلے سمسٹر میں سستا: {cheaper} (فرق {_rs(abs(diff))})۔\n" + VERIFY[language]
            )
        else:
            text = (
                f"Comparison:\n"
                f"• {a.name}: Pehla semester {_rs(fa.total_first_semester)}, baad mein {_rs(fa.total_next_semesters)}"
                f", duration ~{a.duration_years:g} saal, {a.department.name}.\n"
                f"• {b.name}: Pehla semester {_rs(fb.total_first_semester)}, baad mein {_rs(fb.total_next_semesters)}"
                f", duration ~{b.duration_years:g} saal, {b.department.name}.\n"
                f"Sab se sasta pehla semester: {cheaper} (farq {_rs(abs(diff))}).\n" + VERIFY[language]
            )
        return text, [_source_for(a), _source_for(b)], _fee_table(a), True, a.id

    def _answer_policy(self, route, language):
        # Raw wording matches policy text best; the normalised/alias-expanded
        # form is the fallback (it also carries Urdu-alias English tokens).
        hits = retriever.search(route.raw or "", top_k=5)
        if not hits:
            hits = retriever.search(route.normalized or "", top_k=5)
        if not hits:
            return NOT_FOUND[language], [], None, False, None
        top = hits[0]
        sources = [f"{h['title']} — {h['source']}" for h in hits]
        text = top["text"].strip()
        if language == "roman_ur" and top.get("title"):
            pass  # policy texts are stored in English; citation makes the source clear
        return f"{text}\n{VERIFY[language]}", sources, None, True, None

    def _answer_program_info(self, route, language):
        if not route.programs:
            return NOT_FOUND[language], [], None, False, None
        p = route.programs[0]
        dur_note = "" if p.duration_source == "stated_in_source" else " (standard duration for this level; not stated in the fee document)"
        if language == "en":
            text = (f"{p.name} is offered by {p.department.name}, {p.department.faculty.name}. "
                    f"Level: {p.level}. Duration: ~{p.duration_years:g} years{dur_note}. "
                    f"Shift: {p.shift}. " + VERIFY[language])
        elif language == "ur":
            text = (f"{p.name} — {p.department.name}، {p.department.faculty.name} کے تحت ہے۔ "
                    f"درجہ: {p.level}۔ دورانیہ: تقریباً {p.duration_years:g} سال۔ " + VERIFY[language])
        else:
            text = (f"{p.name} — {p.department.name}, {p.department.faculty.name} mein hai. "
                    f"Level: {p.level}. Duration: ~{p.duration_years:g} saal{dur_note}. "
                    f"Shift: {p.shift}. " + VERIFY[language])
        return text, [_source_for(p)], _fee_table(p), True, p.id
