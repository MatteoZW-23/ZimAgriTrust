import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Smartphone, Bell, Mail, Truck, CheckCircle, Wallet, MapPin, Clock } from 'lucide-react';

export default function DriverJoin() {
 const [showNotifyModal, setShowNotifyModal] = useState(false);
 const [email, setEmail] = useState('');
 const [submitted, setSubmitted] = useState(false);

 const features = [
 { icon: Clock, title: "Consistent Work", desc: "Get regular delivery requests from farmers and buyers all year round." },
 { icon: Wallet, title: "Reliable Payments", desc: "Fast, secure payments deposited directly to your mobile wallet." },
 { icon: MapPin, title: "GPS Tracking", desc: "Our driver app includes route optimization and real-time tracking." },
 { icon: Clock, title: "Flexible Schedule", desc: "Pick jobs that fit your schedule. No forced assignments." },
 ];

 const requirements = [
 "Valid driver's license (Class 2 or higher for heavy vehicles)",
 "Vehicle registration and insurance",
 "Smartphone with Android 8+ or iOS 14+",
 "Clean criminal record",
 "Good physical condition for loading/unloading",
 ];

 const steps = [
 { num: 1, title: "Download the App", desc: "Install the Agritrust Driver app on your phone." },
 { num: 2, title: "Register & Verify", desc: "Submit your license, vehicle details, and phone number." },
 { num: 3, title: "Get Approved", desc: "Our team reviews and approves your application within 48 hours." },
 { num: 4, title: "Start Earning", desc: "Accept delivery jobs and get paid after each completed delivery." },
 ];

 return (
 <div className="min-h-screen bg-earth-50">{/* Hero */}
 <section className="bg-gradient-to-br from-primary-700 to-primary-900 text-white py-16 lg:py-24"><div className="container-custom"><motion.div
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 className="text-center max-w-3xl mx-auto"
 ><div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm mb-6"><Truck className="w-4 h-4" /><span className="text-sm font-medium">Driver Opportunity</span></div><h1 className="text-4xl md:text-5xl font-bold mb-4">Drive with ZimAgritrust</h1><p className="text-xl text-primary-100">Join our logistics network and earn delivering crops across Zimbabwe</p></motion.div></div></section>
{/* Features */}
 <section className="py-16"><div className="container-custom"><div className="text-center mb-12"><h2 className="text-3xl font-bold text-earth-900 mb-4">Why Drive with Us?</h2><p className="text-earth-600 max-w-2xl mx-auto">Benefits of joining our driver network</p></div>
<div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">{features.map((feature, index) => (
 <motion.div
 key={feature.title}
 initial={{ opacity: 0, y: 20 }}
 whileInView={{ opacity: 1, y: 0 }}
 viewport={{ once: true }}
 transition={{ delay: index * 0.1 }}
 className="bg-white rounded-xl p-6 shadow-sm border border-earth-100 text-center"
 ><div className="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center mx-auto mb-4"><feature.icon className="w-6 h-6 text-primary-600" /></div><h3 className="font-semibold text-earth-900 mb-2">{feature.title}</h3><p className="text-sm text-earth-500">{feature.desc}</p></motion.div>))}
 </div></div></section>
{/* Requirements */}
 <section className="py-16 bg-white"><div className="container-custom"><div className="grid lg:grid-cols-2 gap-12 items-center"><motion.div
 initial={{ opacity: 0, x: -20 }}
 whileInView={{ opacity: 1, x: 0 }}
 viewport={{ once: true }}
 ><h2 className="text-3xl font-bold text-earth-900 mb-6">Requirements</h2><div className="space-y-4">{requirements.map((req, index) => (
 <div key={index} className="flex items-start gap-3"><div className="w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0 mt-0.5"><CheckCircle className="w-4 h-4 text-primary-600" /></div><span className="text-earth-700">{req}</span></div>))}
 </div></motion.div>
