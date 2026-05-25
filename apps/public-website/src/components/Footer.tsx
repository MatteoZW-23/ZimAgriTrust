import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Phone, MapPin, X, Facebook, Twitter, Instagram, Linkedin } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import logo from "../assets/logo.png";

const WhatsAppIcon = ({ className }) => (
 <svg viewBox="0 0 24 24" fill="currentColor" className={className}><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
);

const ZimFlag = () => (
 <svg viewBox="0 0 40 24" className="w-8 h-5 rounded shadow-sm"><rect width="40" height="8" fill="#009739" /><rect y="8" width="40" height="8" fill="#FFD700" /><rect y="16" width="40" height="8" fill="#DC143C" /><polygon points="0,0 12,12 0,24" fill="#000000" /><polygon points="2,0 12,10 2,20" fill="#FFFFFF" /><circle cx="4" cy="12" r="2" fill="#FFD700" /></svg>
);

export default function Footer({ onOpenAuth }) {
 const [showContactModal, setShowContactModal] = useState(false);
 const currentYear = new Date().getFullYear();

 const footerLinks = {
 platform: [
 { label: 'Marketplace', to: '/', scrollTo: 'marketplace' },
 { label: 'Features', to: '/', scrollTo: 'features' },
 { label: 'Join as Driver', to: '/driver-join' },
 { label: 'Become an Agent', to: '/agent-join' },
 ],
 company: [
 { label: 'About Us', to: '/about' },
 { label: 'Company Profile', to: '/company-profile' },
 { label: 'Leadership', to: '/company-hierarchy' },
 { label: 'Contact', action: () => setShowContactModal(true) },
 ],
 legal: [
 { label: 'Dispute Resolution', to: '/dispute-resolution' },
 { label: 'Returns Policy', to: '/returns' },
 { label: 'Terms of Service', to: '/terms' },
 { label: 'Privacy Policy', to: '/privacy' },
 ],
 };

 const socialLinks = [
 { icon: Facebook, href: 'https://facebook.com/zimagritrust', label: 'Facebook' },
 { icon: Twitter, href: 'https://twitter.com/zimagritrust', label: 'Twitter' },
 { icon: Instagram, href: 'https://instagram.com/zimagritrust', label: 'Instagram' },
 { icon: Linkedin, href: 'https://linkedin.com/company/zimagritrust', label: 'LinkedIn' },
 ];

 return (
 <footer className="bg-earth-900 text-white"><div className="container-custom py-16">{/* Main Footer Content */}
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-12 lg:gap-8">{/* Brand Column */}
 <div className="lg:col-span-4"><Link to="/" className="flex items-center gap-3 mb-6"><div className="w-12 h-12 rounded-xl bg-primary-600 flex items-center justify-center overflow-hidden"><img 
 src={logo} 
 alt="ZimAgritrust Logo" 
 className="w-8 h-8 object-contain"
 /></div><span className="font-display font-bold text-2xl text-white">Zim<span className="text-primary-400">Agri</span>trust
 </span></Link><p className="text-earth-300 leading-relaxed mb-6">Connecting farmers directly with buyers across Zimbabwe. Trade crops safely with secure payments and reliable delivery.
 </p><div className="flex gap-3">{socialLinks.map((social) => (
 <a
 key={social.label}
 href={social.href}
 target="_blank"
 rel="noopener noreferrer"
 className="w-10 h-10 rounded-lg bg-earth-800 flex items-center justify-center text-earth-400 hover:bg-primary-600 hover:text-white transition-all duration-200"
 aria-label={social.label}
 ><social.icon className="w-5 h-5" /></a>))}
 <a
 href="https://wa.me/263717358956"
 target="_blank"
 rel="noopener noreferrer"
 className="w-10 h-10 rounded-lg bg-earth-800 flex items-center justify-center text-earth-400 hover:bg-green-600 hover:text-white transition-all duration-200"
 aria-label="WhatsApp"
 ><WhatsAppIcon className="w-5 h-5" /></a></div></div>
{/* Platform Links */}
 <div className="lg:col-span-2"><h4 className="font-semibold text-white mb-4">Platform</h4><ul className="space-y-3">{footerLinks.platform.map((link) => (
 <li key={link.label}>{link.to ? (
 <Link 
 to={link.to} 
 className="text-earth-400 hover:text-primary-400 transition-colors text-sm"
 >{link.label}
 </Link>) : (
 <button 
 onClick={link.action}
 className="text-earth-400 hover:text-primary-400 transition-colors text-sm text-left"
 >{link.label}
 </button>)}
 </li>))}
 </ul></div>
{/* Company Links */}
 <div className="lg:col-span-2"><h4 className="font-semibold text-white mb-4">Company</h4><ul className="space-y-3">{footerLinks.company.map((link) => (
 <li key={link.label}>{link.to ? (
 <Link 
 to={link.to} 
 className="text-earth-400 hover:text-primary-400 transition-colors text-sm"
 >{link.label}
 </Link>) : (
 <button 
 onClick={link.action}
 className="text-earth-400 hover:text-primary-400 transition-colors text-sm text-left"
 >{link.label}
 </button>)}
 </li>))}
 </ul></div>
{/* Legal Links */}
 <div className="lg:col-span-2"><h4 className="font-semibold text-white mb-4">Legal</h4><ul className="space-y-3">{footerLinks.legal.map((link) => (
 <li key={link.label}><Link 
 to={link.to} 
 className="text-earth-400 hover:text-primary-400 transition-colors text-sm"
 >{link.label}
 </Link></li>))}
 </ul></div>
{/* Contact Info */}
 <div className="lg:col-span-2"><h4 className="font-semibold text-white mb-4">Contact</h4><ul className="space-y-4"><li className="flex items-start gap-3"><MapPin className="w-5 h-5 text-primary-400 flex-shrink-0 mt-0.5" /><span className="text-earth-300 text-sm">PaJunction Mall Shop M3, Harare, Zimbabwe</span></li><li className="flex items-center gap-3"><Phone className="w-5 h-5 text-primary-400 flex-shrink-0" /><a href="tel:+263717358956" className="text-earth-300 text-sm hover:text-primary-400 transition-colors">+263 71 735 8956
 </a></li><li className="flex items-center gap-3"><Mail className="w-5 h-5 text-primary-400 flex-shrink-0" /><a href="mailto:info@zimagritrust.co.zw" className="text-earth-300 text-sm hover:text-primary-400 transition-colors">info@zimagritrust.co.zw
 </a></li></ul></div></div>
{/* Bottom Bar */}
 <div className="mt-12 pt-8 border-t border-earth-800"><div className="flex flex-col md:flex-row justify-between items-center gap-4"><p className="text-earth-400 text-sm">&copy; {currentYear} ZimAgritrust Limited. All rights reserved.
 </p><div className="flex items-center gap-2 text-earth-400 text-sm"><span>Proudly Zimbabwean</span><ZimFlag /></div></div></div></div>
{/* Contact Modal */}
 <AnimatePresence>{showContactModal && (
 <motion.div
 initial={{ opacity: 0 }}
 animate={{ opacity: 1 }}
 exit={{ opacity: 0 }}
 className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
 onClick={() => setShowContactModal(false)}
 ><motion.div
 initial={{ opacity: 0, scale: 0.95, y: 20 }}
 animate={{ opacity: 1, scale: 1, y: 0 }}
 exit={{ opacity: 0, scale: 0.95, y: 20 }}
 onClick={(e) => e.stopPropagation()}
 className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl"
 ><div className="flex items-center justify-between mb-6"><h2 className="text-xl font-bold text-earth-900">Contact Us</h2><button 
 onClick={() => setShowContactModal(false)}
 className="p-2 rounded-lg text-earth-400 hover:text-earth-600 hover:bg-earth-100 transition-colors"
 ><X className="w-5 h-5" /></button></div>
<p className="text-earth-500 mb-6">We're here to help you with any questions</p>
<div className="space-y-3 mb-6"><a 
 href="tel:+263717358956" 
 className="flex items-center gap-4 p-4 rounded-xl bg-earth-50 hover:bg-primary-50 transition-colors group"
 ><div className="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center group-hover:bg-primary-200 transition-colors"><Phone className="w-6 h-6 text-primary-600" /></div><div><p className="font-semibold text-earth-800">Phone</p><p className="text-sm text-earth-500">+263 71 735 8956</p></div></a>
<a 
 href="mailto:info@zimagritrust.co.zw" 
 className="flex items-center gap-4 p-4 rounded-xl bg-earth-50 hover:bg-primary-50 transition-colors group"
 ><div className="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center group-hover:bg-primary-200 transition-colors"><Mail className="w-6 h-6 text-primary-600" /></div><div><p className="font-semibold text-earth-800">Email</p><p className="text-sm text-earth-500">info@zimagritrust.co.zw</p></div></a>
<a 
 href="https://wa.me/263717358956"
 target="_blank"
 rel="noopener noreferrer"
 className="flex items-center gap-4 p-4 rounded-xl bg-earth-50 hover:bg-green-50 transition-colors group"
 ><div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center group-hover:bg-green-200 transition-colors"><WhatsAppIcon className="w-6 h-6 text-green-600" /></div><div><p className="font-semibold text-earth-800">WhatsApp</p><p className="text-sm text-earth-500">+263 71 735 8956</p></div></a></div>
<div className="pt-4 border-t border-earth-100"><p className="text-xs font-semibold text-earth-400 uppercase tracking-wider mb-2 text-center">Business Hours</p><div className="text-center text-sm text-earth-600 space-y-1"><p>Monday - Friday: 8:00 AM - 6:00 PM</p><p>Saturday: 9:00 AM - 1:00 PM</p><p>Sunday: Closed</p></div></div></motion.div></motion.div>)}
 </AnimatePresence></footer>);
}
