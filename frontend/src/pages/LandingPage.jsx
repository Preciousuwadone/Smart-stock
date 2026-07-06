import { Link } from "react-router-dom";
import { Users, Landmark, Sparkles, BellRing, ShieldCheck, BarChart3 } from "lucide-react";
import Logo from "../components/Logo";
import RiskBadge from "../components/RiskBadge";
import "./LandingPage.css";

const FEATURES = [
  { icon: Users, title: "Add Customers & Credit Sales", text: "Log a customer and their credit purchase in seconds — no notebook, no guesswork." },
  { icon: Landmark, title: "Dedicated Nomba Virtual Accounts", text: "Every customer gets their own account number to pay into. Money lands exactly where it should." },
  { icon: Sparkles, title: "AI Credit Scoring & Default Prediction", text: "SmartStock learns each customer's payment behaviour and flags who's likely to default, before it happens." },
  { icon: BellRing, title: "Automated Payment Reminders", text: "Reminders go out on their own by email, with a Nomba checkout link attached, so paying is one tap away." },
  { icon: ShieldCheck, title: "Real-Time Payment Confirmation", text: "Nomba webhooks confirm payments instantly and update your dashboard — no manual reconciliation." },
  { icon: BarChart3, title: "Full Credit Portfolio Dashboard", text: "See exactly who owes what, who's at risk, and how your credit book is trending, at a glance." },
];

const STEPS = [
  { n: "1", title: "Add a customer", text: "Save their name and phone number. SmartStock creates their Nomba virtual account instantly." },
  { n: "2", title: "Record the credit sale", text: "Log what they bought and how much they owe, right when it happens." },
  { n: "3", title: "Customer repays", text: "They pay into their account, or you send them a Nomba checkout link." },
  { n: "4", title: "AI scores & reminds", text: "Behaviour is scored, risky customers are flagged, reminders go out automatically." },
];

export default function LandingPage() {
  const isLoggedIn = !!localStorage.getItem("token");

  return (
    <div className="ss-root">
      <header className="ss-band ss-nav-band">
        <div className="ss-container ss-nav">
          <Logo size={36} />
          <nav className="ss-nav-actions">
            {isLoggedIn ? (
              <Link to="/dashboard" className="ss-btn ss-btn-primary">Go to Dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="ss-btn ss-btn-ghost">Log in</Link>
                <Link to="/login?mode=signup" className="ss-btn ss-btn-primary">Get Started</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main>
        <section className="ss-band ss-hero-band">
          <div className="ss-container ss-hero">
            <div className="ss-hero-copy">
              <span className="ss-eyebrow">Digital credit book for retailers</span>
              <h1>Stop chasing debtors.<br />Let SmartStock collect for you.</h1>
              <p className="ss-hero-sub">
                Replace your notebook credit book. Record customer credit in seconds, give every
                customer their own Nomba account to pay into, and let AI flag who's likely to
                default before it happens.
              </p>
              <div className="ss-hero-ctas">
                <Link to="/login?mode=signup" className="ss-btn ss-btn-primary ss-btn-lg">Get Started Free</Link>
                <Link to="/login" className="ss-btn ss-btn-ghost ss-btn-lg">I already have an account</Link>
              </div>
              <div className="ss-trust-strip">
                <span>No card required</span>
                <span>Nomba-secured accounts</span>
                <span>Automated reminders</span>
              </div>
            </div>

            <div className="ss-hero-visual">
              <div className="ss-mock-card">
                <div className="ss-mock-header">
                  <span>Customer Credit Book</span>
                  <span className="ss-mock-total">₦248,500 outstanding</span>
                </div>
                {[
                  { name: "Amaka Okafor", amt: "₦42,000", risk: "low" },
                  { name: "Tunde Bello", amt: "₦18,500", risk: "medium" },
                  { name: "Chinedu Eze", amt: "₦96,000", risk: "high" },
                ].map((row) => (
                  <div className="ss-mock-row" key={row.name}>
                    <div className="ss-mock-avatar">{row.name[0]}</div>
                    <div className="ss-mock-info">
                      <strong>{row.name}</strong>
                      <span>{row.amt} owed</span>
                    </div>
                    <RiskBadge tier={row.risk} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="ss-band ss-partner-band">
          <div className="ss-container ss-partner">
            <span>Payments powered by</span>
            <strong>Nomba</strong>
          </div>
        </section>

        <section className="ss-band ss-features-band">
          <div className="ss-container">
            <h2>Everything your credit book needs</h2>
            <p className="ss-section-sub">From recording a sale to getting paid, SmartStock handles the whole cycle.</p>
            <div className="ss-features-grid">
              {FEATURES.map((f) => (
                <div className="ss-feature-card" key={f.title}>
                  <div className="ss-feature-icon"><f.icon size={22} strokeWidth={1.75} /></div>
                  <h3>{f.title}</h3>
                  <p>{f.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="ss-band ss-steps-band">
          <div className="ss-container">
            <h2>How it works</h2>
            <div className="ss-steps-grid">
              {STEPS.map((s) => (
                <div className="ss-step" key={s.n}>
                  <div className="ss-step-num">{s.n}</div>
                  <h3>{s.title}</h3>
                  <p>{s.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="ss-band ss-cta-outer-band">
          <div className="ss-container">
            <div className="ss-cta-band">
              <h2>Your credit book deserves better than a notebook.</h2>
              <Link to="/login?mode=signup" className="ss-btn ss-btn-primary ss-btn-lg">Get Started Free</Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="ss-band ss-footer-band">
        <div className="ss-container ss-footer">
          <Logo size={28} />
          <p>Digital credit book for Nigerian businesses, powered by Nomba.</p>
          <span className="ss-footer-copy">© 2026 SmartStock</span>
        </div>
      </footer>
    </div>
  );
}