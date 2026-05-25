import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Package, Star, MapPin, CheckCircle, ShoppingCart, Truck, Shield, Heart } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export default function ProductDetail() {
 const { productId } = useParams();
 const [product, setProduct] = useState(null);
 const [supplier, setSupplier] = useState(null);
 const [loading, setLoading] = useState(true);
 const [quantity, setQuantity] = useState(1);
 const [selectedImage, setSelectedImage] = useState(0);

 useEffect(() => {
 fetchProductDetail();
 }, [productId]);

 const fetchProductDetail = async () => {
 try {
 const response = await fetch(`${API}/suppliers/public/products/${productId}`);
 const data = await response.json();
 setProduct(data);
 if (data.supplier) {
 setSupplier(data.supplier);
 }
 } catch (error) {
 console.error("Error fetching product detail:", error);
 } finally {
 setLoading(false);
 }
 };

 const getCategoryLabel = (cat) => {
 const labels = {
 seeds: "Seeds",
 fertilizer: "Fertilizer",
 pesticides: "Pesticides",
 herbicides: "Herbicides",
 fungicides: "Fungicides",
 animal_feed: "Animal Feed",
 tractor: "Tractors",
 sprayer: "Sprayers",
 irrigation: "Irrigation",
 tiller: "Tillers",
 harvester: "Harvesters",
 tools: "Tools",
 };
 return labels[cat] || cat;
 };

 const getProductType = () => {
 const machineryCategories = ["tractor", "sprayer", "irrigation", "tiller", "harvester", "tools"];
 return machineryCategories.includes(product?.category) ? "machinery" : "input";
 };

 if (loading) {
 return (
 <div className="min-h-screen bg-earth-50 flex items-center justify-center"><div className="text-center"><div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent"></div><p className="mt-4 text-gray-600">Loading product details...</p></div></div>);
 }

 if (!product) {
 return (
 <div className="min-h-screen bg-earth-50 flex items-center justify-center"><div className="text-center"><Package size={48} className="text-gray-300 mx-auto mb-4" /><p className="text-gray-600 text-lg">Product not found.</p><Link to="/marketplace" className="text-green-600 hover:text-green-700 mt-4 inline-block">Back to Marketplace
 </Link></div></div>);
 }

 const productType = getProductType();
 const isMachinery = productType === "machinery";

 return (
 <div className="min-h-screen bg-earth-50">{/* Header */}
 <div className="bg-white border-b border-gray-200"><div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4"><Link
 to="/marketplace"
 className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition"
 ><ArrowLeft size={18} />Back to Marketplace
 </Link></div></div>
{/* Product Detail */}
 <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12"><div className="grid grid-cols-1 lg:grid-cols-2 gap-12">{/* Product Images */}
 <motion.div
 initial={{ opacity: 0, x: -20 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ duration: 0.5 }}
 ><div className="bg-white rounded-2xl shadow-lg overflow-hidden"><div className="aspect-square bg-gray-100 flex items-center justify-center">{isMachinery ? (
 <div className="text-8xl"></div>) : (
 <div className="text-8xl"></div>)}
 </div><div className="p-4 grid grid-cols-4 gap-2">{[0, 1, 2, 3].map((i) => (
 <button
 key={i}
 onClick={() => setSelectedImage(i)}
 className={`aspect-square rounded-lg bg-gray-100 flex items-center justify-center transition ${
 selectedImage === i ? "ring-2 ring-green-500" : ""
 }`}
 >{isMachinery ? (
 <div className="text-2xl"></div>) : (
 <div className="text-2xl"></div>)}
 </button>))}
 </div></div></motion.div>
{/* Product Info */}
 <motion.div
 initial={{ opacity: 0, x: 20 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ duration: 0.5, delay: 0.2 }}
 ><div className="bg-white rounded-2xl shadow-lg p-8"><div className="flex items-start justify-between mb-4"><div><span className="inline-block px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full mb-2">{getCategoryLabel(product.category)}
 </span><h1 className="text-3xl font-bold text-gray-900 mb-2">{product.name}</h1><div className="flex items-center gap-2 text-gray-600">{supplier && (
 <><Link
 to={`/suppliers/${supplier.id}`}
 className="hover:text-green-600 font-medium"
 >{supplier.business_name}
 </Link><span>•</span></>)}
 <div className="flex items-center gap-1"><Star size={16} className="fill-yellow-400 text-yellow-400" /><span className="font-medium">{product.supplier_rating?.toFixed(1) || "N/A"}</span>{product.supplier_rating && (
 <span className="text-gray-400">({Math.floor(product.supplier_rating * 50)} reviews)</span>)}
 </div></div></div>{product.supplier_verification === "approved" && (
 <div className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full"><CheckCircle size={16} />Verified
 </div>)}
 </div>
<p className="text-4xl font-bold text-green-600 mb-6">${product.price?.toFixed(2)}
 <span className="text-lg text-gray-500 font-normal">{isMachinery ? "" : "/unit"}
 </span></p>
<div className="space-y-4 mb-6">{product.quantity_available !== undefined && (
 <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"><span className="text-gray-600">Availability:</span><span className={`font-medium ${product.quantity_available > 0 ? "text-green-600" : "text-red-600"}`}>{product.quantity_available > 0 ? `${product.quantity_available} in stock` : "Out of stock"}
 </span></div>)}
 {!isMachinery && (
 <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"><span className="text-gray-600">Quantity:</span><div className="flex items-center gap-3"><button
 onClick={() => setQuantity(Math.max(1, quantity - 1))}
 className="w-10 h-10 rounded-lg border border-gray-300 flex items-center justify-center hover:bg-gray-100 transition"
 >-
 </button><span className="w-12 text-center font-medium">{quantity}</span><button
 onClick={() => setQuantity(quantity + 1)}
 className="w-10 h-10 rounded-lg border border-gray-300 flex items-center justify-center hover:bg-gray-100 transition"
 >+
 </button></div></div>)}
 </div>
<div className="space-y-3 mb-6"><button className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"><ShoppingCart size={20} />{isMachinery ? "Contact Supplier" : "Add to Cart"}
 </button>{!isMachinery && (
 <button className="w-full bg-gray-900 hover:bg-gray-800 text-white font-medium py-3 px-6 rounded-lg transition-colors">Buy Now
 </button>)}
 <button className="w-full border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"><Heart size={20} />Add to Wishlist
 </button></div>
<div className="flex items-center gap-6 text-sm text-gray-600 border-t border-gray-200 pt-6"><div className="flex items-center gap-2"><Truck size={18} className="text-green-600" /><span>Free delivery on orders over $100</span></div><div className="flex items-center gap-2"><Shield size={18} className="text-green-600" /><span>Secure payment</span></div></div></div></motion.div></div>
{/* Product Details */}
 <motion.div
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5, delay: 0.4 }}
 className="mt-12"
 ><div className="bg-white rounded-2xl shadow-lg p-8"><h2 className="text-2xl font-bold text-gray-900 mb-6">Product Details</h2><p className="text-gray-600 mb-6">{product.description || "Quality agricultural product from verified supplier."}</p>
<div className="grid grid-cols-1 md:grid-cols-2 gap-4"><div className="p-4 bg-gray-50 rounded-lg"><p className="text-sm text-gray-600 mb-1">Category</p><p className="font-medium">{getCategoryLabel(product.category)}</p></div><div className="p-4 bg-gray-50 rounded-lg"><p className="text-sm text-gray-600 mb-1">Product Type</p><p className="font-medium">{product.product_type || "Standard"}</p></div><div className="p-4 bg-gray-50 rounded-lg"><p className="text-sm text-gray-600 mb-1">Brand</p><p className="font-medium">{product.brand || "Generic"}</p></div><div className="p-4 bg-gray-50 rounded-lg"><p className="text-sm text-gray-600 mb-1">SKU</p><p className="font-medium">{product.sku || "N/A"}</p></div></div></div></motion.div>
{/* Supplier Information */}
 {supplier && (
 <motion.div
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5, delay: 0.6 }}
 className="mt-8"
 ><div className="bg-white rounded-2xl shadow-lg p-8"><h2 className="text-2xl font-bold text-gray-900 mb-6">Supplier Information</h2><div className="flex items-start gap-6"><div className="w-16 h-16 rounded-xl bg-green-100 flex items-center justify-center flex-shrink-0"><Package size={32} className="text-green-600" /></div><div className="flex-1"><div className="flex items-start justify-between mb-4"><div><Link
 to={`/suppliers/${supplier.id}`}
 className="text-xl font-bold text-gray-900 hover:text-green-600 transition"
 >{supplier.business_name}
 </Link><div className="flex items-center gap-2 text-gray-600 mt-1"><MapPin size={16} />{supplier.location || "Zimbabwe"}
 </div></div><div className="flex items-center gap-2"><div className="flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-700 text-sm font-medium rounded-full"><Star size={14} className="fill-yellow-500 text-yellow-500" />{supplier.rating?.toFixed(1) || "N/A"}
 </div>{supplier.verification_status === "approved" && (
 <div className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full"><CheckCircle size={14} />Verified
 </div>)}
 </div></div>
<div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"><div><p className="text-sm text-gray-600">Products</p><p className="font-medium">{supplier.total_products || "N/A"}</p></div><div><p className="text-sm text-gray-600">Orders</p><p className="font-medium">{supplier.total_orders || "N/A"}</p></div><div><p className="text-sm text-gray-600">Member Since</p><p className="font-medium">{supplier.joined_date ? new Date(supplier.joined_date).getFullYear() : "N/A"}</p></div><div><p className="text-sm text-gray-600">Response Time</p><p className="font-medium">~2 hours</p></div></div>
<div className="flex gap-3"><Link
 to={`/suppliers/${supplier.id}`}
 className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors text-center"
 >View Supplier Profile
 </Link><button className="flex-1 border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors">Contact Supplier
 </button></div></div></div></div></motion.div>)}
 </div></div>);
}
