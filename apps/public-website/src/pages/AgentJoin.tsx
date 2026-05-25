import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
 Users,
 CheckCircle,
 ClipboardCheck,
 DollarSign,
 ArrowRight,
 Phone,
 Mail,
 GraduationCap,
} from "lucide-react";

const benefits = [
 {
 title: "Support Farmers",
 description:
 "Help farmers list crops, manage inventory, and set fair prices.",
 icon: Users,
 },
 {
 title: "Assist Buyers",
 description:
 "Guide buyers through the marketplace and facilitate transactions.",
 icon: CheckCircle,
 },
 {
 title: "Verify Quality",
 description:
 "Inspect crop quality, quantities, and delivery standards.",
 icon: ClipboardCheck,
 },
 {
 title: "Earn Commission",
 description:
 "Receive commissions for every successful transaction facilitated.",
 icon: DollarSign,
 },
];

const steps = [
 {
 step: "01",
 title: "Apply Online",
 description:
 "Submit your details, location, and agricultural experience.",
 },
 {
 step: "02",
 title: "Interview",
 description:
 "Complete a short phone or video interview with our team.",
 },
 {
 step: "03",
 title: "Agent Academy",
 description:
 "Participate in a 2-week training program covering operations and standards.",
 },
 {
 step: "04",
 title: "Field Assessment",
 description:
 "Shadow experienced agents and complete a practical evaluation.",
 },
 {
 step: "05",
 title: "Certification",
 description:
 "Receive official certification and begin supporting your community.",
 },
];

const requirements = [
 "Resident of Zimbabwe with valid ID",
 "Smartphone with internet access",
 "Strong communication skills",
 "Knowledge of agricultural practices",
 "Passion for rural development",
];

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

async function submitAgentApplication(payload) {
 const res = await fetch(`${API_BASE}/recruitment/apply`, {
 method: "POST",
 headers: { "Content-Type": "application/json" },
 body: JSON.stringify(payload),
 });
 if (!res.ok) {
 let detail = "Submission failed";
 try {
 const j = await res.json();
 detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
 } catch {}
 throw new Error(detail);
 }
 return res.json();
}

function formatPhone(p) {
 const trimmed = p.trim();
 if (trimmed.startsWith("+")) return trimmed.replace(/\s/g, "");
 return `+263${trimmed.replace(/^0+/, "").replace(/\s/g, "")}`;
}

export default function AgentJoin() {
 const navigate = useNavigate();
 const [submitted, setSubmitted] = useState(false);
 const [submitError, setSubmitError] = useState("");
 const [submitting, setSubmitting] = useState(false);
 const [applicationId, setApplicationId] = useState(null);

 // Form fields
 const [fullName, setFullName] = useState("");
 const [phone, setPhone] = useState("");
 const [email, setEmail] = useState("");
 const [province, setProvince] = useState("");
 const [district, setDistrict] = useState("");
 const [nationalId, setNationalId] = useState("");
 const [experienceYears, setExperienceYears] = useState(1);
 const [hasSmartphone, setHasSmartphone] = useState(true);
 const [hasTransport, setHasTransport] = useState(false);
 const [transportType, setTransportType] = useState("");
 const [motivation, setMotivation] = useState("");

 async function handleSubmit(e) {
 e.preventDefault();
 setSubmitError("");
 setSubmitting(true);
 try {
 const res = await submitAgentApplication({
 full_name: fullName.trim(),
 phone_number: formatPhone(phone),
 national_id: nationalId.trim(),
 province,
 district: district.trim() || province,
 has_smartphone: hasSmartphone,
 has_transport: hasTransport,
 transport_type: hasTransport ? transportType || null : null,
 agri_experience_years: parseInt(experienceYears, 10) || 0,
 specializations: ["verification"], // can be expanded later
 });
 // Stash motivation + email locally for the back office to pick up later
 try {
 localStorage.setItem(`agent_app_${res.id}`, JSON.stringify({
 email,
 motivation,
 submitted_at: new Date().toISOString(),
 }));
 } catch {}
 setApplicationId(res.id);
 setSubmitted(true);
 window.scrollTo({ top: 0, behavior: "smooth" });
 } catch (err) {
 setSubmitError(err.message);
 } finally {
 setSubmitting(false);
 }
 }

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
 to="/about"
 className="hover:text-green-700 transition-colors"
 >About
 </Link></nav></div></header>
{/* HERO */}
 <section className="bg-gradient-to-r from-green-700 to-green-900 text-white pt-36 pb-24"><div className="max-w-7xl mx-auto px-6"><motion.div
 initial={{ opacity: 0, y: 40 }}
 animate={{ opacity: 1, y: 0 }}
 className="max-w-4xl"
 ><span className="inline-flex items-center gap-2 rounded-full bg-white/10 backdrop-blur-sm px-4 py-2 text-sm font-medium mb-6"><GraduationCap className="w-4 h-4" />Agent Academy
 </span>
<h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6">Join the Agent Academy
 </h1>
<p className="text-xl text-green-100 leading-relaxed max-w-3xl">Become a certified ZimAgriTrust Agent and support agricultural
 communities across Zimbabwe.
 </p></motion.div></div></section>
{/* BENEFITS */}
 <section className="py-24"><div className="max-w-7xl mx-auto px-6"><div className="mb-14"><h2 className="text-4xl font-bold text-gray-900 mb-4">What Does an Agent Do?
 </h2>
<p className="text-lg text-gray-600">Agents bridge the gap between farmers, buyers, and logistics
 providers.
 </p></div>
<div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">{benefits.map((item, index) => (
 <motion.div
 key={index}
 whileHover={{ y: -6 }}
 className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8"
 ><div className="w-14 h-14 rounded-2xl bg-green-100 flex items-center justify-center mb-6"><item.icon className="w-7 h-7 text-green-700" /></div>
<h3 className="text-2xl font-semibold text-gray-900 mb-4">{item.title}
 </h3>
<p className="text-gray-600 leading-relaxed">{item.description}
 </p></motion.div>))}
 </div></div></section>
{/* CERTIFICATION JOURNEY */}
 <section className="py-24 bg-white"><div className="max-w-6xl mx-auto px-6"><div className="mb-14 text-center"><h2 className="text-4xl font-bold text-gray-900 mb-4">Certification Journey
 </h2>
