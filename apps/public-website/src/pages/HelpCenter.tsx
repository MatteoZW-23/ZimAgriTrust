import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronDown, Phone, Mail, MessageSquare, Book, Shield, Zap } from 'lucide-react';

const HelpCenter = () => {
 const [activeTab, setActiveTab] = useState('general');
 const [search, setSearch] = useState('');

 const faqs = [
 {
 category: 'general',
 question: "What is ZimAgriTrust?",
 answer: "ZimAgriTrust is a digital agricultural marketplace that connects Zimbabwean farmers directly to buyers, ensuring fair prices and secure payments through an escrow system."
 },
 {
 category: 'general',
 question: "How do I create an account?",
 answer: "You can sign up via our website or mobile app. You'll need a valid Zimbabwean phone number to receive a verification code. During signup, you can choose to be a Farmer or a Buyer."
 },
 {
 category: 'payments',
 question: "What is escrow?",
 answer: "Escrow is a legal arrangement in which we hold the buyer's payment safely until the farmer delivers the crops. Once the buyer confirms receipt and quality, the funds are released to the farmer."
 },
 {
 category: 'payments',
 question: "How do I withdraw my funds?",
 answer: "Farmers can withdraw their earnings to EcoCash, OneMoney, or a registered bank account directly from the Wallet section of the app. Withdrawals are usually processed within 24 hours."
 },
 {
 category: 'logistics',
 question: "Who handles the delivery?",
 answer: "We have a network of verified transporters. When a deal is made, you can choose to arrange your own transport or request a ZimAgriTrust driver through the platform."
 },
 {
 category: 'trust',
 question: "What is the Trust Score?",
 answer: "The Trust Score (0-100) reflects a user's reliability. it is calculated based on successful transactions, quality ratings, and verification status. Higher scores lead to more business opportunities."
 }
 ];

 const filteredFaqs = faqs.filter(faq => (activeTab === 'all' || faq.category === activeTab) &&
 (faq.question.toLowerCase().includes(search.toLowerCase()) || faq.answer.toLowerCase().includes(search.toLowerCase()))
 );

 return (
 <div className="pt-24 pb-20 bg-earth-50 min-h-screen"><div className="container-custom">{/* Hero */}
 <div className="bg-primary-600 rounded-[3rem] p-12 lg:p-20 text-white text-center mb-16 relative overflow-hidden"><div className="absolute top-0 right-0 w-64 h-64 bg-white/10 blur-[80px] rounded-full"></div><div className="relative z-10 max-w-2xl mx-auto"><h1 className="text-4xl lg:text-5xl font-display font-bold mb-8">How can we help?</h1><div className="relative"><Search className="absolute left-6 top-1/2 -translate-y-1/2 text-primary-300" size={24} /><input 
 type="text" 
 placeholder="Search for articles, guides, or FAQs..."
 className="w-full bg-white/10 backdrop-blur-md border-2 border-white/20 rounded-2xl pl-16 pr-6 py-5 text-lg font-medium placeholder:text-white/60 focus:bg-white focus:text-earth-900 focus:border-white transition-all outline-none"
 value={search}
 onChange={(e) => setSearch(e.target.value)}
 /></div></div></div>
{/* Categories */}
 <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">{[
 { id: 'general', label: 'General', icon: Book },
 { id: 'payments', label: 'Payments', icon: Zap },
 { id: 'logistics', label: 'Logistics', icon: Zap }, // Use Truck if available
 { id: 'trust', label: 'Trust & Safety', icon: Shield },
 ].map(cat => (
 <button
 key={cat.id}
 onClick={() => setActiveTab(cat.id)}
 className={`flex flex-col items-center justify-center p-8 rounded-3xl border-2 transition-all ${activeTab === cat.id ? 'bg-white border-primary-500 shadow-xl shadow-primary-100 scale-105' : 'bg-white/50 border-earth-100 hover:border-earth-200'}`}
 ><div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-4 ${activeTab === cat.id ? 'bg-primary-600 text-white' : 'bg-earth-100 text-earth-500'}`}><cat.icon size={24} /></div><span className={`font-black text-sm uppercase tracking-widest ${activeTab === cat.id ? 'text-earth-900' : 'text-earth-400'}`}>{cat.label}</span></button>))}
 </div>
<div className="grid lg:grid-cols-3 gap-12">{/* FAQ Accordion */}
 <div className="lg:col-span-2 space-y-4"><h2 className="text-2xl font-bold text-earth-900 mb-8">Frequently Asked Questions</h2>{filteredFaqs.map((faq, i) => (
 <FaqItem key={i} faq={faq} />))}
 {filteredFaqs.length === 0 && (
 <div className="text-center py-12"><p className="text-earth-400 font-bold">No results found for your search.</p></div>)}
 </div>
{/* Sidebar Contact */}
 <div className="space-y-6"><div className="bg-white rounded-3xl p-8 shadow-lg border border-earth-100"><h3 className="text-xl font-bold text-earth-800 mb-6">Still need help?</h3><div className="space-y-4"><a href="tel:+263771234567" className="flex items-center gap-4 p-4 rounded-2xl bg-earth-50 hover:bg-primary-50 hover:text-primary-600 transition-all group"><div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-sm group-hover:bg-primary-600 group-hover:text-white transition-all"><Phone size={20} /></div><div><p className="text-xs font-black text-earth-400 uppercase">Call Us</p><p className="font-bold">+263 71 735 8956</p></div></a><a href="mailto:support@zimagritrust.com" className="flex items-center gap-4 p-4 rounded-2xl bg-earth-50 hover:bg-primary-50 hover:text-primary-600 transition-all group"><div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-sm group-hover:bg-primary-600 group-hover:text-white transition-all"><Mail size={20} /></div><div><p className="text-xs font-black text-earth-400 uppercase">Email Us</p><p className="font-bold">support@zimagritrust.com</p></div></a><button className="w-full flex items-center gap-4 p-4 rounded-2xl bg-earth-50 hover:bg-primary-50 hover:text-primary-600 transition-all group"><div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-sm group-hover:bg-primary-600 group-hover:text-white transition-all"><MessageSquare size={20} /></div><div><p className="text-xs font-black text-earth-400 uppercase">Live Chat</p><p className="font-bold">Available 24/7</p></div></button></div></div>
<div className="bg-earth-900 rounded-3xl p-8 text-white"><h3 className="text-xl font-bold mb-4 text-secondary-400">Agent Network</h3><p className="text-earth-300 text-sm font-medium leading-relaxed mb-6">Prefer in-person support? Our certified agents are available in every district to help with verification and platform usage.
 </p><button className="text-sm font-black underline decoration-secondary-500 underline-offset-4 hover:text-secondary-400 transition-colors">Find Agent Near You
 </button></div></div></div></div></div>);
};

const FaqItem = ({ faq }) => {
 const [isOpen, setIsOpen] = useState(false);

 return (
 <div className="bg-white rounded-2xl border border-earth-100 overflow-hidden transition-all hover:shadow-md"><button 
 onClick={() => setIsOpen(!isOpen)}
 className="w-full flex items-center justify-between p-6 text-left"
 ><span className="font-bold text-earth-800 pr-8">{faq.question}</span><ChevronDown className={`shrink-0 text-earth-300 transition-transform duration-300 ${isOpen ? 'rotate-180 text-primary-600' : ''}`} /></button><AnimatePresence>{isOpen && (
 <motion.div
 initial={{ height: 0, opacity: 0 }}
 animate={{ height: 'auto', opacity: 1 }}
 exit={{ height: 0, opacity: 0 }}
 className="overflow-hidden"
 ><div className="p-6 pt-0 border-t border-earth-50"><p className="text-earth-600 font-medium leading-relaxed">{faq.answer}
 </p></div></motion.div>)}
 </AnimatePresence></div>);
};

export default HelpCenter;
