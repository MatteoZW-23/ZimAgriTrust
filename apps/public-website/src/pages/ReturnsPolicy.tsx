import React from "react";
import { Link } from "react-router-dom";
import {
  RotateCcw,
  ShieldAlert,
  CheckCircle2,
  Clock,
  Scale,
  Phone,
  Mail,
  ArrowRight,
} from "lucide-react";

function ReturnsPolicy() {
  return (
    <div className="min-h-screen bg-earth-50">
      {/* HEADER */}
      <header className="fixed top-0 left-0 w-full z-50 bg-white/90 backdrop-blur-xl border-b border-earth-100">
        <div className="container-custom h-20 flex items-center justify-between">
          <Link
            to="/"
            className="flex items-center gap-3"
          >
            <img
              src="/logo.png"
              alt="ZimAgriTrust"
              className="h-10 w-auto"
            />

            <span className="text-xl font-bold text-primary-700">
              ZimAgriTrust
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            <Link
              to="/"
              className="nav-link"
            >
              Home
            </Link>

            <Link
              to="/about"
              className="nav-link"
            >
              About
            </Link>

            <Link
              to="/help"
              className="nav-link"
            >
              Help
            </Link>
          </nav>
        </div>
      </header>

      {/* HERO */}
      <section className="gradient-hero text-white pt-36 pb-24 relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.04]">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage:
                "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
              backgroundSize: "40px 40px",
            }}
          />
        </div>

        <div className="container-narrow relative z-10">
          <div className="max-w-3xl">
            <div className="badge bg-white/10 text-white border border-white/10 mb-6">
              <RotateCcw className="w-4 h-4" />
              Returns & Refund Policy
            </div>

            <h1 className="text-5xl lg:text-6xl font-bold leading-tight mb-6">
              Returns & Refund Policy
            </h1>

            <p className="text-xl text-white/80 leading-relaxed">
              Transparent refund and dispute resolution procedures for
              agricultural marketplace transactions.
            </p>

            <p className="mt-6 text-sm text-white/50">
              Last updated: May 2026
            </p>
          </div>
        </div>
      </section>

      {/* CONTENT */}
      <section className="section-padding">
        <div className="container-narrow">
          <div className="card p-8 lg:p-12">
            {/* INTRO */}
            <div className="mb-14">
              <p className="text-lg text-earth-600 leading-relaxed">
                Because agricultural products are perishable, returns are
                handled through our dispute resolution framework rather than
                traditional return shipping procedures.
              </p>
            </div>

            {/* SECTION */}
            <section className="mb-14">
              <div className="flex items-center gap-3 mb-6">
                <Clock className="w-7 h-7 text-primary-700" />

                <h2 className="text-3xl font-bold text-earth-900">
                  1. Inspection Window
                </h2>
              </div>

              <p className="text-earth-600 leading-relaxed text-lg">
                Buyers have 24 hours after delivery to inspect goods and raise
                issues. After 24 hours, products are considered accepted and no
                refund may be issued.
              </p>
            </section>

            {/* REFUNDS */}
            <section className="mb-14">
              <div className="flex items-center gap-3 mb-8">
                <ShieldAlert className="w-7 h-7 text-primary-700" />

                <h2 className="text-3xl font-bold text-earth-900">
                  2. Refund Eligibility
                </h2>
              </div>

              <div className="space-y-8">
                {/* FULL */}
                <div className="bg-primary-50 rounded-3xl p-8 border border-primary-100">
                  <h3 className="text-2xl font-bold text-primary-800 mb-5">
                    Full Refund (100%)
                  </h3>

                  <ul className="space-y-4">
                    {[
                      "Goods never delivered",
                      "Completely wrong crop delivered",
                      "Crop quality significantly below listing",
                      "Fraudulent listing confirmed",
                    ].map((item, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-3"
                      >
                        <CheckCircle2 className="w-5 h-5 text-primary-700 mt-1" />

                        <span className="text-earth-700">
                          {item}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* PARTIAL */}
                <div className="bg-secondary-50 rounded-3xl p-8 border border-secondary-100">
                  <h3 className="text-2xl font-bold text-secondary-800 mb-5">
                    Partial Refund (10%–50%)
                  </h3>

                  <ul className="space-y-4">
                    {[
                      "Quality lower than advertised but usable",
                      "Quantity shortage",
                      "Minor damage or defects",
                      "Delivery delays exceeding 48 hours",
                    ].map((item, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-3"
                      >
                        <CheckCircle2 className="w-5 h-5 text-secondary-700 mt-1" />

                        <span className="text-earth-700">
                          {item}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* NO REFUND */}
                <div className="bg-earth-100 rounded-3xl p-8 border border-earth-200">
                  <h3 className="text-2xl font-bold text-earth-800 mb-5">
                    No Refund
                  </h3>

                  <ul className="space-y-4">
                    {[
                      "Buyer changed mind",
                      "Market price changed after purchase",
                      "Buyer-caused damage",
                      "Inspection window expired",
                      "Quality matches listing description",
                    ].map((item, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-3"
                      >
                        <CheckCircle2 className="w-5 h-5 text-earth-700 mt-1" />

                        <span className="text-earth-700">
                          {item}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>

            {/* PROCESS */}
            <section className="mb-14">
              <div className="flex items-center gap-3 mb-8">
                <ArrowRight className="w-7 h-7 text-primary-700" />

                <h2 className="text-3xl font-bold text-earth-900">
                  3. Refund Process
                </h2>
              </div>

              <div className="space-y-6">
                {[
                  'Do NOT confirm delivery in the app',
                  'Go to "My Orders" → "Raise Dispute"',
                  "Select dispute reason",
                  "Upload evidence photos",
                  "Agent investigates within 48 hours",
                  "Decision communicated via SMS, WhatsApp, and email",
                  "Approved refunds processed within 3–5 business days",
                ].map((step, i) => (
                  <div
                    key={i}
                    className="flex gap-5"
                  >
                    <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold shrink-0">
                      {i + 1}
                    </div>

                    <p className="text-earth-600 leading-relaxed pt-2">
                      {step}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* EVIDENCE */}
            <section className="mb-14">
              <div className="flex items-center gap-3 mb-6">
                <Scale className="w-7 h-7 text-primary-700" />

                <h2 className="text-3xl font-bold text-earth-900">
                  4. Evidence Requirements
                </h2>
              </div>

              <div className="grid md:grid-cols-2 gap-5">
                {[
                  "Clear photos of delivered goods",
                  "Comparison photos",
                  "Weighing scale photos",
                  "Delivery notes or receipts",
                  "Communication history with seller",
                  "Transport verification details",
                ].map((item, i) => (
                  <div
                    key={i}
                    className="bg-earth-50 rounded-2xl p-5 flex items-center gap-4"
                  >
                    <CheckCircle2 className="w-5 h-5 text-primary-700" />

                    <span className="text-earth-700">
                      {item}
                    </span>
                  </div>
                ))}
              </div>
            </section>

            {/* TIMELINE */}
            <section className="mb-14">
              <h2 className="text-3xl font-bold text-earth-900 mb-8">
                5. Refund Timeline
              </h2>

              <div className="grid md:grid-cols-2 gap-6">
                {[
                  "Dispute Raised — Day 1",
                  "Agent Assigned — Within 24 Hours",
                  "Evidence Collection — Day 2–3",
                  "Decision — Day 3–4",
                  "Refund Processing — 3–5 Business Days",
                ].map((item, i) => (
                  <div
                    key={i}
                    className="card p-6"
                  >
                    <p className="font-semibold text-earth-800">
                      {item}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* CONTACT */}
            <section>
              <div className="gradient-primary rounded-[2rem] p-10 text-white">
                <h2 className="text-4xl font-bold mb-4">
                  Need Help?
                </h2>

                <p className="text-white/80 text-lg mb-10">
                  Contact our dispute resolution and refund support team.
                </p>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="glass rounded-3xl p-6 flex items-center gap-5">
                    <div className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center">
                      <Mail className="w-6 h-6" />
                    </div>

                    <div>
                      <p className="text-sm text-white/60 mb-1">
                        Email Support
                      </p>

                      <h3 className="text-xl font-semibold">
                        disputes@zimagritrust.com
                      </h3>
                    </div>
                  </div>

                  <div className="glass rounded-3xl p-6 flex items-center gap-5">
                    <div className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center">
                      <Phone className="w-6 h-6" />
                    </div>

                    <div>
                      <p className="text-sm text-white/60 mb-1">
                        WhatsApp Support
                      </p>

                      <h3 className="text-xl font-semibold">
                        +263 71 735 8956
                      </h3>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-earth-200 bg-white py-8">
        <div className="container-custom flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-earth-500 text-sm">
            © 2026 ZimAgriTrust. All rights reserved.
          </p>

          <div className="flex items-center gap-6 text-sm">
            <Link
              to="/privacy"
              className="nav-link"
            >
              Privacy Policy
            </Link>

            <Link
              to="/terms"
              className="nav-link"
            >
              Terms
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default ReturnsPolicy;