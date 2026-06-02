import { useState, useEffect } from 'react';
import { getSupplierProductDetail, createSupplierOrder } from '../api';
import { Package, Star, MapPin, ShoppingCart, ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react';

interface Product {
  id: string;
  name: string;
  description?: string;
  price: number;
  category: string;
  quantity_available: number;
  supplier_name?: string;
  supplier_rating?: number;
  photo_urls?: string[];
}

interface SupplierProductDetailProps {
  productId: string;
  onBack?: () => void;
}

export function SupplierProductDetail({ productId, onBack }: SupplierProductDetailProps) {
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [showCheckout, setShowCheckout] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);
  const [checkoutData, setCheckoutData] = useState({
    delivery_address: '',
    delivery_phone: '',
    delivery_method: 'platform_driver',
    buyer_notes: '',
  });
  const [orderLoading, setOrderLoading] = useState(false);

  useEffect(() => {
    loadProduct();
  }, [productId]);

  const loadProduct = async () => {
    try {
      const data = await getSupplierProductDetail(productId);
      setProduct(data);
    } catch (err) {
      setMessage({ type: 'error', text: 'Unable to load this product. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = () => {
    setMessage(null);
    if (quantity > (product?.quantity_available || 0)) {
      setMessage({ type: 'error', text: 'Insufficient stock for the selected quantity.' });
      return;
    }
    setShowCheckout(true);
  };

  const handlePlaceOrder = async (e) => {
    e.preventDefault();
    setOrderLoading(true);
    try {
      await createSupplierOrder({
        items: [{ product_id: productId, quantity }],
        delivery_address: checkoutData.delivery_address,
        delivery_phone: checkoutData.delivery_phone,
        shipping_method: checkoutData.delivery_method,
        buyer_notes: checkoutData.buyer_notes,
      });
      setMessage({ type: 'success', text: 'Order placed successfully.' });
      setShowCheckout(false);
      onBack?.();
    } catch (err) {
      setMessage({ type: 'error', text: `Error placing order: ${err.message}` });
    } finally {
      setOrderLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!product) {
    return <div className="text-center py-12 text-earth-500">Product not found</div>;
  }

  const total = (product.price || 0) * quantity;

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="flex items-center gap-2 text-earth-600 hover:text-earth-800">
        <ArrowLeft className="w-5 h-5" /> Back to Marketplace
      </button>

      {message && (
        <div className={`rounded-2xl border px-4 py-3 text-sm font-bold ${
          message.type === 'success'
            ? 'border-green-200 bg-green-50 text-green-700'
            : 'border-red-200 bg-red-50 text-red-700'
        }`}>
          {message.text}
        </div>
      )}

      {!showCheckout ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            {product.photo_urls?.[0] && (
              <img src={product.photo_urls[0]} alt={product.name} className="w-full h-64 object-cover rounded-xl mb-6" />
            )}
            <h1 className="text-3xl font-black text-earth-800 mb-2">{product.name}</h1>
            <p className="text-earth-600 mb-4">{product.description}</p>
            
            <div className="flex items-center gap-4 mb-6">
              <div className="text-3xl font-black text-green-600">${product.price?.toFixed(2)}</div>
              {product.quantity_available > 0 ? (
                <div className="flex items-center gap-1 text-green-600">
                  <CheckCircle className="w-5 h-5" /> {product.quantity_available} in stock
                </div>
              ) : (
                <div className="flex items-center gap-1 text-red-600">
                  <AlertCircle className="w-5 h-5" /> Out of stock
                </div>
              )}
            </div>

            <div className="space-y-3 mb-6">
              <div className="flex items-center gap-2 text-earth-600">
                <Package className="w-5 h-5" />
                <span className="font-medium">Category:</span>
                <span>{product.category}</span>
              </div>
              <div className="flex items-center gap-2 text-earth-600">
                <MapPin className="w-5 h-5" />
                <span className="font-medium">Supplier:</span>
                <span>{product.supplier_name}</span>
              </div>
              {product.supplier_rating && (
                <div className="flex items-center gap-2 text-earth-600">
                  <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                  <span className="font-medium">Rating:</span>
                  <span>{product.supplier_rating.toFixed(1)}</span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-4 mb-6">
              <label className="font-bold text-earth-700">Quantity:</label>
              <input
                type="number"
                min="1"
                max={product.quantity_available}
                value={quantity}
                onChange={(e) => setQuantity(Math.min(parseInt(e.target.value) || 1, product.quantity_available))}
                className="w-24 px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              />
            </div>

            <button
              onClick={handleAddToCart}
              disabled={product.quantity_available === 0}
              className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-black py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              <ShoppingCart className="w-5 h-5" /> Add to Order
            </button>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-6 h-fit">
            <h3 className="text-xl font-black text-earth-800 mb-4">Order Summary</h3>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between">
                <span className="text-earth-600">Subtotal ({quantity} × ${product.price?.toFixed(2)})</span>
                <span className="font-bold">${total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-earth-600">Escrow protection</span>
                <span className="font-bold text-green-600">Included</span>
              </div>
              <div className="border-t border-earth-200 pt-3 flex justify-between">
                <span className="font-black text-earth-800">Total</span>
                <span className="font-black text-2xl text-green-600">${total.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-lg p-6 max-w-2xl mx-auto">
          <h2 className="text-2xl font-black text-earth-800 mb-6">Checkout</h2>
          <form onSubmit={handlePlaceOrder} className="space-y-4">
            <div className="bg-earth-50 rounded-xl p-4 mb-4">
              <h3 className="font-bold text-earth-800 mb-2">Order Summary</h3>
              <div className="flex justify-between mb-2">
                <span className="text-earth-600">{product.name} × {quantity}</span>
                <span className="font-bold">${total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between mb-2">
                <span className="text-earth-600">Escrow protection</span>
                <span className="font-bold text-green-600">Included</span>
              </div>
              <div className="border-t border-earth-200 pt-2 flex justify-between">
                <span className="font-black text-earth-800">Total</span>
                <span className="font-black text-xl text-green-600">${total.toFixed(2)}</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Delivery Address *</label>
              <input
                type="text"
                value={checkoutData.delivery_address}
                onChange={(e) => setCheckoutData({ ...checkoutData, delivery_address: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Delivery Phone *</label>
              <input
                type="tel"
                value={checkoutData.delivery_phone}
                onChange={(e) => setCheckoutData({ ...checkoutData, delivery_phone: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Delivery Method</label>
              <select
                value={checkoutData.delivery_method}
                onChange={(e) => setCheckoutData({ ...checkoutData, delivery_method: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              >
                <option value="platform_driver">Driver Delivery (ZimAgriTrust)</option>
                <option value="buyer_pickup">Buyer Pickup</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Notes (Optional)</label>
              <textarea
                value={checkoutData.buyer_notes}
                onChange={(e) => setCheckoutData({ ...checkoutData, buyer_notes: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                rows={3}
              />
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowCheckout(false)}
                className="flex-1 bg-earth-200 hover:bg-earth-300 text-earth-800 font-bold py-3 px-6 rounded-xl"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={orderLoading}
                className="flex-1 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white font-bold py-3 px-6 rounded-xl"
              >
                {orderLoading ? 'Placing Order...' : `Pay $${total.toFixed(2)}`}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
