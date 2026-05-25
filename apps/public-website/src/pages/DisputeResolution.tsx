import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
 ShieldAlert,
 Scale,
 FileSearch,
 Gavel,
 MessageSquare,
 CheckCircle2,
} from "lucide-react";

const disputeLevels = [
 {
 title: "Level 1: Direct Negotiation",
 time: "24 Hours",
 description:
 "Users attempt to resolve issues directly through platform chat before escalation.",
 },
 {
 title: "Level 2: Agent Mediation",
 time: "48 Hours",
 description:
 "Certified agents collect evidence, interview parties, and recommend resolutions.",
 },
 {
 title: "Level 3: Admin Review",
 time: "7 Days",
 description:
 "Admin reviews all case notes and may uphold or overturn decisions.",
 },
 {
 title: "Level 4: Legal Arbitration",
 time: "Over $1,000",
 description:
 "Binding arbitration under Zimbabwean law for major disputes.",
 },
];

const disputeTypes = [
 {
 title: "Quality Disputes",
 percent: "60%",
 desc: "Issues with freshness, crop grade, or product condition.",
 },
 {
 title: "Quantity Disputes",
 percent: "20%",
 desc: "Delivered quantity differs from agreed amount.",
 },
 {
 title: "Delivery Disputes",
 percent: "15%",
 desc: "Late delivery or non-arrival of goods.",
 },
 {
 title: "Payment Disputes",
 percent: "5%",
 desc: "Escrow or payment processing issues.",
 },
];

const evidenceItems = [
 "Listing photos",
 "Delivery photos",
 "Agent verification report",
 "Weighing scale photos",
 "Chat history",
 "Delivery receipts",
 "Tracking logs",
];

function DisputeResolution() {
 return (
 <div className="min-h-screen bg-gray-50">{/* HEADER */}
 <header className="fixed top-0 left-0 w-full z-50 bg-white/90 backdrop-blur-md border-b border-gray-100"><div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between"><Link
 to="/"
 className="flex items-center gap-3 text-green-700 font-bold text-xl"
 ><img
 src="/logo.png"
 alt="ZimAgriTrust"
 className="h-10 w-auto"
 /><span>ZimAgriTrust</span></Link>
<nav className="hidden md:flex items-center gap-8 text-gray-600 font-medium"><Link to="/" className="hover:text-green-700 transition-colors">Home
 </Link>
<Link
 to="/how-it-works"
 className="hover:text-green-700 transition-colors"
 >How It Works
 </Link>
<Link
 to="/help"
 className="hover:text-green-700 transition-colors"
 >Help
 </Link></nav></div></header>
{/* HERO */}
 <section className="bg-gradient-to-r from-green-700 to-green-900 text-white pt-36 pb-24"><div className="max-w-6xl mx-auto px-6"><motion.div
 initial={{ opacity: 0, y: 30 }}
 animate={{ opacity: 1, y: 0 }}
 className="max-w-3xl"
 ><div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm mb-6"><ShieldAlert className="w-4 h-4" /><span className="text-sm font-medium">Marketplace Protection
 </span></div>
<h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6">Dispute Resolution Process
 </h1>
<p className="text-xl text-green-100 leading-relaxed">Fair, transparent, and structured conflict resolution for farmers,
 buyers, and logistics partners.
 </p></motion.div></div></section>
{/* MAIN CONTENT */}
 <section className="py-20"><div className="max-w-6xl mx-auto px-6">{/* INTRO CARD */}
 <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-10 md:p-14 mb-16"><p className="text-lg text-gray-600 leading-relaxed">ZimAgriTrust provides a structured dispute resolution framework
 designed to protect both farmers and buyers while maintaining
 marketplace trust and accountability.
 </p></div>
{/* ESCALATION PATH */}
 <section className="mb-24"><div className="flex items-center gap-3 mb-10"><Scale className="w-8 h-8 text-green-700" />
<h2 className="text-4xl font-bold text-gray-900">Escalation Path
 </h2></div>
<div className="grid md:grid-cols-2 gap-8">{disputeLevels.map((item, index) => (
 <motion.div
 key={index}
 whileHover={{ y: -5 }}
 className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8"
 ><div className="flex items-center justify-between mb-5"><span className="text-sm font-semibold bg-green-100 text-green-700 px-3 py-1 rounded-full">{item.time}
 </span>
<span className="text-5xl font-bold text-gray-100">0{index + 1}
 </span></div>
<h3 className="text-2xl font-semibold text-gray-900 mb-4">{item.title}
 </h3>
<p className="text-gray-600 leading-relaxed">{item.description}
 </p></motion.div>))}
 </div></section>
{/* COMMON DISPUTES */}
 <section className="mb-24"><div className="flex items-center gap-3 mb-10"><MessageSquare className="w-8 h-8 text-green-700" />
<h2 className="text-4xl font-bold text-gray-900">Common Dispute Types
 </h2></div>
<div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">{disputeTypes.map((item, index) => (
 <div
 key={index}
 className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8"
 ><div className="text-5xl font-bold text-green-700 mb-5">{item.percent}
 </div>
<h3 className="text-xl font-semibold text-gray-900 mb-3">{item.title}
 </h3>
<p className="text-gray-600 leading-relaxed">{item.desc}
 </p></div>))}
 </div></section>
{/* EVIDENCE */}
 <section className="mb-24"><div className="flex items-center gap-3 mb-10"><FileSearch className="w-8 h-8 text-green-700" />
<h2 className="text-4xl font-bold text-gray-900">Evidence Required
 </h2></div>
<div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-10"><div className="grid md:grid-cols-2 gap-6">{evidenceItems.map((item, index) => (
 <div
 key={index}
 className="flex items-center gap-3 text-gray-700"
 ><CheckCircle2 className="w-5 h-5 text-green-700" />
<span>{item}</span></div>))}
 </div></div></section>
{/* LEGAL */}
 <section><div className="flex items-center gap-3 mb-10"><Gavel className="w-8 h-8 text-green-700" />
<h2 className="text-4xl font-bold text-gray-900">Legal & Contact
 </h2></div>
<div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-10 space-y-5"><p className="text-gray-600 leading-relaxed">Arbitration processes are governed by Zimbabwean law and
 administered fairly and independently.
 </p>
<div><p className="font-semibold text-gray-900">Dispute Support Email
 </p>
<p className="text-gray-600">disputes@zimagritrust.com
 </p></div>
<div><p className="font-semibold text-gray-900">WhatsApp Support
 </p>
<p className="text-gray-600">+263 71 735 8956
 </p></div></div></section></div></section>
{/* FOOTER */}
 <footer className="border-t border-gray-200 bg-white py-8"><div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4"><p className="text-gray-500 text-sm">© 2026 ZimAgriTrust. All rights reserved.
 </p>
<div className="flex items-center gap-6 text-sm text-gray-500"><Link to="/privacy-policy" className="hover:text-green-700">Privacy Policy
 </Link>
<Link to="/terms" className="hover:text-green-700">Terms
 </Link></div></div></footer></div>);
}

export default DisputeResolution;