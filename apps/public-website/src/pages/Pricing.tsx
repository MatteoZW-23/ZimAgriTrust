import React from 'react';
import { motion } from 'framer-motion';
import { Check, Zap, Shield, Truck, Users } from 'lucide-react';

const Pricing = () => {
 const plans = [
 {
 name: "Free",
 price: "$0",
 description: "Perfect for individual farmers and small buyers starting out.",
 features: [
 "Unlimited crop listings",
 "Secure escrow payments",
 "USSD access (*123#)",
 "Basic trust score",
 "Public marketplace visibility"
 ],
 cta: "Sign Up Free",
 popular: false
 },
 {
 name: "Business",
 price: "$50",
 period: "/month",
 description: "Advanced tools for agricultural enterprises and large traders.",
 features: [
 "All Free features",
 "Priority marketplace ranking",
 "Advanced analytics & trends",
 "Bulk listing tools",
 "Dedicated account manager",
 "Verified Business badge"
 ],
 cta: "Go Business",
 popular: true
 }
 ];

 const fees = [
 { label: "Platform Fee (Seller)", value: "2.5%", sub: "On every successful sale" },
 { label: "Escrow Fee (Buyer)", value: "0.5%", sub: "For payment protection" },
 { label: "Withdrawal Fee", value: "1%", sub: "Capped at $5 max" },
 { label: "Premium Listing", value: "$2", sub: "For 7-day featured status" },
 ];

 return (
 <div className="pt-24 pb-20"><div className="container-custom"><div className="text-center max-w-3xl mx-auto mb-16"><motion.h1 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 className="text-4xl sm:text-5xl font-display font-bold text-earth-900 mb-6"
 >Simple, Transparent <span className="text-primary-600">Pricing</span></motion.h1><motion.p 
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.1 }}
 className="text-lg text-earth-600"
 >No hidden costs. No surprise charges. We only succeed when you do.
 </motion.p></div>
<div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto mb-20">{plans.map((plan, i) => (
 <motion.div
 key={plan.name}
 initial={{ opacity: 0, scale: 0.95 }}
 animate={{ opacity: 1, scale: 1 }}
 transition={{ delay: i * 0.1 }}
 className={`relative bg-white rounded-3xl p-8 shadow-xl border-2 ${plan.popular ? 'border-primary-500' : 'border-earth-100'}`}
 >{plan.popular && (
 <div className="absolute top-0 right-8 -translate-y-1/2 bg-primary-600 text-white px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest">Most Popular
 </div>)}
 <h3 className="text-2xl font-bold text-earth-800 mb-2">{plan.name}</h3><div className="flex items-baseline gap-1 mb-4"><span className="text-5xl font-black text-earth-900">{plan.price}</span>{plan.period && <span className="text-earth-500 font-bold">{plan.period}</span>}
 </div><p className="text-earth-600 mb-8 font-medium">{plan.description}</p>
 <ul className="space-y-4 mb-8">{plan.features.map(feat => (
 <li key={feat} className="flex items-start gap-3 text-earth-700 font-medium"><div className="w-5 h-5 rounded-full bg-primary-100 flex items-center justify-center shrink-0 mt-0.5"><Check className="w-3 h-3 text-primary-600" /></div>{feat}
 </li>))}
 </ul>
<button className={`w-full py-4 rounded-2xl font-black transition-all ${plan.popular ? 'bg-primary-600 text-white hover:bg-primary-700 shadow-lg shadow-primary-200' : 'bg-earth-100 text-earth-700 hover:bg-earth-200'}`}>{plan.cta}
 </button></motion.div>))}
 </div>
<div className="bg-earth-900 rounded-[3rem] p-12 text-white relative overflow-hidden"><div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/10 blur-[100px] rounded-full"></div><div className="absolute bottom-0 left-0 w-64 h-64 bg-secondary-500/10 blur-[100px] rounded-full"></div>
<div className="relative z-10"><h2 className="text-3xl font-bold mb-12 text-center">Transaction Fees</h2><div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">{fees.map((fee, i) => (
 <div key={i} className="text-center"><p className="text-earth-400 font-bold uppercase tracking-widest text-xs mb-2">{fee.label}</p><p className="text-4xl font-black text-primary-500 mb-2">{fee.value}</p><p className="text-sm text-earth-300 font-medium">{fee.sub}</p></div>))}
 </div><div className="mt-12 pt-12 border-t border-white/10 text-center"><p className="text-earth-400 max-w-2xl mx-auto italic">* All fees are automatically deducted from the payout or escrow amount. 
 Prices are in USD. Exchange rates for EcoCash/OneMoney are calculated at the time of transaction.
 </p></div></div></div></div></div>);
};

export default Pricing;
