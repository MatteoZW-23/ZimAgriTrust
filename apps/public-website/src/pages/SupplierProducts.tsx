import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Filter, Package, ChevronDown, Grid, List } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export default function SupplierProducts() {
 const [products, setProducts] = useState([]);
 const [filteredProducts, setFilteredProducts] = useState([]);
 const [loading, setLoading] = useState(true);
 const [searchTerm, setSearchTerm] = useState("");
 const [categoryFilter, setCategoryFilter] = useState("all");
 const [productTypeFilter, setProductTypeFilter] = useState("all");
 const [showFilters, setShowFilters] = useState(false);
 const [viewMode, setViewMode] = useState("grid");

 useEffect(() => {
 fetchProducts();
 }, []);

 useEffect(() => {
 filterProducts();
 }, [searchTerm, categoryFilter, productTypeFilter, products]);

 const fetchProducts = async () => {
 try {
 const response = await fetch(`${API}/suppliers/public/products?limit=100`);
 const data = await response.json();
 setProducts(data);
 setFilteredProducts(data);
 } catch (error) {
 console.error("Error fetching products:", error);
 } finally {
 setLoading(false);
 }
 };

 const filterProducts = () => {
 let filtered = [...products];

 if (searchTerm) {
 filtered = filtered.filter(
 (product) =>product.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
 product.description?.toLowerCase().includes(searchTerm.toLowerCase())
 );
 }

 if (categoryFilter !== "all") {
 filtered = filtered.filter((product) => product.category === categoryFilter);
 }

 if (productTypeFilter !== "all") {
 filtered = filtered.filter((product) => product.product_type === productTypeFilter);
 }

 setFilteredProducts(filtered);
 };

 const categories = [...new Set(products.map((p) => p.category).filter(Boolean))];
 const productTypes = [...new Set(products.map((p) => p.product_type).filter(Boolean))];

 return (
 <div className="min-h-screen bg-earth-50">{/* Hero Section */}
 <div className="bg-gradient-to-r from-green-600 to-emerald-700 text-white py-16"><div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><motion.div
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.5 }}
 ><h1 className="text-4xl md:text-5xl font-bold mb-4">Supplier Products</h1><p className="text-xl text-green-100 mb-8">Browse quality agricultural inputs from verified suppliers
 </p>
{/* Search Bar */}
 <div className="relative max-w-2xl"><input
 type="text"
 placeholder="Search products..."
 value={searchTerm}
 onChange={(e) => setSearchTerm(e.target.value)}
 className="w-full px-5 py-4 pl-12 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-300"
 /><Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} /></div>
{/* Filter and View Toggle */}
 <div className="flex items-center gap-4 mt-4"><button
 onClick={() => setShowFilters(!showFilters)}
 className="flex items-center gap-2 text-green-100 hover:text-white transition"
 ><Filter size={18} />Filters
 <ChevronDown size={18} className={showFilters ? "rotate-180" : ""} /></button>
