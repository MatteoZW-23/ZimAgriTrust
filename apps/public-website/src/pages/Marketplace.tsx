import React, { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ChevronDown, Grid, List, Package, Search, SlidersHorizontal, Tractor } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

type MarketplaceItem = {
  id: string;
  kind: "crop" | "input" | "machinery" | "request";
  name: string;
  description?: string;
  category?: string;
  price: number;
  currency?: string;
  quantity_available?: number;
  supplier_name?: string;
  supplier_rating?: number;
  supplier_verification?: string;
  location_label?: string;
  quantity_unit?: string;
};

export default function Marketplace() {
  const [activeTab, setActiveTab] = useState<"products" | "requests" | "inputs" | "machinery">("products");
  const [items, setItems] = useState<MarketplaceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [priceFilter, setPriceFilter] = useState("all");
  const [ratingFilter, setRatingFilter] = useState("all");

  useEffect(() => {
    void fetchItems();
  }, [activeTab, searchTerm]);

  const fetchItems = async () => {
    setLoading(true);
    try {
      if (activeTab === "products") {
        const params = new URLSearchParams({ limit: "100" });
        if (searchTerm.trim()) params.set("crop", searchTerm.trim());
        const response = await fetch(`${API}/public/listings?${params.toString()}`);
        const data = await response.json();
        const productItems = (Array.isArray(data) ? data : data.data || []).map((item: any) => ({
          id: item.id,
          kind: "crop" as const,
          name: item.product_type || item.crop || item.title || "Agricultural Product",
          description: item.description,
          category: String(item.sector || item.product_type || "product").toLowerCase(),
          price: Number(item.price_per_unit || 0),
          currency: item.currency || "USD",
          quantity_available: Number(item.quantity || 0),
          quantity_unit: item.quantity_unit || "units",
          supplier_name: item.seller_name || "Verified Farmer",
          supplier_rating: Number(item.seller_trust_score || 0) / 20,
          supplier_verification: item.seller_verified ? "approved" : "pending",
          location_label: [item.location_district, item.location_province].filter(Boolean).join(", ") || "Zimbabwe",
        }));
        setItems(productItems);
        return;
      }

      if (activeTab === "requests") {
        const params = new URLSearchParams({ kind: "requests", limit: "100" });
        if (searchTerm.trim()) params.set("q", searchTerm.trim());
        const response = await fetch(`${API}/browse/search?${params.toString()}`);
        const data = await response.json();
        const requestItems = (Array.isArray(data) ? data : data.results || []).map((item: any) => ({
          id: item.id,
          kind: "request" as const,
          name: item.name || item.product_type || "Agricultural Request",
          description: "Buyer is looking for this agricultural product or service.",
          category: String(item.sector || "buyer_request").toLowerCase(),
          price: Number(item.price_per_unit || 0),
          currency: item.currency || "USD",
          quantity_available: Number(item.quantity || 0),
          quantity_unit: item.unit || "units",
          supplier_name: "Buyer request",
          supplier_rating: 0,
          supplier_verification: "pending",
          location_label: item.location || "Zimbabwe",
        }));
        setItems(requestItems);
        return;
      }

      const response = await fetch(`${API}/suppliers/public/products?limit=100`);
      const data = await response.json();
      const filtered = (Array.isArray(data) ? data : []).filter((product: any) => {
        const category = String(product.category || "").toLowerCase();
        if (activeTab === "inputs") {
          return ["seeds", "fertilizer", "pesticides", "herbicides", "fungicides", "animal_feed"].includes(category);
        }
        return ["tractor", "sprayer", "irrigation", "tiller", "harvester", "tools"].includes(category);
      });
      const supplierItems = filtered
        .filter((product: any) => {
          const term = searchTerm.trim().toLowerCase();
          if (!term) return true;
          return String(product.name || "").toLowerCase().includes(term) || String(product.description || "").toLowerCase().includes(term);
        })
        .map((product: any) => ({
          id: product.id,
          kind: activeTab === "inputs" ? "input" as const : "machinery" as const,
          name: product.name,
          description: product.description,
          category: String(product.category || "").toLowerCase(),
          price: Number(product.price || 0),
          currency: product.currency || "USD",
          quantity_available: Number(product.quantity_available || 0),
          supplier_name: product.supplier_name || "Verified Supplier",
          supplier_rating: Number(product.supplier_rating || 0),
          supplier_verification: product.supplier_verification,
          location_label: product.location || product.province || "Zimbabwe",
        }));
      setItems(supplierItems);
    } catch (error) {
      console.error("Marketplace load failed:", error);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const categories = useMemo(() => {
    if (activeTab === "products") return ["crops", "horticulture", "dairy", "apiculture", "floriculture", "livestock", "poultry", "value_added"];
    if (activeTab === "requests") return ["buyer_request", "crops", "horticulture", "dairy", "apiculture", "floriculture", "inputs"];
    if (activeTab === "inputs") return ["seeds", "fertilizer", "pesticides", "herbicides", "fungicides", "animal_feed"];
    return ["tractor", "sprayer", "irrigation", "tiller", "harvester", "tools"];
  }, [activeTab]);

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      if (categoryFilter !== "all" && item.category !== categoryFilter) return false;
      if (priceFilter !== "all") {
        const price = item.price || 0;
        if (priceFilter === "0-50" && price > 50) return false;
        if (priceFilter === "50-100" && (price <= 50 || price > 100)) return false;
        if (priceFilter === "100-500" && (price <= 100 || price > 500)) return false;
        if (priceFilter === "500+" && price <= 500) return false;
      }
      if (ratingFilter !== "all") {
        const rating = item.supplier_rating || 0;
        if (ratingFilter === "4+" && rating < 4) return false;
        if (ratingFilter === "3+" && rating < 3) return false;
      }
      return true;
    });
  }, [categoryFilter, items, priceFilter, ratingFilter]);

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      maize: "Maize",
      soybeans: "Soybeans",
      wheat: "Wheat",
      groundnuts: "Groundnuts",
      sunflower: "Sunflower",
      sorghum: "Sorghum",
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
      product: "Product",
      buyer_request: "Buyer Request",
      crops: "Crops",
      horticulture: "Horticulture",
      dairy: "Dairy",
      apiculture: "Apiculture / Bees",
      floriculture: "Flowers",
      livestock: "Livestock",
      poultry: "Poultry",
      value_added: "Value Added",
    };
    return labels[category] || category;
  };

  const emptyIcon = activeTab === "machinery" ? <Tractor size={48} className="mx-auto mb-4 text-gray-300" /> : <Package size={48} className="mx-auto mb-4 text-gray-300" />;

  return (
    <div className="min-h-screen bg-earth-50">
      <div className="bg-gradient-to-r from-green-600 to-emerald-700 py-16 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <h1 className="mb-4 text-4xl font-bold md:text-5xl">Marketplace</h1>
            <p className="mb-8 text-xl text-green-100">Browse verified agricultural products, buyer requests, inputs, and machinery across Zimbabwe.</p>
            <div className="relative max-w-2xl">
              <input
                type="text"
                placeholder="Search products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg px-5 py-4 pl-12 text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-300"
              />
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 transform text-gray-400" size={20} />
            </div>
          </motion.div>
        </div>
      </div>

      <div className="sticky top-16 z-40 border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl gap-1 px-4 sm:px-6 lg:px-8">
          {[
            { id: "products", label: "Products" },
            { id: "requests", label: "Buyer Requests" },
            { id: "inputs", label: "Inputs" },
            { id: "machinery", label: "Machinery" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as "products" | "requests" | "inputs" | "machinery")}
              className={`px-6 py-4 font-medium transition-colors ${
                activeTab === tab.id ? "border-b-2 border-green-600 text-green-600" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowFilters((value) => !value)}
                className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 transition hover:bg-gray-50"
              >
                <SlidersHorizontal size={18} />
                Filters
                <ChevronDown size={18} className={showFilters ? "rotate-180" : ""} />
              </button>
              <div className="flex items-center gap-2 rounded-lg bg-gray-100 p-1">
                <button onClick={() => setViewMode("grid")} className={`rounded p-2 ${viewMode === "grid" ? "bg-white shadow" : ""}`}><Grid size={18} /></button>
                <button onClick={() => setViewMode("list")} className={`rounded p-2 ${viewMode === "list" ? "bg-white shadow" : ""}`}><List size={18} /></button>
              </div>
            </div>
            <p className="text-sm text-gray-600">Showing {filteredItems.length} items</p>
          </div>

          {showFilters && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-4 grid grid-cols-1 gap-4 border-t border-gray-200 pt-4 md:grid-cols-4">
              <div>
                <label className="mb-2 block text-sm font-medium">Category</label>
                <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500">
                  <option value="all">All Categories</option>
                  {categories.map((category) => <option key={category} value={category}>{getCategoryLabel(category)}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium">Price Range</label>
                <select value={priceFilter} onChange={(e) => setPriceFilter(e.target.value)} className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500">
                  <option value="all">All Prices</option>
                  <option value="0-50">$0 - $50</option>
                  <option value="50-100">$50 - $100</option>
                  <option value="100-500">$100 - $500</option>
                  <option value="500+">$500+</option>
                </select>
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium">Seller Rating</label>
                <select value={ratingFilter} onChange={(e) => setRatingFilter(e.target.value)} className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500">
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
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 transition hover:bg-gray-50"
                >
                  Reset Filters
                </button>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        {loading ? (
          <div className="py-12 text-center">
            <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-green-600 border-t-transparent" />
            <p className="mt-4 text-gray-600">Loading marketplace items...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="py-12 text-center">
            {emptyIcon}
            <p className="text-lg text-gray-600">No items found matching your criteria.</p>
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredItems.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className="overflow-hidden rounded-xl bg-white shadow-md transition-shadow hover:shadow-lg"
              >
                <div className="p-6">
                  <div className="mb-4 flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="mb-2 text-lg font-bold text-gray-900">{item.name}</h3>
                      <p className="mb-2 text-sm text-gray-500">{item.supplier_name || "Verified Seller"}</p>
                      {(item.supplier_rating || 0) > 0 && (
                        <div className="flex items-center gap-1">
                          <span className="text-yellow-500">★</span>
                          <span className="text-sm font-medium">{(item.supplier_rating || 0).toFixed(1)}</span>
                        </div>
                      )}
                    </div>
                    {item.supplier_verification === "approved" && (
                      <span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-700">Verified</span>
                    )}
                  </div>

                  <p className="mb-4 line-clamp-2 text-sm text-gray-600">{item.description || "Quality agricultural listing"}</p>
                  <div className="mb-4 space-y-2">
                    <div className="flex items-center justify-between text-sm"><span className="text-gray-600">Category:</span><span className="font-medium">{getCategoryLabel(item.category || "crop")}</span></div>
                    <div className="flex items-center justify-between text-sm"><span className="text-gray-600">{item.kind === "request" ? "Target:" : "Price:"}</span><span className="font-bold text-green-600">${item.price.toFixed(2)}</span></div>
                    <div className="flex items-center justify-between text-sm"><span className="text-gray-600">{item.kind === "request" ? "Needed:" : "Stock:"}</span><span className="font-medium text-green-600">{item.quantity_available || 0} {item.quantity_unit || "units"}</span></div>
                  </div>
                  <button className="w-full rounded-lg bg-green-600 px-4 py-2 font-medium text-white transition-colors hover:bg-green-700" onClick={() => (window.location.href = `/products/${item.id}`)}>
                    {item.kind === "request" ? "View Request" : "View Details"}
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl bg-white shadow-md">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Item</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Seller</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Stock</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Rating</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredItems.map((item, index) => (
                  <motion.tr key={item.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3, delay: index * 0.05 }} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium text-gray-900">{item.name}</div>
                        <div className="line-clamp-1 text-sm text-gray-500">{item.description || ""}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{item.supplier_name || "Verified Seller"}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{getCategoryLabel(item.category || "crop")}</td>
                    <td className="px-6 py-4 text-sm font-medium text-green-600">${item.price.toFixed(2)}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{item.quantity_available || 0} {item.quantity_unit || "units"}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{(item.supplier_rating || 0) > 0 ? `★ ${(item.supplier_rating || 0).toFixed(1)}` : "N/A"}</td>
                    <td className="px-6 py-4">
                      <button className="text-sm font-medium text-green-600 hover:text-green-700" onClick={() => (window.location.href = `/products/${item.id}`)}>
                        {item.kind === "request" ? "View Request" : "View"}
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
