import React from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Scale,
  Shield,
  CreditCard,
  AlertTriangle,
  Truck,
  MessageSquare,
  Ban,
  Database,
  Gavel,
  RefreshCw,
} from "lucide-react";

function TermsConditions() {
  const sections = [
    { id: "services", title: "Platform Services", icon: FileText },
    { id: "registration", title: "User Registration", icon: Shield },
    { id: "trading", title: "Trading & Escrow", icon: Scale },
    { id: "fees", title: "Fees & Payments", icon: CreditCard },
    { id: "prohibited", title: "Prohibited Activities", icon: AlertTriangle },
    { id: "delivery", title: "Delivery & Logistics", icon: Truck },
    { id: "disputes", title: "Dispute Resolution", icon: MessageSquare },
    { id: "liability", title: "Liability", icon: Ban },
    { id: "termination", title: "Termination", icon: Database },
    { id: "legal", title: "Legal", icon: Gavel },
  ];

  return (
    <div className="min-h-screen bg-earth-50">
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-700 to-primary-900 text-white py-16 lg:py-24">
        <div className="container-custom">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-3xl mx-auto"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm mb-6">
              <Scale className="w-4 h-4" />
              <span className="text-sm font-medium">Legal</span>
            </div>

            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Terms & Conditions
            </h1>

            <p className="text-primary-100">
              Last updated: May 2026 | Effective: May 1, 2026
            </p>
          </motion.div>
        </div>
      </section>

      {/* Content */}
      <section className="py-16">
        <div className="container-custom">
          <div className="grid lg:grid-cols-4 gap-8">
            {/* Sidebar */}
            <div className="hidden lg:block">
              <div className="sticky top-24 bg-white rounded-xl p-6 shadow-sm border border-earth-100">
                <h3 className="font-semibold text-earth-900 mb-4">
                  Contents
                </h3>

                <nav className="space-y-2">
                  {sections.map((section) => (
                    <a
                      key={section.id}
                      href={`#${section.id}`}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-earth-600 hover:bg-primary-50 hover:text-primary-700 transition-colors"
                    >
                      <section.icon className="w-4 h-4" />
                      {section.title}
                    </a>
                  ))}
                </nav>
              </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3">
              <div className="bg-white rounded-2xl p-8 shadow-sm border border-earth-100">
                <p className="text-earth-600 mb-8 leading-relaxed">
                  Welcome to ZimAgriTrust. These Terms and Conditions govern
                  your use of our platform and services. By accessing or using
                  our platform, you agree to be bound by these terms.
                </p>

                {/* Platform Services */}
                <div id="services" className="mb-12 scroll-mt-24">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-primary-600" />
                    </div>

                    <h2 className="text-2xl font-bold text-earth-900">
                      1. Platform Services
                    </h2>
                  </div>

                  <p className="text-earth-600">
                    ZimAgriTrust provides a digital marketplace connecting
                    farmers, buyers, and logistics providers. We facilitate
                    trade but do not own the commodities listed unless
                    explicitly stated.
                  </p>
                </div>

                {/* Registration */}
                <div
                  id="registration"
                  className="mb-12 scroll-mt-24 pt-8 border-t border-earth-100"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <Shield className="w-5 h-5 text-primary-600" />
                    </div>

                    <h2 className="text-2xl font-bold text-earth-900">
                      2. User Registration & Eligibility
                    </h2>
                  </div>

                  <ul className="space-y-2 text-earth-600">
                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      You must be at least 18 years old to use this platform.
                    </li>

                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      Users must provide accurate and complete registration
                      information.
                    </li>

                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      You are responsible for maintaining your account PIN.
                    </li>

                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      Multiple accounts are prohibited.
                    </li>
                  </ul>
                </div>

                {/* Trading */}
                <div
                  id="trading"
                  className="mb-12 scroll-mt-24 pt-8 border-t border-earth-100"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <Scale className="w-5 h-5 text-primary-600" />
                    </div>

                    <h2 className="text-2xl font-bold text-earth-900">
                      3. Trading & Escrow Protection
                    </h2>
                  </div>

                  <ul className="space-y-2 text-earth-600">
                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      All trades are protected through our escrow system.
                    </li>

                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      Funds are held securely until delivery confirmation.
                    </li>

                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      Buyers have 24 hours to inspect and dispute goods.
                    </li>
                  </ul>
                </div>

                {/* Fees */}
                <div
                  id="fees"
                  className="mb-12 scroll-mt-24 pt-8 border-t border-earth-100"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <CreditCard className="w-5 h-5 text-primary-600" />
                    </div>

                    <h2 className="text-2xl font-bold text-earth-900">
                      4. Fees & Payments
                    </h2>
                  </div>

                  <div className="space-y-2 text-earth-600">
                    <p>
                      <strong>Platform fee:</strong> 2.5%
                    </p>

                    <p>
                      <strong>Escrow fee:</strong> 0.5%
                    </p>

                    <p>
                      <strong>Withdrawal fee:</strong> 1%
                    </p>

                    <p>
                      <strong>Premium listing:</strong> $2
                    </p>
                  </div>
                </div>

                {/* Prohibited */}
                <div
                  id="prohibited"
                  className="mb-12 scroll-mt-24 pt-8 border-t border-earth-100"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                      <AlertTriangle className="w-5 h-5 text-red-600" />
                    </div>

                    <h2 className="text-2xl font-bold text-earth-900">
                      5. Prohibited Activities
                    </h2>
                  </div>

                  <ul className="space-y-2 text-earth-600">
                    <li className="flex items-start gap-2">
                      <span className="text-red-500 mt-1">•</span>
                      Listing illegal or fraudulent products.
                    </li>

                    <li className="flex items-start gap-2">
                      <span className="text-red-500 mt-1">•</span>
                      Bypassing escrow payments.
                    </li>

                    <li className="flex items-start gap-2">
                      <span className="text-red-500 mt-1">•</span>
                      Manipulating prices or misleading buyers.
                    </li>
                  </ul>
                </div>

                {/* Delivery */}
                <div
                  id="delivery"
                  className="mb-12 scroll-mt-24 pt-8 border-t border-earth-100"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <Truck className="w-5 h-5 text-primary-600" />
                    </div>

                    <h2 className="text-2xl font-bold text-earth-900">
                      6. Delivery & Logistics
                    </h2>
                  </div>

                  <p className="text-earth-600">
                    Delivery may be completed by farmers, buyers, platform
                    drivers, or transport cooperatives.
                  </p>
                </div>

                {/* Disputes */}
                <div
                  id="disputes"
                  className="mb-12 scroll-mt-24 pt-8 border-t border-earth-100"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <MessageSquare className="w-5 h-5 text-primary-600" />
                    </div>

                    <h2 className="text-2xl font-bold text-earth-900">
                      7. Dispute Resolution
                    </h2>
                  </div>

                  <ul className="space-y-2 text-earth-600">
                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      Disputes must first be resolved directly between users.
                    </li>

                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      Formal disputes are reviewed within 48 hours.
                    </li>
                  </ul>
                </div>

                {/* Liability */}
                <div
                  id="liability"
                  className="mb-12 scroll-mt-24 pt-8 border-t border-earth-100"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <Ban className="w-5 h-5 text-primary-600" />
                    </div>

                    <h2 className="text-2xl font-bold text-earth-900">
                      8. Limitation of Liability
                    </h2>
                  </div>

                  <p className="text-earth-600">
                    ZimAgriTrust is not liable for indirect or consequential
                    damages including crop failure, logistics delays, or market
                    fluctuations.
                  </p>
                </div>

                {/* Termination */}
                <div
                  id="termination"
                  className="mb-12 scroll-mt-24 pt-8 border-t border-earth-100"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <Database className="w-5 h-5 text-primary-600" />
                    </div>

                    <h2 className="text-2xl font-bold text-earth-900">
                      9. Account Suspension & Termination
                    </h2>
                  </div>

                  <ul className="space-y-2 text-earth-600">
                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      Accounts violating terms may be suspended.
                    </li>

                    <li className="flex items-start gap-2">
                      <span className="text-primary-500 mt-1">•</span>
                      Users may delete accounts at any time.
                    </li>
                  </ul>
                </div>

                {/* Legal */}
                <div
                  id="legal"
                  className="scroll-mt-24 pt-8 border-t border-earth-100"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <Gavel className="w-5 h-5 text-primary-600" />
                    </div>

                    <h2 className="text-2xl font-bold text-earth-900">
                      10. Governing Law & Contact
                    </h2>
                  </div>

                  <div className="space-y-3 text-earth-600">
                    <p>
                      These terms are governed by the laws of Zimbabwe.
                    </p>

                    <p>
                      <strong>Email:</strong> legal@zimagritrust.com
                    </p>

                    <p>
                      <strong>Phone:</strong> +263 71 735 8956
                    </p>

                    <p className="flex items-center gap-2 mt-4">
                      <RefreshCw className="w-4 h-4" />

                      <span>
                        Continued use of the platform constitutes acceptance of
                        updated terms.
                      </span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default TermsConditions;