import React from 'react';
import { Smartphone, ShieldCheck, Truck, Users, BarChart3, Clock } from 'lucide-react';

export default function Features() {
  const features = [
    {
      icon: <Smartphone size={32} />,
      title: "Trade Anywhere",
      desc: "Use our website, mobile app, WhatsApp, or dial *123# on any phone. Works even without internet."
    },
    {
      icon: <ShieldCheck size={32} />,
      title: "Secure Payments",
      desc: "Your money is held safely in escrow until you receive your goods. Protected for both buyers and sellers."
    },
    {
      icon: <Truck size={32} />,
      title: "Delivery Included",
      desc: "Get instant shipping quotes and track your delivery in real-time from pickup to drop-off."
    },
    {
      icon: <Users size={32} />,
      title: "Local Agents",
      desc: "Our trained agents in every province help with quality checks, verification, and support."
    },
    {
      icon: <BarChart3 size={32} />,
      title: "Live Market Prices",
      desc: "See current crop prices from ZAMACE and GMB to help you decide when and where to sell."
    },
    {
      icon: <Clock size={32} />,
      title: "Fast Payouts",
      desc: "Farmers get paid quickly once delivery is confirmed. No long waits for your money."
    }
  ];

  return (
    <section className="features-section" id="features">
      <div className="container">
        <div className="section-header fade-in">
          <span className="section-label">Why Choose Us</span>
          <h2>Simple, Safe, and Direct</h2>
          <p>Everything you need to buy or sell crops without the hassle of middlemen.</p>
        </div>

        <div className="features-grid">
          {features.map((f, i) => (
            <div key={i} className="feature-card-premium fade-in">
              <div className="feature-icon-wrapper">
                {f.icon}
              </div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>

        <div className="how-it-works-banner fade-in" id="how-it-works">
          <div className="banner-text-simple">
            <h2>No Smartphone? No Problem.</h2>
            <p>Dial <strong>*123#</strong> on any mobile phone to buy, sell, or check prices. No internet required.</p>
            <div className="ussd-simple">Works on all networks</div>
          </div>
        </div>
      </div>
    </section>
  );
}