<motion.div
 initial={{ opacity: 0, x: 20 }}
 whileInView={{ opacity: 1, x: 0 }}
 viewport={{ once: true }}
 className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-2xl p-8"
 ><h3 className="text-xl font-semibold text-earth-900 mb-4">Download the Driver App</h3><p className="text-earth-600 mb-6">Available on Android and iOS. Install the app to start receiving delivery requests.</p><div className="flex flex-col sm:flex-row gap-3"><button 
 onClick={() => setShowNotifyModal(true)}
 className="btn btn-primary flex items-center justify-center gap-2"
 ><Smartphone className="w-5 h-5" />Download for Android
 </button><button 
 onClick={() => setShowNotifyModal(true)}
 className="btn bg-white text-earth-900 border border-earth-200 hover:bg-earth-50 flex items-center justify-center gap-2"
 ><svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>Download for iOS
 </button></div></motion.div></div></div></section>
{/* How It Works */}
 <section className="py-16"><div className="container-custom"><div className="text-center mb-12"><h2 className="text-3xl font-bold text-earth-900 mb-4">How It Works</h2><p className="text-earth-600 max-w-2xl mx-auto">Get started in 4 simple steps</p></div>
<div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">{steps.map((step, index) => (
 <motion.div
 key={step.num}
 initial={{ opacity: 0, y: 20 }}
 whileInView={{ opacity: 1, y: 0 }}
 viewport={{ once: true }}
 transition={{ delay: index * 0.1 }}
 className="relative"
 ><div className="bg-white rounded-xl p-6 shadow-sm border border-earth-100"><div className="w-10 h-10 rounded-full bg-primary-600 text-white flex items-center justify-center font-bold mb-4">{step.num}
 </div><h3 className="font-semibold text-earth-900 mb-2">{step.title}</h3><p className="text-sm text-earth-500">{step.desc}</p></div>{index < 3 && (
 <div className="hidden lg:block absolute top-1/2 -right-3 w-6 h-0.5 bg-primary-200"></div>)}
 </motion.div>))}
 </div></div></section>
{/* CTA */}
 <section className="py-16 bg-white"><div className="container-custom"><div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl p-8 lg:p-12 text-center"><h2 className="text-3xl font-bold text-white mb-4">Ready to Hit the Road?</h2><p className="text-primary-100 mb-8 max-w-2xl mx-auto">Download the app now and join hundreds of drivers earning with ZimAgritrust.</p><button 
 onClick={() => setShowNotifyModal(true)}
 className="btn bg-white text-primary-700 hover:bg-primary-50 inline-flex items-center gap-2"
 ><Bell className="w-5 h-5" />Notify Me When Available
 </button></div></div></section>
{/* Notify Modal */}
 <AnimatePresence>{showNotifyModal && (
 <motion.div
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 exit={{ opacity: 0 }}
 className="fixed inset-0 z-50 flex items-center justify-center p-4"
 ><div 
 className="absolute inset-0 bg-black/60 backdrop-blur-sm"
 onClick={() => setShowNotifyModal(false)}
 /><motion.div
 initial={{ opacity: 0, scale: 0.95, y: 20 }}
 animate={{ opacity: 1, scale: 1, y: 0 }}
 exit={{ opacity: 0, scale: 0.95, y: 20 }}
 className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md p-8"
 onClick={(e) => e.stopPropagation()}
 ><button 
 onClick={() => setShowNotifyModal(false)}
 className="absolute top-4 right-4 p-2 text-earth-400 hover:text-earth-600 rounded-lg hover:bg-earth-100 transition-colors"
 ><X className="w-5 h-5" /></button>
<div className="text-center mb-6"><div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4"><Truck className="w-10 h-10 text-primary-600" /></div><h2 className="text-2xl font-bold text-earth-900 mb-2">Driver App Coming Soon!</h2><p className="text-earth-500">Be the first to know when our driver app launches.</p></div>
{!submitted ? (
 <form 
 onSubmit={(e) => { e.preventDefault(); setSubmitted(true); }}
 className="space-y-4"
 ><div><label className="block text-sm font-medium text-earth-700 mb-1.5">Email Address</label><div className="relative"><Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-earth-400" /><input
 type="email"
 placeholder="your@email.com"
 value={email}
 onChange={(e) => setEmail(e.target.value)}
 className="input-field pl-10"
 required
 /></div></div><button type="submit" className="btn btn-primary w-full justify-center"><Bell className="w-5 h-5" />Notify Me
 </button></form>) : (
 <div className="text-center py-4"><div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4"><CheckCircle className="w-8 h-8 text-green-600" /></div><h3 className="text-lg font-semibold text-earth-900 mb-2">You're on the list!</h3><p className="text-earth-500 mb-6">We'll contact you as soon as the driver app is available.</p><button 
 onClick={() => setShowNotifyModal(false)}
 className="btn bg-earth-100 text-earth-700 hover:bg-earth-200"
 >Close
 </button></div>)}
 </motion.div></motion.div>)}
 </AnimatePresence></div>);
}
