import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, MapPin, Star, Award, CheckCircle, Filter, ChevronDown } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export default function Suppliers() {
 const [suppliers, setSuppliers] = useState([]);
 const [filteredSuppliers, setFilteredSuppliers] = useState([]);
 const [loading, setLoading] = useState(true);
 const [searchTerm, setSearchTerm] = useState("");
 const [businessTypeFilter, setBusinessTypeFilter] = useState("all");
 const [verificationFilter, setVerificationFilter] = useState("all");
 const [showFilters, setShowFilters] = useState(false);

 useEffect(() => {
 fetchSuppliers();
 }, []);

 useEffect(() => {
 filterSuppliers();
 }, [searchTerm, businessTypeFilter, verificationFilter, suppliers]);

 const fetchSuppliers = async () => {
 try {
 const response = await fetch(`${API}/suppliers/public/list?limit=100`);
 const data = await response.json();
 setSuppliers(data);
 setFilteredSuppliers(data);
 } catch (error) {
 console.error("Error fetching suppliers:", error);
 } finally {
 setLoading(false);
 }
 };

 const filterSuppliers = () => {
 let filtered = [...suppliers];

 // Search filter
 if (searchTerm) {
 filtered = filtered.filter(
 (supplier) =>supplier.business_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
 supplier.location?.toLowerCase().includes(searchTerm.toLowerCase())
 );
 }

 // Business type filter
 if (businessTypeFilter !== "all") {
 filtered = filtered.filter(
 (supplier) => supplier.business_type === businessTypeFilter
 );
 }

 // Verification status filter
 if (verificationFilter !== "all") {
 filtered = filtered.filter(
 (supplier) => supplier.verification_status === verificationFilter
 );
 }

 setFilteredSuppliers(filtered);
 };

 const getVerificationBadge = (status) => {
 switch (status) {
 case "approved":
 return (
 <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full"><CheckCircle size={12} />Verified
 </span>);
 case "pending":
 return (
 <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded-full">Pending
 </span>);
 case "suspended":
 return (
 <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">Suspended
 </span>);
 default:
 return (
 <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">{status}
 </span>);
 }
 };

 const getBusinessTypeLabel = (type) => {
 const labels = {
 agro_dealer: "Agro Dealer",
 distributor: "Distributor",
 manufacturer: "Manufacturer",
 importer: "Importer",
 };
 return labels[type] || type;
 };

 return (
 <div className="min-h-screen bg-earth-50">{/* Hero Section */}
 <div className="bg-gradient-to-r from-green-600 to-emerald-700 text-white py-16"><div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><motion.div
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5 }}
 ><h1 className="text-4xl md:text-5xl font-bold mb-4">Verified Suppliers</h1><p className="text-xl text-green-100 mb-8">Connect with trusted agricultural input suppliers across Zimbabwe
 </p>
{/* Search Bar */}
 <div className="relative max-w-2xl"><input
 type="text"
 placeholder="Search suppliers by name or location..."
 value={searchTerm}
 onChange={(e) => setSearchTerm(e.target.value)}
 className="w-full px-5 py-4 pl-12 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-300"
 /><Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} /></div>
{/* Filter Toggle */}
 <button
 onClick={() => setShowFilters(!showFilters)}
 className="mt-4 flex items-center gap-2 text-green-100 hover:text-white transition"
 ><Filter size={18} />Filters
 <ChevronDown size={18} className={showFilters ? "rotate-180" : ""} /></button>
{/* Filters */}
 {showFilters && (
 <motion.div
 initial={{ opacity: 0, height: 0 }}
 animate={{ opacity: 1, height: "auto" }}
 className="mt-4 bg-white/10 backdrop-blur rounded-lg p-4 grid grid-cols-1 md:grid-cols-3 gap-4"
 ><div><label className="block text-sm font-medium mb-2">Business Type</label><select
 value={businessTypeFilter}
 onChange={(e) => setBusinessTypeFilter(e.target.value)}
 className="w-full px-3 py-2 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-300"
 ><option value="all">All Types</option><option value="agro_dealer">Agro Dealer</option><option value="distributor">Distributor</option><option value="manufacturer">Manufacturer</option><option value="importer">Importer</option></select></div><div><label className="block text-sm font-medium mb-2">Verification Status</label><select
 value={verificationFilter}
 onChange={(e) => setVerificationFilter(e.target.value)}
 className="w-full px-3 py-2 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-300"
 ><option value="all">All Status</option><option value="approved">Verified</option><option value="pending">Pending</option></select></div></motion.div>)}
 </motion.div></div></div>
{/* Suppliers Grid */}
 <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">{loading ? (
 <div className="text-center py-12"><div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent"></div><p className="mt-4 text-gray-600">Loading suppliers...</p></div>) : filteredSuppliers.length === 0 ? (
 <div className="text-center py-12"><p className="text-gray-600 text-lg">No suppliers found matching your criteria.</p></div>) : (
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">{filteredSuppliers.map((supplier, index) => (
 <motion.div
 key={supplier.id}
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.3, delay: index * 0.1 }}
 className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow overflow-hidden"
 ><div className="p-6"><div className="flex items-start justify-between mb-4"><div className="flex-1"><h3 className="text-xl font-bold text-gray-900 mb-1">{supplier.business_name}
 </h3><div className="flex items-center gap-2 text-sm text-gray-600"><MapPin size={14} />{supplier.location || "Zimbabwe"}
 </div></div>{getVerificationBadge(supplier.verification_status)}
 </div>
<div className="space-y-2 mb-4"><div className="flex items-center justify-between text-sm"><span className="text-gray-600">Type:</span><span className="font-medium">{getBusinessTypeLabel(supplier.business_type)}</span></div>{supplier.rating && (
 <div className="flex items-center justify-between text-sm"><span className="text-gray-600">Rating:</span><div className="flex items-center gap-1"><Star size={14} className="fill-yellow-400 text-yellow-400" /><span className="font-medium">{supplier.rating.toFixed(1)}</span></div></div>)}
 {supplier.product_types && supplier.product_types.length > 0 && (
 <div className="flex flex-wrap gap-1 mt-2">{supplier.product_types.slice(0, 3).map((type, idx) => (
 <span
 key={idx}
 className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full"
 >{type}
 </span>))}
 {supplier.product_types.length > 3 && (
 <span className="text-xs text-gray-500">+{supplier.product_types.length - 3} more
 </span>)}
 </div>)}
 </div>
<button
 className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
 onClick={() => (window.location.href = `/suppliers/${supplier.id}`)}
 >View Products
 </button></div></motion.div>))}
 </div>)}
 </div></div>);
}
