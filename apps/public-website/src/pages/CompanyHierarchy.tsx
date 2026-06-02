import React from "react";
import { Shield, Users, Truck, Sprout, Building2, Headphones } from "lucide-react";

const teams = [
  {
    title: "Platform Governance",
    description: "Sets policy, risk controls, product standards, and compliance oversight.",
    icon: Shield,
  },
  {
    title: "Marketplace Operations",
    description: "Manages farmer, buyer, supplier, listing, quality, and order workflows.",
    icon: Sprout,
  },
  {
    title: "Field Agent Network",
    description: "Handles farm visits, crop checks, identity support, and dispute evidence.",
    icon: Users,
  },
  {
    title: "Logistics Coordination",
    description: "Coordinates approved drivers, delivery assignment, pickup, tracking, and proof of delivery.",
    icon: Truck,
  },
  {
    title: "Finance & Escrow",
    description: "Controls wallet, escrow, settlement, fee, payout, and reconciliation processes.",
    icon: Building2,
  },
  {
    title: "Support Desk",
    description: "Supports farmers, buyers, suppliers, drivers, agents, and enterprise customers.",
    icon: Headphones,
  },
];

export default function CompanyHierarchy() {
  return (
    <main className="bg-earth-50 min-h-screen">
      <section className="gradient-primary text-white py-20">
        <div className="container-custom">
          <span className="badge bg-white/15 text-white border-white/20 mb-4">Operating Model</span>
          <h1 className="text-4xl sm:text-5xl font-display font-bold mb-4">Company Hierarchy</h1>
          <p className="max-w-3xl text-white/80 text-lg">
            ZimAgriTrust is structured around clear accountability: governance protects the platform,
            operations keep trade moving, field agents verify trust, and finance safeguards every payment flow.
          </p>
        </div>
      </section>

      <section className="section-padding">
        <div className="container-custom">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {teams.map((team) => (
              <article key={team.title} className="bg-white rounded-3xl p-8 shadow-lg shadow-earth-200/50 border border-earth-100">
                <div className="w-14 h-14 rounded-2xl bg-primary-50 flex items-center justify-center mb-6">
                  <team.icon className="w-7 h-7 text-primary-700" />
                </div>
                <h2 className="text-xl font-bold text-earth-900 mb-3">{team.title}</h2>
                <p className="text-earth-600 leading-relaxed">{team.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
