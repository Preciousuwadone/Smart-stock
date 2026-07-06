import { Link } from "react-router-dom";
import Logo from "../components/Logo";
import "./LandingPage.css";

const icon = (path) => (props) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
    strokeLinecap="round" strokeLinejoin="round" width="26" height="26" {...props}>
    {path}
  </svg>
);

const IconCustomers = icon(<>
  <circle cx="9" cy="8" r="3" /><path d="M4 20c0-3 2.5-5 5-5s5 2 5 5" />
  <circle cx="17" cy="9" r="2.4" /><path d="M15 20c0-2.5 1-4 3.5-4.3" />
</>);
const IconBank = icon(<>
  <path d="M4 10l8-5 8 5" /><rect x="5" y="10" width="14" height="8" rx="1" />
  <line x1="4" y1="20" x2="20" y2="20" /><line x1="8" y1="10" x2="8" y2="18" />
  <line x1="12" y1="10" x2="12" y2="18" /><line x1="16" y1="10" x2="16" y2="18" />
</>);
const IconSpark = icon(<>
  <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z" />
  <circle cx="18.5" cy="17" r="1.4" />
</>);
const IconBell = icon(<>
  <path d="M6 16v-4a6 6 0 1 1 12 0v4l1.5 2.5h-15L6 16z" /><path d="M10 20a2 2 0 0 0 4 0" />
</>);
const IconShield = icon(<>
  <path d="M12 3l7 3v5c0 5-3 8.5-7 10-4-1.5-7-5-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" />
</>);
const IconChart = icon(<>
  <line x1="4" y1="20" x2="20" y2="20" /><rect x="6" y="14" width="3" height="6" />
  <rect x="11" y="9" width="3" height="11" /><rect x="16" y="5" width="3" height="15" />
</>);

const FEATURES = [
  { icon: IconCustomers, title: "Add Customers & Credit Sales", text: "Log a customer and their credit purchase in seconds — no more notebook, no more guesswork." },
  { icon: IconBank, title: "Dedicated Nomba Virtual Accounts", text: "Every customer gets their own account number to pay into. Money lands exactly where it should." },
  { icon: IconSpark, title: "AI Credit Scoring & Default Prediction", text: "SmartStock learns each customer's payment behaviour and flags who's likely to default — before it happens." },
  { icon: IconBell, title: "Automated Payment Reminders", text: "SMS and email reminders go out on their own, with a Nomba checkout link attached, so paying is one tap away." },
  { icon: IconShield, title: "Real-Time Payment Confirmation", text: "Nomba webhooks confirm payments instantly and update your dashboard — no manual reconciliation." },
  { icon: IconChart, title: "Full Credit Portfolio Dashboard", text: "See exactly who owes what, who's at risk, and how your credit book is trending, at a glance." },
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
                <Link to="/login?mode=signup" className="ss-btn ss-btn-primary">Get Started Free</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main>
        <section className="ss-band ss-hero-band">
          <div className="ss-container ss-hero">
            <div className="ss-hero-copy">
              <span className="ss-eyebrow">Built for Nigerian shop owners 🇳🇬</span>
              <h1>Stop chasing debtors.<br />Let SmartStock collect for you.</h1>
              <p className="ss-hero-sub">
                Replace your notebook credit book. Record customer credit in seconds, give every
                customer their own Nomba account to pay into, and let AI flag who's likely to
                default — before it happens.
              </p>
              <div className="ss-hero-ctas">
                <Link to="/login?mode=signup" className="ss-btn ss-btn-primary ss-btn-lg">Get Started Free</Link>
                <Link to="/login" className="ss-btn ss-btn-ghost ss-btn-lg">I already have an account</Link>
              </div>
              <div className="ss-trust-strip">
                <span>✓ No card required</span>
                <span>✓ Nomba-secured accounts</span>
                <span>✓ SMS + Email reminders</span>
              </div>
            </div>

            <div className="ss-hero-visual">
              <div className="ss-mock-card">
                <div className="ss-mock-header">
                  <span>Customer Credit Book</span>
                  <span className="ss-mock-total">₦248,500 outstanding</span>
                </div>
                {[
                  { name: "Amaka Okafor", amt: "₦42,000", risk: "Low", color: "success" },
                  { name: "Tunde Bello", amt: "₦18,500", risk: "Medium", color: "accent" },
                  { name: "Chinedu Eze", amt: "₦96,000", risk: "High", color: "danger" },
                ].map((row) => (
                  <div className="ss-mock-row" key={row.name}>
                    <div className="ss-mock-avatar">{row.name[0]}</div>
                    <div className="ss-mock-info">
                      <strong>{row.name}</strong>
                      <span>{row.amt} owed</span>
                    </div>
                    <span className={`ss-badge ss-badge-${row.color}`}>{row.risk} risk</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="ss-band ss-features-band">
          <div className="ss-container">
            <h2>Everything your credit book needs</h2>
            <p className="ss-section-sub">From recording a sale to getting paid — SmartStock handles the whole cycle.</p>
            <div className="ss-features-grid">
              {FEATURES.map((f) => (
                <div className="ss-feature-card" key={f.title}>
                  <div className="ss-feature-icon"><f.icon /></div>
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
          <span className="ss-footer-copy">© 2026 SmartStock. Made in Nigeria 🇳🇬</span>
        </div>
      </footer>
    </div>
  );
}