<div className="flex items-center gap-2 bg-white/10 rounded-lg p-1"><button
 onClick={() => setViewMode("grid")}
 className={`p-2 rounded ${viewMode === "grid" ? "bg-white/20" : "hover:bg-white/10"}`}
 ><Grid size={18} /></button><button
 onClick={() => setViewMode("list")}
 className={`p-2 rounded ${viewMode === "list" ? "bg-white/20" : "hover:bg-white/10"}`}
 ><List size={18} /></button></div></div>
{/* Filters */}
 {showFilters && (
 <motion.div
 initial={{ opacity: 0, height: 0 }}
 animate={{ opacity: 1, height: "auto" }}
 className="mt-4 bg-white/10 backdrop-blur rounded-lg p-4 grid grid-cols-1 md:grid-cols-2 gap-4"
 ><div><label className="block text-sm font-medium mb-2">Category</label><select
 value={categoryFilter}
 onChange={(e) => setCategoryFilter(e.target.value)}
 className="w-full px-3 py-2 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-300"
 ><option value="all">All Categories</option>{categories.map((cat) => (
 <option key={cat} value={cat}>{cat}
 </option>))}
 </select></div><div><label className="block text-sm font-medium mb-2">Product Type</label><select
 value={productTypeFilter}
 onChange={(e) => setProductTypeFilter(e.target.value)}
 className="w-full px-3 py-2 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-300"
 ><option value="all">All Types</option>{productTypes.map((type) => (
 <option key={type} value={type}>{type}
 </option>))}
 </select></div></motion.div>)}
 </motion.div></div></div>
{/* Products Grid/List */}
 <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">{loading ? (
 <div className="text-center py-12"><div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent"></div><p className="mt-4 text-gray-600">Loading products...</p></div>) : filteredProducts.length === 0 ? (
 <div className="text-center py-12"><Package size={48} className="text-gray-300 mx-auto mb-4" /><p className="text-gray-600 text-lg">No products found matching your criteria.</p></div>) : viewMode === "grid" ? (
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">{filteredProducts.map((product, index) => (
 <motion.div
 key={product.id}
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ duration: 0.3, delay: index * 0.05 }}
 className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow overflow-hidden"
 ><div className="p-6"><h3 className="text-lg font-bold text-gray-900 mb-2">{product.name}</h3><p className="text-gray-600 text-sm mb-4 line-clamp-2">{product.description || "Quality agricultural product"}</p>
<div className="space-y-2 mb-4"><div className="flex items-center justify-between text-sm"><span className="text-gray-600">Supplier:</span><span className="font-medium">{product.supplier_name || "Unknown"}</span></div><div className="flex items-center justify-between text-sm"><span className="text-gray-600">Category:</span><span className="font-medium">{product.category}</span></div><div className="flex items-center justify-between text-sm"><span className="text-gray-600">Price:</span><span className="font-bold text-green-600">${product.price.toFixed(2)}</span></div>{product.quantity_available !== undefined && (
 <div className="flex items-center justify-between text-sm"><span className="text-gray-600">Stock:</span><span className="font-medium">{product.quantity_available} units</span></div>)}
 {product.supplier_rating && (
 <div className="flex items-center justify-between text-sm"><span className="text-gray-600">Rating:</span><span className="font-medium">⭐ {product.supplier_rating.toFixed(1)}</span></div>)}
 </div>
<button
 className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
 onClick={() => (window.location.href = `/products/${product.id}`)}
 >View Details
 </button></div></motion.div>))}
 </div>) : (
 <div className="bg-white rounded-xl shadow-md overflow-hidden"><table className="w-full"><thead className="bg-gray-50"><tr><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supplier</th><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th></tr></thead><tbody className="divide-y divide-gray-200">{filteredProducts.map((product, index) => (
 <motion.tr
 key={product.id}
 initial={{ opacity: 0, x: -20 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ duration: 0.3, delay: index * 0.05 }}
 className="hover:bg-gray-50"
 ><td className="px-6 py-4"><div><div className="font-medium text-gray-900">{product.name}</div><div className="text-sm text-gray-500 line-clamp-1">{product.description || ""}</div></div></td><td className="px-6 py-4 text-sm text-gray-600">{product.supplier_name || "Unknown"}</td><td className="px-6 py-4 text-sm text-gray-600">{product.category}</td><td className="px-6 py-4 text-sm font-medium text-green-600">${product.price.toFixed(2)}</td><td className="px-6 py-4 text-sm text-gray-600">{product.quantity_available || "N/A"}</td><td className="px-6 py-4"><button
 className="text-green-600 hover:text-green-700 text-sm font-medium"
 onClick={() => (window.location.href = `/products/${product.id}`)}
 >View
 </button></td></motion.tr>))}
 </tbody></table></div>)}
 </div></div>);
}
