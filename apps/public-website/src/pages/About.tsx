import React from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
 ShieldCheck,
 Target,
 Award,
 Users,
 Sprout,
 TrendingUp,
 ArrowRight,
} from "lucide-react";

const values = [
 {
 title: "Trust",
 description:
 "Built through transparency, verified identity, and escrow protection.",
 icon: ShieldCheck,
 },
 {
 title: "Fairness",
 description:
 "Equal market access and fair opportunities for every stakeholder.",
 icon: Target,
 },
 {
 title: "Quality",
 description:
 "Maintaining agricultural standards across the entire value chain.",
 icon: Award,
 },
];

const stats = [
 {
 value: "10,000+",
 label: "Active Farmers",
 icon: Users,
 },
 {
 value: "$5M+",
 label: "Trade Volume",
 icon: TrendingUp,
 },
 {
 value: "10 Provinces",
 label: "National Coverage",
 icon: Sprout,
 },
];

function About({ setAuthOpen }) {
 const navigate = useNavigate();

 const handleGetStarted = () => {
 if (setAuthOpen) {
 setAuthOpen(true);
 } else {
 navigate("/");
 }
 };

 return (
 <div className="min-h-screen bg-gray-50">{/* HERO */}
 <section className="bg-gradient-to-r from-green-700 to-green-900 text-white pt-36 pb-24"><div className="max-w-7xl mx-auto px-6"><motion.div
 initial={{ opacity: 0, y: 40 }}
 animate={{ opacity: 1, y: 0 }}
 className="max-w-4xl"
 ><span className="inline-flex items-center rounded-full bg-white/10 backdrop-blur-sm px-4 py-2 text-sm font-medium mb-6">Our Story
 </span>
<h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6">Empowering Zimbabwe's Agricultural Future
 </h1>
<p className="text-xl text-green-100 leading-relaxed max-w-3xl">We are building the digital infrastructure that transforms how
 agriculture works across Zimbabwe through trust, transparency,
 and technology.
 </p></motion.div></div></section>
{/* MAIN CONTENT */}
 <section className="py-24"><div className="max-w-7xl mx-auto px-6"><div className="grid lg:grid-cols-[1fr_360px] gap-16">{/* LEFT CONTENT */}
 <div>{/* MISSION */}
 <motion.div
 initial={{ opacity: 0, y: 30 }}
 animate={{ opacity: 1, y: 0 }}
 className="mb-20"
 ><h2 className="text-4xl font-bold text-gray-900 mb-6">Our Mission
 </h2>
<p className="text-lg text-gray-600 leading-relaxed mb-8">ZimAgriTrust is revolutionizing Zimbabwe’s agricultural
 marketplace by connecting farmers directly with buyers through
 a secure, transparent, and efficient digital platform.
 </p>
<div className="bg-green-50 border-l-4 border-green-700 rounded-r-2xl p-8"><p className="text-2xl font-semibold italic text-green-900 leading-relaxed">“Our goal is to ensure no farmer is left behind in the
 digital age.”
 </p></div></motion.div>
{/* VISION */}
 <motion.div
 initial={{ opacity: 0, y: 30 }}
 animate={{ opacity: 1, y: 0 }}
 className="mb-20"
 ><h2 className="text-4xl font-bold text-gray-900 mb-6">Our Vision
 </h2>
<p className="text-lg text-gray-600 leading-relaxed">To become Africa’s leading agricultural marketplace platform,
 setting the standard for trust, transparency, and efficiency
 in agricultural trade.
 </p></motion.div>
{/* VALUES */}
 <section><h2 className="text-4xl font-bold text-gray-900 mb-10">Our Core Values
 </h2>
<div className="grid md:grid-cols-3 gap-8">{values.map((item, index) => (
 <motion.div
 key={index}
 whileHover={{ y: -6 }}
 className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8"
 ><div className="w-14 h-14 rounded-2xl bg-green-100 flex items-center justify-center mb-6"><item.icon className="w-7 h-7 text-green-700" /></div>
<h3 className="text-2xl font-semibold text-gray-900 mb-4">{item.title}
 </h3>
<p className="text-gray-600 leading-relaxed">{item.description}
 </p></motion.div>))}
 </div></section></div>
{/* SIDEBAR */}
 <aside className="space-y-8">{/* STATS */}
 <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8"><h3 className="text-2xl font-bold text-gray-900 mb-8">Marketplace Impact
 </h3>
<div className="space-y-8">{stats.map((item, index) => (
 <div
 key={index}
 className="flex items-center gap-5"
 ><div className="w-14 h-14 rounded-2xl bg-green-100 flex items-center justify-center"><item.icon className="w-6 h-6 text-green-700" /></div>
<div><h4 className="text-2xl font-bold text-gray-900">{item.value}
 </h4>
<p className="text-gray-600">{item.label}
 </p></div></div>))}
 </div></div>
{/* CTA */}
 <div className="bg-gradient-to-br from-green-700 to-green-900 rounded-3xl p-8 text-white"><h3 className="text-3xl font-bold mb-4">Ready to Trade?
 </h3>
<p className="text-green-100 leading-relaxed mb-8">Join Zimbabwe’s trusted agricultural marketplace and start
 trading securely today.
 </p>
<button
 onClick={handleGetStarted}
 className="w-full bg-white text-green-700 hover:bg-green-50 transition-colors rounded-2xl px-6 py-4 font-semibold flex items-center justify-center gap-2"
 >Get Started
 <ArrowRight className="w-5 h-5" /></button></div></aside></div></div></section></div>);
}

export default About;