<p className="text-lg text-gray-600">Follow these steps to become a certified field agent.
 </p></div>
<div className="space-y-8">{steps.map((item, index) => (
 <motion.div
 key={index}
 whileHover={{ scale: 1.01 }}
 className="bg-gray-50 border border-gray-100 rounded-3xl p-8 flex flex-col md:flex-row md:items-center gap-8"
 ><div className="text-6xl font-bold text-green-700 min-w-[120px]">{item.step}
 </div>
<div><h3 className="text-2xl font-semibold text-gray-900 mb-3">{item.title}
 </h3>
<p className="text-gray-600 leading-relaxed">{item.description}
 </p></div></motion.div>))}
 </div></div></section>
{/* REQUIREMENTS */}
 <section className="py-24"><div className="max-w-5xl mx-auto px-6"><div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-10"><h2 className="text-4xl font-bold text-gray-900 mb-10">Requirements
 </h2>
<div className="grid md:grid-cols-2 gap-6">{requirements.map((item, index) => (
 <div
 key={index}
 className="flex items-center gap-4"
 ><CheckCircle className="w-6 h-6 text-green-700" />
<span className="text-gray-700 text-lg">{item}
 </span></div>))}
 </div></div></div></section>
{/* APPLICATION FORM */}
 <section className="pb-24"><div className="max-w-5xl mx-auto px-6"><div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-10 md:p-14"><AnimatePresence mode="wait">{!submitted ? (
 <motion.div
 key="form"
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 exit={{ opacity: 0 }}
 ><h2 className="text-4xl font-bold text-gray-900 mb-4">Apply Now
 </h2>
<p className="text-gray-600 mb-10">Complete the application form to begin your certification
 journey.
 </p>
{submitError && (
 <div className="mb-6 rounded-2xl bg-red-50 border border-red-200 p-4 text-red-700"><strong>Submission failed:</strong> {submitError}
 </div>)}

 <form onSubmit={handleSubmit} className="space-y-8"><div className="grid md:grid-cols-2 gap-6"><div><label className="block text-sm font-medium text-gray-700 mb-2">Full Name
 </label><input
 type="text"
 required
 value={fullName}
 onChange={(e) => setFullName(e.target.value)}
 placeholder="e.g. Tendai Moyo"
 className="w-full rounded-2xl border border-gray-200 px-5 py-4 focus:outline-none focus:ring-2 focus:ring-green-600"
 /></div>
<div><label className="block text-sm font-medium text-gray-700 mb-2">Phone Number
 </label><input
 type="tel"
 required
 value={phone}
 onChange={(e) => setPhone(e.target.value)}
 placeholder="+263 77 123 4567"
 className="w-full rounded-2xl border border-gray-200 px-5 py-4 focus:outline-none focus:ring-2 focus:ring-green-600"
 /></div></div>
<div className="grid md:grid-cols-2 gap-6"><div><label className="block text-sm font-medium text-gray-700 mb-2">Email Address
 </label><input
 type="email"
 required
 value={email}
 onChange={(e) => setEmail(e.target.value)}
 placeholder="you@example.com"
 className="w-full rounded-2xl border border-gray-200 px-5 py-4 focus:outline-none focus:ring-2 focus:ring-green-600"
 /></div>
<div><label className="block text-sm font-medium text-gray-700 mb-2">National ID
 </label><input
 type="text"
 required
 value={nationalId}
 onChange={(e) => setNationalId(e.target.value)}
 placeholder="63-1234567X12"
 className="w-full rounded-2xl border border-gray-200 px-5 py-4 focus:outline-none focus:ring-2 focus:ring-green-600"
 /></div></div>
