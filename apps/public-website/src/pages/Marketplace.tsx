import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Filter, Package, Tractor, ChevronDown, Grid, List, SlidersHorizontal } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export default function Marketplace() {
  const [activeTab, setActiveTab] = useState("crops");
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState("grid");

  // Filter states
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [priceFilter, setPriceFilter] = useState("all");
  const [ratingFilter, setRatingFilter] = useState("all");

  useEffect(() => {
    if (activeTab === "inputs" || activeTab === "machinery") {
      fetchSupplierProducts();
    } else {
      // For crops, we would fetch from the crops API
      setProducts([]);
      setFilteredProducts([]);
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    filterProducts();
  }, [searchTerm, categoryFilter, priceFilter, ratingFilter, products]);

  const fetchSupplierProducts = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API}/suppliers/public/products?limit=100`);
      const data = await response.json();
      
      // Filter by category based on active tab
      const filtered = data.filter(p => {
        if (activeTab === "inputs") {
          return ["seeds", "fertilizer", "pesticides", "herbicides", "fungicides", "animal_feed"].includes(p.category);
        } else if (activeTab === "machinery") {
          return ["tractor", "sprayer", "irrigation", "tiller", "harvester", "tools"].includes(p.category);
        }
        return true;
      });
      
      setProducts(filtered);
      setFilteredProducts(filtered);
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
        (product) =>
          product.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          product.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (categoryFilter !== "all") {
      filtered = filtered.filter((product) => product.category === categoryFilter);
    }

    if (priceFilter !== "all") {
      filtered = filtered.filter((product) => {
        const price = product.price || 0;
        switch (priceFilter) {
          case "0-50": return price <= 50;
          case "50-100": return price > 50 && price <= 100;
          case "100-500": return price > 100 && price <= 500;
          case "500+": return price > 500;
          default: return true;
        }
      });
    }

    if (ratingFilter !== "all") {
      filtered = filtered.filter((product) => {
        const rating = product.supplier_rating || 0;
        switch (ratingFilter) {
          case "4+": return rating >= 4;
          case "3+": return rating >= 3;
          default: return true;
        }
      });
    }

    setFilteredProducts(filtered);
  };

  const categories = activeTab === "inputs" 
    ? ["seeds", "fertilizer", "pesticides", "herbicides", "fungicides", "animal_feed"]
    : ["tractor", "sprayer", "irrigation", "tiller", "harvester", "tools"];

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

  return (
    <div className="min-h-screen bg-earth-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-700 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Marketplace</h1>
            <p className="text-xl text-green-100 mb-8">
              Browse crops, agricultural inputs, and machinery from verified suppliers
            </p>

            {/* Search Bar */}
            <div className="relative max-w-2xl">
              <input
                type="text"
                placeholder="Search products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-5 py-4 pl-12 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-300"
              />
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveTab("crops")}
              className={`px-6 py-4 font-medium transition-colors ${
                activeTab === "crops"
                  ? "text-green-600 border-b-2 border-green-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              🌾 Crops
            </button>
            <button
              onClick={() => setActiveTab("inputs")}
              className={`px-6 py-4 font-medium transition-colors ${
                activeTab === "inputs"
                  ? "text-green-600 border-b-2 border-green-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              🛒 Inputs
            </button>
            <button
              onClick={() => setActiveTab("machinery")}
              className={`px-6 py-4 font-medium transition-colors ${
                activeTab === "machinery"
                  ? "text-green-600 border-b-2 border-green-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              🚜 Machinery
            </button>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition"
              >
                <SlidersHorizontal size={18} />
                Filters
                <ChevronDown size={18} className={showFilters ? "rotate-180" : ""} />
              </button>

              <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode("grid")}
                  className={`p-2 rounded ${viewMode === "grid" ? "bg-white shadow" : ""}`}
                >
                  <Grid size={18} />
                </button>
                <button
                  onClick={() => setViewMode("list")}
                  className={`p-2 rounded ${viewMode === "list" ? "bg-white shadow" : ""}`}
                >
                  <List size={18} />
                </button>
              </div>
            </div>

            <p className="text-sm text-gray-600">
              Showing {filteredProducts.length} products
            </p>
          </div>

          {/* Filters */}
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mt-4 pt-4 border-t border-gray-200 grid grid-cols-1 md:grid-cols-4 gap-4"
            >
              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">All Categories</option>
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {getCategoryLabel(cat)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Price Range</label>
                <select
                  value={priceFilter}
                  onChange={(e) => setPriceFilter(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">All Prices</option>
                  <option value="0-50">$0 - $50</option>
                  <option value="50-100">$50 - $100</option>
                  <option value="100-500">$100 - $500</option>
                  <option value="500+">$500+</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Supplier Rating</label>
                <select
                  value={ratingFilter}
                  onChange={(e) => setRatingFilter(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">All Ratings</option>
                  <option value="4+">4+ stars</option>
                  <option value="3+">3+ stars</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={() => {
                    setCategoryFilter("all");
                    setPriceFilter("all");
                    setRatingFilter("all");
                  }}
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition"
                >
                  Reset Filters
                </button>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Products Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {activeTab === "crops" ? (
          <div className="text-center py-12">
            <div className="bg-white rounded-xl shadow-sm p-12">
              <Package size={48} className="text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-gray-900 mb-2">Crops Marketplace</h3>
              <p className="text-gray-600">Browse farmers' produce listings coming soon.</p>
            </div>
          </div>
        ) : loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent"></div>
            <p className="mt-4 text-gray-600">Loading products...</p>
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="text-center py-12">
            {activeTab === "inputs" ? (
              <Package size={48} className="text-gray-300 mx-auto mb-4" />
            ) : (
              <Tractor size={48} className="text-gray-300 mx-auto mb-4" />
            )}
            <p className="text-gray-600 text-lg">No products found matching your criteria.</p>
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProducts.map((product, index) => (
              <motion.div
                key={product.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow overflow-hidden"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-gray-900 mb-2">{product.name}</h3>
                      <p className="text-sm text-gray-500 mb-2">{product.supplier_name || "Unknown Supplier"}</p>
                      {product.supplier_rating && (
                        <div className="flex items-center gap-1">
                          <span className="text-yellow-500">⭐</span>
                          <span className="text-sm font-medium">{product.supplier_rating.toFixed(1)}</span>
                        </div>
                      )}
                    </div>
                    {product.supplier_verification === "approved" && (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                        ✓ Verified
                      </span>
                    )}
                  </div>

                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">{product.description || "Quality agricultural product"}</p>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Category:</span>
                      <span className="font-medium">{getCategoryLabel(product.category)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Price:</span>
                      <span className="font-bold text-green-600">${product.price?.toFixed(2)}</span>
                    </div>
                    {product.quantity_available !== undefined && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Stock:</span>
                        <span className={`font-medium ${product.quantity_available > 0 ? "text-green-600" : "text-red-600"}`}>
                          {product.quantity_available > 0 ? `${product.quantity_available} units` : "Out of stock"}
                        </span>
                      </div>
                    )}
                  </div>

                  <button
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                    onClick={() => (window.location.href = `/products/${product.id}`)}
                  >
                    View Details
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supplier</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rating</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredProducts.map((product, index) => (
                  <motion.tr
                    key={product.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium text-gray-900">{product.name}</div>
                        <div className="text-sm text-gray-500 line-clamp-1">{product.description || ""}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{product.supplier_name || "Unknown"}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{getCategoryLabel(product.category)}</td>
                    <td className="px-6 py-4 text-sm font-medium text-green-600">${product.price?.toFixed(2)}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{product.quantity_available || "N/A"}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {product.supplier_rating ? `⭐ ${product.supplier_rating.toFixed(1)}` : "N/A"}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        className="text-green-600 hover:text-green-700 text-sm font-medium"
                        onClick={() => (window.location.href = `/products/${product.id}`)}
                      >
                        View
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
