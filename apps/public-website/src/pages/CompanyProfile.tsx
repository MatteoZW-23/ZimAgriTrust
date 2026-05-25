import React, { useState } from "react";
import {
 Award,
 Briefcase,
 Globe,
 ShieldCheck,
 Mail,
 Phone,
 X,
 Users,
 ArrowRight,
 Building2,
 TrendingUp,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const stakeholders = [
 {
 title: "Farmers",
 description:
 "Direct market access, fair pricing, and secure payment protection.",
 icon: Users,
 },
 {
 title: "Buyers",
 description:
 "Reliable sourcing, verified quality, and transparent transactions.",
 icon: Briefcase,
 },
 {
 title: "Logistics",
 description:
 "Optimized delivery coordination and consistent transport demand.",
 icon: Globe,
 },
];

const stats = [
 {
 title: "Established",
 value: "2024",
 subtitle: "Harare, Zimbabwe",
 icon: Building2,
 },
 {
 title: "Market Reach",
 value: "10 Provinces",
 subtitle: "Nationwide Operations",
 icon: Globe,
 },
 {
 title: "Trade Security",
 value: "95%",
 subtitle: "Risk Reduction",
 icon: ShieldCheck,
 },
 {
 title: "Growth",
 value: "$5M+",
 subtitle: "Trade Volume",
 icon: TrendingUp,
 },
];

function CompanyProfile() {
 const [showContactModal, setShowContactModal] = useState(false);

 return (
 <div className="min-h-screen bg-gray-50">{/* HERO */}
 <section className="bg-gradient-to-r from-green-700 to-green-900 text-white pt-36 pb-24"><div className="max-w-7xl mx-auto px-6"><motion.div
 initial={{ opacity: 0, y: 40 }}
 animate={{ opacity: 1, y: 0 }}
 className="max-w-4xl"
 ><span className="inline-flex items-center rounded-full bg-white/10 backdrop-blur-sm px-4 py-2 text-sm font-medium mb-6">Corporate Profile
 </span>
<h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6">ZimAgriTrust Limited
 </h1>
<p className="text-xl text-green-100 leading-relaxed max-w-3xl">Zimbabwe’s pioneer in digital agricultural trade, logistics,
 and secure financial settlement infrastructure.
 </p></motion.div></div></section>
{/* MAIN CONTENT */}
 <section className="py-24"><div className="max-w-7xl mx-auto px-6"><div className="grid lg:grid-cols-[1fr_360px] gap-16">{/* LEFT SIDE */}
 <div>{/* EXECUTIVE SUMMARY */}
 <motion.div
 initial={{ opacity: 0, y: 30 }}
 animate={{ opacity: 1, y: 0 }}
 className="mb-20"
 ><h2 className="text-4xl font-bold text-gray-900 mb-6">Executive Summary
 </h2>
<div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-10"><p className="text-lg text-gray-600 leading-relaxed">ZimAgriTrust Limited is a leading agricultural technology
 company headquartered in Harare, Zimbabwe. We have pioneered
 an integrated marketplace that combines agricultural trade,
 logistics coordination, and secure escrow-based financial
 settlement into one unified ecosystem.
 </p></div></motion.div>
{/* BUSINESS MODEL */}
 <motion.div
 initial={{ opacity: 0, y: 30 }}
 animate={{ opacity: 1, y: 0 }}
 className="mb-20"
 ><h2 className="text-4xl font-bold text-gray-900 mb-10">Business Model
 </h2>
<div className="grid md:grid-cols-3 gap-8">{stakeholders.map((item, index) => (
 <motion.div
 key={index}
 whileHover={{ y: -6 }}
 className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8"
 ><div className="w-14 h-14 rounded-2xl bg-green-100 flex items-center justify-center mb-6"><item.icon className="w-7 h-7 text-green-700" /></div>
<h3 className="text-2xl font-semibold text-gray-900 mb-4">{item.title}
 </h3>
<p className="text-gray-600 leading-relaxed">{item.description}
 </p></motion.div>))}
 </div></motion.div>
{/* OPERATIONAL EXCELLENCE */}
 <motion.div
 initial={{ opacity: 0, y: 30 }}
 animate={{ opacity: 1, y: 0 }}
 ><h2 className="text-4xl font-bold text-gray-900 mb-6">Operational Excellence
 </h2>
<div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-10"><p className="text-lg text-gray-600 leading-relaxed mb-6">Our escrow-powered transaction infrastructure ensures that
 payments are only released upon successful verification and
 delivery confirmation.
 </p>
<div className="bg-green-50 border-l-4 border-green-700 rounded-r-2xl p-8"><p className="text-2xl font-semibold italic text-green-900 leading-relaxed">“Reducing agricultural trade risk by over 95% compared
 to traditional informal marketplaces.”
 </p></div></div></motion.div></div>
{/* SIDEBAR */}
 <aside className="space-y-8">{/* QUICK FACTS */}
 <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8"><h3 className="text-2xl font-bold text-gray-900 mb-8">Quick Facts
 </h3>
<div className="space-y-8">{stats.map((item, index) => (
 <div
 key={index}
 className="flex items-center gap-5"
 ><div className="w-14 h-14 rounded-2xl bg-green-100 flex items-center justify-center"><item.icon className="w-6 h-6 text-green-700" /></div>
<div><p className="text-sm text-gray-500 mb-1">{item.title}
 </p>
<h4 className="text-2xl font-bold text-gray-900">{item.value}
 </h4>
<p className="text-gray-600 text-sm">{item.subtitle}
 </p></div></div>))}
 </div></div>
{/* CERTIFICATION */}
 <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8"><div className="flex items-center gap-4 mb-6"><div className="w-14 h-14 rounded-2xl bg-green-100 flex items-center justify-center"><Award className="w-7 h-7 text-green-700" /></div>
<div><h3 className="text-xl font-bold text-gray-900">Certified Operations
 </h3>
<p className="text-gray-600">AMA & ZAMACE Standards
 </p></div></div>
<p className="text-gray-600 leading-relaxed">We maintain compliance with recognized agricultural and
 commodity trading standards in Zimbabwe.
 </p></div>
{/* CTA */}
 <div className="bg-gradient-to-br from-green-700 to-green-900 rounded-3xl p-8 text-white"><h3 className="text-3xl font-bold mb-4">Partner With Us
 </h3>
<p className="text-green-100 leading-relaxed mb-8">Explore institutional partnerships and collaborative
 opportunities with ZimAgriTrust.
 </p>
<button
 onClick={() => setShowContactModal(true)}
 className="w-full bg-white text-green-700 hover:bg-green-50 transition-colors rounded-2xl px-6 py-4 font-semibold flex items-center justify-center gap-2"
 >Contact Relations
 <ArrowRight className="w-5 h-5" /></button></div></aside></div></div></section>
{/* CONTACT MODAL */}
 <AnimatePresence>{showContactModal && (
 <motion.div
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 exit={{ opacity: 0 }}
 onClick={() => setShowContactModal(false)}
 className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center px-6"
 ><motion.div
 initial={{ scale: 0.95, opacity: 0 }}
 animate={{ scale: 1, opacity: 1 }}
 exit={{ scale: 0.95, opacity: 0 }}
 onClick={(e) => e.stopPropagation()}
 className="bg-white rounded-3xl p-10 max-w-lg w-full relative"
 ><button
 onClick={() => setShowContactModal(false)}
 className="absolute top-5 right-5 w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors"
 ><X className="w-5 h-5 text-gray-700" /></button>
<h2 className="text-3xl font-bold text-gray-900 mb-3">Partner Relations
 </h2>
<p className="text-gray-600 mb-10">Connect with our institutional partnerships team.
 </p>
<div className="space-y-5"><a
 href="tel:+263788272020"
 className="flex items-center gap-5 bg-gray-50 hover:bg-green-50 transition-colors rounded-2xl p-5"
 ><div className="w-14 h-14 rounded-2xl bg-green-100 flex items-center justify-center"><Phone className="w-6 h-6 text-green-700" /></div>
<div><h4 className="font-semibold text-gray-900">Partnerships Hotline
 </h4>
<p className="text-gray-600">+263 788 272 020
 </p></div></a>
<a
 href="mailto:partnerships@zimagritrust.co.zw"
 className="flex items-center gap-5 bg-gray-50 hover:bg-green-50 transition-colors rounded-2xl p-5"
 ><div className="w-14 h-14 rounded-2xl bg-green-100 flex items-center justify-center"><Mail className="w-6 h-6 text-green-700" /></div>
<div><h4 className="font-semibold text-gray-900">Email Us
 </h4>
<p className="text-gray-600">partnerships@zimagritrust.co.zw
 </p></div></a></div>
<div className="mt-10 pt-6 border-t border-gray-100 text-center"><h4 className="font-semibold text-gray-900 mb-2">Business Hours
 </h4>
<p className="text-gray-600 text-sm">Monday – Friday: 8:00 AM – 5:00 PM
 </p>
<p className="text-gray-500 text-sm mt-2">Partnership inquiries are usually answered within 24 hours.
 </p></div></motion.div></motion.div>)}
 </AnimatePresence></div>);
}

export default CompanyProfile;