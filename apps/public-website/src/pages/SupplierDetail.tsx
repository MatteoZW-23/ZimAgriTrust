import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { MapPin, Star, CheckCircle, Award, Phone, Mail, ArrowLeft, Package, TrendingUp, Clock, Truck, Users, Heart } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export default function SupplierDetail() {
  const { supplierId } = useParams();
  const [supplier, setSupplier] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("products");
  const [following, setFollowing] = useState(false);

  useEffect(() => {
    fetchSupplierDetails();
  }, [supplierId]);

  const fetchSupplierDetails = async () => {
    try {
      const response = await fetch(`${API}/suppliers/public/${supplierId}/products`);
      const data = await response.json();
      setProducts(data);

      if (data.length > 0 && data[0].supplier) {
        setSupplier(data[0].supplier);
      }
    } catch (error) {
      console.error("Error fetching supplier details:", error);
    } finally {
      setLoading(false);
    }
  };

  const getVerificationBadge = (status) => {
    switch (status) {
      case "approved":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
            <CheckCircle size={16} />
            Verified Business
          </span>
        );
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-700 text-sm font-medium rounded-full">
            Pending Verification
          </span>
        );
      case "suspended":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 text-sm font-medium rounded-full">
            Suspended
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-700 text-sm font-medium rounded-full">
            {status}
          </span>
        );
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

  if (loading) {
    return (
      <div className="min-h-screen bg-earth-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent"></div>
          <p className="mt-4 text-gray-600">Loading supplier details...</p>
        </div>
      </div>
    );
  }

  if (!supplier) {
    return (
      <div className="min-h-screen bg-earth-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 text-lg">Supplier not found.</p>
          <Link to="/suppliers" className="text-green-600 hover:text-green-700 mt-4 inline-block">
            Back to Suppliers
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-earth-50">
      {/* Cover Image */}
      <div className="h-48 bg-gradient-to-r from-green-600 to-emerald-700"></div>

      {/* Header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-24 relative z-10">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="flex flex-col md:flex-row gap-8 items-start">
            {/* Logo */}
            <div className="w-32 h-32 rounded-2xl bg-green-100 flex items-center justify-center flex-shrink-0 -mt-24 md:-mt-16 border-4 border-white shadow-lg">
              <Package size={48} className="text-green-600" />
            </div>

            {/* Supplier Info */}
            <div className="flex-1">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">{supplier.business_name}</h1>
                  <p className="text-gray-600 mb-2">
                    {supplier.description || "Agricultural inputs supplier"}
                  </p>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Star size={16} className="fill-yellow-400 text-yellow-400" />
                      <span className="font-medium">{supplier.rating?.toFixed(1) || "N/A"}</span>
                      {supplier.rating && (
                        <span className="text-gray-400">({Math.floor(supplier.rating * 100)} ratings)</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock size={16} />
                      <span>Member since {supplier.joined_date ? new Date(supplier.joined_date).getFullYear() : "N/A"}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <MapPin size={16} />
                      <span>{supplier.location || "Zimbabwe"}</span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  {getVerificationBadge(supplier.verification_status)}
                  <button
                    onClick={() => setFollowing(!following)}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      following
                        ? "bg-gray-100 text-gray-700 hover:bg-gray-200"
                        : "bg-green-600 text-white hover:bg-green-700"
                    }`}
                  >
                    {following ? "Following" : "Follow"}
                  </button>
                </div>
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-2">
                <div className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 text-sm rounded-full">
                  <CheckCircle size={14} />
                  Verified business
                </div>
                <div className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full">
                  <Award size={14} />
                  Tax compliant
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="mt-8 border-t border-gray-200">
            <div className="flex gap-8">
              {["products", "about", "reviews", "contact"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-4 font-medium transition-colors border-b-2 ${
                    activeTab === tab
                      ? "border-green-600 text-green-600"
                      : "border-transparent text-gray-600 hover:text-gray-900"
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "products" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">All Products ({products.length})</h2>
              <Link to="/supplier-products" className="text-green-600 hover:text-green-700 font-medium">
                View All →
              </Link>
            </div>

            {products.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-xl shadow-sm">
                <Package size={48} className="text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600 text-lg">No products available from this supplier.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {products.map((product, index) => (
                  <motion.div
                    key={product.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow overflow-hidden"
                  >
                    <div className="p-4">
                      <h3 className="font-bold text-gray-900 mb-2 line-clamp-1">{product.name}</h3>
                      <p className="text-green-600 font-bold mb-2">${product.price?.toFixed(2)}</p>
                      <p className="text-xs text-gray-500 mb-3">{getCategoryLabel(product.category)}</p>
                      <p className={`text-xs font-medium mb-3 ${product.quantity_available > 0 ? "text-green-600" : "text-red-600"}`}>
                        {product.quantity_available > 0 ? `${product.quantity_available} in stock` : "Out of stock"}
                      </p>
                      <button
                        className="w-full bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors"
                        onClick={() => (window.location.href = `/products/${product.id}`)}
                      >
                        View Details
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {activeTab === "about" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">About {supplier.business_name}</h2>
              <p className="text-gray-600 mb-6">
                {supplier.description || "Trusted agricultural input supplier providing quality products to farmers across Zimbabwe."}
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Business Type</p>
                  <p className="font-medium">{getBusinessTypeLabel(supplier.business_type)}</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Products Listed</p>
                  <p className="font-medium">{products.length}</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Member Since</p>
                  <p className="font-medium">{supplier.joined_date ? new Date(supplier.joined_date).getFullYear() : "N/A"}</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Location</p>
                  <p className="font-medium">{supplier.location || "Zimbabwe"}</p>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === "reviews" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Customer Reviews</h2>
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex text-yellow-400">★★★★★</div>
                    <span className="text-sm text-gray-600">2 days ago</span>
                  </div>
                  <p className="text-gray-700">Great quality products and fast delivery. Highly recommended!</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex text-yellow-400">★★★★☆</div>
                    <span className="text-sm text-gray-600">1 week ago</span>
                  </div>
                  <p className="text-gray-700">Good prices and reliable supplier. Will order again.</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex text-yellow-400">★★★★★</div>
                    <span className="text-sm text-gray-600">2 weeks ago</span>
                  </div>
                  <p className="text-gray-700">Excellent customer service and product quality.</p>
                </div>
              </div>
              <button className="mt-6 w-full border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-3 px-6 rounded-lg transition-colors">
                Write a Review
              </button>
            </div>
          </motion.div>
        )}

        {activeTab === "contact" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Contact Supplier</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center">
                      <Phone size={24} className="text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Phone</p>
                      <p className="font-medium">+263 XXX XXX XXX</p>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                      <Mail size={24} className="text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Email</p>
                      <p className="font-medium">contact@example.com</p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-6">
                <textarea
                  placeholder="Write your message here..."
                  className="w-full p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  rows={4}
                />
                <button className="mt-4 w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors">
                  Send Message
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Supplier Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="mt-8"
        >
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Supplier Stats</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center">
                  <Package size={24} className="text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{products.length}</p>
                  <p className="text-sm text-gray-600">Total products</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                  <Users size={24} className="text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{supplier.total_orders || "N/A"}</p>
                  <p className="text-sm text-gray-600">Orders completed</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-yellow-100 flex items-center justify-center">
                  <Clock size={24} className="text-yellow-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">~2h</p>
                  <p className="text-sm text-gray-600">Avg response time</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
                  <Truck size={24} className="text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">98%</p>
                  <p className="text-sm text-gray-600">On-time delivery</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