<div className="grid md:grid-cols-2 gap-6"><div><label className="block text-sm font-medium text-gray-700 mb-2">Province
 </label><select
 required
 value={province}
 onChange={(e) => setProvince(e.target.value)}
 className="w-full rounded-2xl border border-gray-200 px-5 py-4 focus:outline-none focus:ring-2 focus:ring-green-600"
 ><option value="">Select Province</option><option>Harare</option><option>Bulawayo</option><option>Manicaland</option><option>Mashonaland Central</option><option>Mashonaland East</option><option>Mashonaland West</option><option>Masvingo</option><option>Matabeleland North</option><option>Matabeleland South</option><option>Midlands</option></select></div>
<div><label className="block text-sm font-medium text-gray-700 mb-2">District
 </label><input
 type="text"
 required
 value={district}
 onChange={(e) => setDistrict(e.target.value)}
 placeholder="e.g. Harare East"
 className="w-full rounded-2xl border border-gray-200 px-5 py-4 focus:outline-none focus:ring-2 focus:ring-green-600"
 /></div></div>
<div className="grid md:grid-cols-2 gap-6"><div><label className="block text-sm font-medium text-gray-700 mb-2">Years of Agriculture Experience
 </label><input
 type="number"
 min={0}
 required
 value={experienceYears}
 onChange={(e) => setExperienceYears(e.target.value)}
 className="w-full rounded-2xl border border-gray-200 px-5 py-4 focus:outline-none focus:ring-2 focus:ring-green-600"
 /></div><div><label className="block text-sm font-medium text-gray-700 mb-2">Transport (if any)
 </label><input
 type="text"
 value={transportType}
 onChange={(e) => {
 setTransportType(e.target.value);
 setHasTransport(e.target.value.trim().length > 0);
 }}
 placeholder="Motorbike, car, bicycle..."
 className="w-full rounded-2xl border border-gray-200 px-5 py-4 focus:outline-none focus:ring-2 focus:ring-green-600"
 /></div></div>
<div className="flex items-center gap-3"><input
 type="checkbox"
 id="hasSmartphone"
 checked={hasSmartphone}
 onChange={(e) => setHasSmartphone(e.target.checked)}
 className="w-5 h-5 text-green-700"
 /><label htmlFor="hasSmartphone" className="text-gray-700">I have a smartphone (required for the agent app)
 </label></div>
<div><label className="block text-sm font-medium text-gray-700 mb-2">Why do you want to become an agent?
 </label><textarea
 rows="5"
 required
 value={motivation}
 onChange={(e) => setMotivation(e.target.value)}
 placeholder="Tell us about your motivation and experience..."
 className="w-full rounded-2xl border border-gray-200 px-5 py-4 focus:outline-none focus:ring-2 focus:ring-green-600"
 /></div>
<button
 type="submit"
 disabled={submitting}
 className="w-full bg-green-700 hover:bg-green-800 disabled:bg-gray-400 transition-colors text-white rounded-2xl px-6 py-4 font-semibold flex items-center justify-center gap-2"
 >{submitting ? "Submitting..." : "Submit Application"}
 <ArrowRight className="w-5 h-5" /></button></form></motion.div>) : (
 <motion.div
 key="success"
 initial={{ opacity: 0, scale: 0.95 }}
 animate={{ opacity: 1, scale: 1 }}
 className="text-center"
 ><div className="w-24 h-24 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-8"><CheckCircle className="w-12 h-12 text-green-700" /></div>
<h2 className="text-4xl font-bold text-gray-900 mb-4">Application Submitted
 </h2>
<p className="text-lg text-gray-600 leading-relaxed max-w-2xl mx-auto mb-6">Thank you for applying to the Agent Academy. Our team will
 review your application and contact you within 5 business
 days.
 </p>
{applicationId && (
 <div className="bg-gray-50 rounded-2xl px-6 py-4 inline-block mb-10"><div className="text-xs uppercase tracking-wider text-gray-500 mb-1">Application ID</div><code className="text-sm font-mono text-gray-800">{applicationId}</code></div>)}

 <div className="block" />
<button
 onClick={() => navigate("/")}
 className="bg-green-700 hover:bg-green-800 transition-colors text-white rounded-2xl px-8 py-4 font-semibold"
 >Return Home
 </button></motion.div>)}
 </AnimatePresence></div></div></section>
{/* CONTACT */}
 <section className="pb-24"><div className="max-w-5xl mx-auto px-6"><div className="bg-gradient-to-r from-green-700 to-green-900 rounded-3xl p-10 text-white"><h2 className="text-4xl font-bold mb-4">Questions?
 </h2>
<p className="text-green-100 text-lg mb-10">Contact our recruitment team for more information.
 </p>
<div className="grid md:grid-cols-2 gap-6"><div className="bg-white/10 rounded-2xl p-6 flex items-center gap-5"><div className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center"><Mail className="w-6 h-6" /></div>
<div><p className="text-sm text-green-100 mb-1">Recruitment Email
 </p>
<h3 className="text-xl font-semibold">recruitment@zimagritrust.com
 </h3></div></div>
<div className="bg-white/10 rounded-2xl p-6 flex items-center gap-5"><div className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center"><Phone className="w-6 h-6" /></div>
<div><p className="text-sm text-green-100 mb-1">Recruitment Hotline
 </p>
<h3 className="text-xl font-semibold">+263 788 272 020
 </h3></div></div></div></div></div></section></div>);
}