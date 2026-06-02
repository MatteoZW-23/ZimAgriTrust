import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, CheckCircle, Heart, MapPin, Package, Shield, ShoppingCart, Star } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export default function ProductDetail() {
  const { productId } = useParams();
  const [product, setProduct] = useState<any>(null);
  const [party, setParty] = useState<any>(null);
  const [sourceType, setSourceType] = useState<"supplier" | "crop" | null>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [showCheckout, setShowCheckout] = useState(false);
  const [checkoutData, setCheckoutData] = useState({
    delivery_address: "",
    delivery_phone: "",
    shipping_method: "platform_driver",
    buyer_notes: "",
  });
  const [orderLoading, setOrderLoading] = useState(false);

  useEffect(() => {
    void fetchDetail();
  }, [productId]);

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const supplierResponse = await fetch(`${API}/suppliers/public/products/${productId}`);
      if (supplierResponse.ok) {
        const data = await supplierResponse.json();
        setProduct({
          ...data,
          name: data.name,
          price: Number(data.price || 0),
          quantity_available: Number(data.quantity_available || 0),
        });
        setParty(data?.supplier || null);
        setSourceType("supplier");
        return;
      }

      const cropResponse = await fetch(`${API}/public/listings/${productId}`);
      if (!cropResponse.ok) throw new Error("Listing not found");
      const crop = await cropResponse.json();
      setProduct({
        ...crop,
        name: crop.product_type || crop.crop || crop.title || "Crop Listing",
        price: Number(crop.price_per_unit || 0),
        quantity_available: Number(crop.quantity || 0),
        category: String(crop.product_type || "crop").toLowerCase(),
        supplier_verification: crop.seller_verified ? "approved" : "pending",
        supplier_rating: Number(crop.seller_trust_score || 0) / 20,
      });
      setParty({
        business_name: crop.seller_name || "Verified Farmer",
      });
      setSourceType("crop");
    } catch {
      setProduct(null);
      setParty(null);
      setSourceType(null);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryLabel = (cat: string) => {
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
      crop: "Crop",
    };
    return labels[String(cat || "").toLowerCase()] || cat || "Product";
  };

  const isCrop = sourceType === "crop";
  const isSupplierProduct = sourceType === "supplier";
  const isMachinery = isSupplierProduct && ["tractor", "sprayer", "irrigation", "tiller", "harvester", "tools"].includes(String(product?.category || "").toLowerCase());
  const orderSubtotal = Number(product?.price || 0) * quantity;

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isSupplierProduct) return;
    setOrderLoading(true);
    try {
      const response = await fetch(`${API}/suppliers/public/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          items: [{ product_id: productId, quantity }],
          delivery_address: checkoutData.delivery_address,
          delivery_phone: checkoutData.delivery_phone,
          shipping_method: checkoutData.shipping_method,
          buyer_notes: checkoutData.buyer_notes,
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        if (response.status === 401) throw new Error("Please log in to place a supplier order.");
        throw new Error(error.detail || "Order failed");
      }

      alert("Order placed successfully. You can track it from your portal orders.");
      setShowCheckout(false);
    } catch (err) {
      alert(`Error placing order: ${(err as Error).message}`);
    } finally {
      setOrderLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-earth-50">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-green-600 border-t-transparent" />
          <p className="mt-4 text-gray-600">Loading details...</p>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-earth-50">
        <div className="text-center">
          <Package size={48} className="mx-auto mb-4 text-gray-300" />
          <p className="text-lg text-gray-600">Item not found.</p>
          <Link to="/marketplace" className="mt-4 inline-block text-green-600 hover:text-green-700">Back to Marketplace</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-earth-50">
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <Link to="/marketplace" className="inline-flex items-center gap-2 text-gray-600 transition hover:text-gray-900">
            <ArrowLeft size={18} />
            Back to Marketplace
          </Link>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-2">
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
            <div className="overflow-hidden rounded-2xl bg-white shadow-lg">
              <div className="flex aspect-square items-center justify-center bg-gray-100 text-5xl font-bold text-green-700">
                {String(product.name || "PR").slice(0, 2).toUpperCase()}
              </div>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
            <div className="rounded-2xl bg-white p-8 shadow-lg">
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <span className="mb-2 inline-block rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-700">
                    {getCategoryLabel(product.category)}
                  </span>
                  <h1 className="mb-2 text-3xl font-bold text-gray-900">{product.name}</h1>
                  <div className="flex items-center gap-2 text-gray-600">
                    {party && <span className="font-medium">{party.business_name}</span>}
                    <span>•</span>
                    <div className="flex items-center gap-1">
                      <Star size={16} className="fill-yellow-400 text-yellow-400" />
                      <span className="font-medium">{(Number(product.supplier_rating || 0)).toFixed(1)}</span>
                    </div>
                  </div>
                </div>
                {product.supplier_verification === "approved" && (
                  <div className="flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-700">
                    <CheckCircle size={16} />
                    Verified
                  </div>
                )}
              </div>

              <p className="mb-6 text-4xl font-bold text-green-600">
                ${Number(product.price || 0).toFixed(2)}
                <span className="text-lg font-normal text-gray-500">/{isMachinery ? "item" : "unit"}</span>
              </p>

              <div className="mb-6 space-y-4">
                <div className="flex items-center justify-between rounded-lg bg-gray-50 p-4">
                  <span className="text-gray-600">Availability:</span>
                  <span className={`font-medium ${(product.quantity_available || 0) > 0 ? "text-green-600" : "text-red-600"}`}>
                    {(product.quantity_available || 0) > 0 ? `${product.quantity_available} in stock` : "Out of stock"}
                  </span>
                </div>
                {!isMachinery && (
                  <div className="flex items-center justify-between rounded-lg bg-gray-50 p-4">
                    <span className="text-gray-600">Quantity:</span>
                    <div className="flex items-center gap-3">
                      <button onClick={() => setQuantity(Math.max(1, quantity - 1))} className="flex h-10 w-10 items-center justify-center rounded-lg border border-gray-300 transition hover:bg-gray-100">-</button>
                      <span className="w-12 text-center font-medium">{quantity}</span>
                      <button onClick={() => setQuantity(quantity + 1)} className="flex h-10 w-10 items-center justify-center rounded-lg border border-gray-300 transition hover:bg-gray-100">+</button>
                    </div>
                  </div>
                )}
              </div>

              <div className="mb-6 rounded-xl border border-green-200 bg-green-50 p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Shield size={20} className="text-green-600" />
                  <span className="font-semibold text-green-900">Escrow Protection</span>
                </div>
                <p className="text-sm text-green-700">
                  {isCrop
                    ? "Farmer crop trades settle through escrow after negotiation, delivery completion, and buyer confirmation."
                    : "Supplier checkout totals are protected in escrow. Platform fees settle after delivery instead of being added as surprise buyer charges."}
                </p>
              </div>

              <div className="mb-6 space-y-3">
                {isSupplierProduct ? (
                  <>
                    <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 px-6 py-3 font-medium text-white transition-colors hover:bg-green-700">
                      <ShoppingCart size={20} />
                      {isMachinery ? "Contact Supplier" : "Add to Cart"}
                    </button>
                    {!isMachinery && (
                      <button onClick={() => setShowCheckout(true)} className="w-full rounded-lg bg-gray-900 px-6 py-3 font-medium text-white transition-colors hover:bg-gray-800">
                        Buy Now
                      </button>
                    )}
                  </>
                ) : (
                  <Link to="/dashboard" className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 px-6 py-3 font-medium text-white transition-colors hover:bg-green-700">
                    <ShoppingCart size={20} />
                    Sign In to Trade This Crop
                  </Link>
                )}
                <button className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-300 px-6 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50">
                  <Heart size={20} />
                  Save Listing
                </button>
              </div>

              <div className="space-y-3 border-t border-gray-100 pt-6 text-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <MapPin size={16} />
                  {product.location || product.location_label || product.location_district || product.location_province || "Zimbabwe"}
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <Package size={16} />
                  {product.description || "Quality agricultural product available for verified trade."}
                </div>
              </div>
            </div>

            <div className="mt-8 rounded-2xl bg-white p-8 shadow-lg">
              <h3 className="mb-6 text-xl font-bold text-gray-900">Listing Details</h3>
              <div className="space-y-4">
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-600">Category</span>
                  <span className="font-medium">{getCategoryLabel(product.category)}</span>
                </div>
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-600">{isCrop ? "Commodity" : "Product Type"}</span>
                  <span className="font-medium">{product.product_type || product.name || "Standard"}</span>
                </div>
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-600">Availability</span>
                  <span className="font-medium">{product.quantity_available || "In stock"}</span>
                </div>
                <div className="flex justify-between border-b border-gray-100 pb-3">
                  <span className="text-gray-600">Location</span>
                  <span className="font-medium">{product.location || product.location_district || product.location_province || "Zimbabwe"}</span>
                </div>
                {party && (
                  <div className="flex justify-between border-b border-gray-100 pb-3">
                    <span className="text-gray-600">{isCrop ? "Farmer" : "Supplier"}</span>
                    <span className="font-medium">{party.business_name}</span>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {showCheckout && isSupplierProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
            <h3 className="text-2xl font-bold text-gray-900">Secure Checkout</h3>
            <p className="mt-2 text-sm text-gray-600">Escrow holds your payment until delivery is completed.</p>
            <form className="mt-6 space-y-4" onSubmit={handlePlaceOrder}>
              <input value={checkoutData.delivery_address} onChange={(e) => setCheckoutData((prev) => ({ ...prev, delivery_address: e.target.value }))} required placeholder="Delivery address" className="w-full rounded-xl border border-gray-300 px-4 py-3 focus:border-green-500 focus:outline-none" />
              <input value={checkoutData.delivery_phone} onChange={(e) => setCheckoutData((prev) => ({ ...prev, delivery_phone: e.target.value }))} required placeholder="Delivery phone number" className="w-full rounded-xl border border-gray-300 px-4 py-3 focus:border-green-500 focus:outline-none" />
              <select value={checkoutData.shipping_method} onChange={(e) => setCheckoutData((prev) => ({ ...prev, shipping_method: e.target.value }))} className="w-full rounded-xl border border-gray-300 px-4 py-3 focus:border-green-500 focus:outline-none">
                <option value="platform_driver">Platform Driver</option>
                <option value="buyer_pickup">Buyer Pickup</option>
              </select>
              <textarea value={checkoutData.buyer_notes} onChange={(e) => setCheckoutData((prev) => ({ ...prev, buyer_notes: e.target.value }))} placeholder="Notes for supplier" className="w-full rounded-xl border border-gray-300 px-4 py-3 focus:border-green-500 focus:outline-none" rows={4} />
              <div className="rounded-xl bg-gray-50 p-4 text-sm text-gray-700">
                <div className="flex justify-between"><span>Subtotal</span><span>${orderSubtotal.toFixed(2)}</span></div>
                <div className="mt-2 flex justify-between"><span>Escrow protection</span><span className="text-green-600">Included</span></div>
                <div className="mt-3 flex justify-between border-t border-gray-200 pt-3 text-base font-bold"><span>Total held in escrow</span><span>${orderSubtotal.toFixed(2)}</span></div>
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={() => setShowCheckout(false)} className="flex-1 rounded-xl border border-gray-300 px-4 py-3 font-semibold text-gray-700 transition hover:bg-gray-50">Cancel</button>
                <button type="submit" disabled={orderLoading} className="flex-1 rounded-xl bg-green-600 px-4 py-3 font-semibold text-white transition hover:bg-green-700 disabled:opacity-60">
                  {orderLoading ? "Placing Order..." : "Place Order"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
