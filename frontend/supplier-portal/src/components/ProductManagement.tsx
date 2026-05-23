import React, { useState, useEffect } from 'react';
import { getProducts, createProduct, updateProduct, deleteProduct, boostProduct } from '../api.ts';
import { Plus, Edit, Trash2, Zap, Search, Filter } from 'lucide-react';

export function ProductManagement() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    loadProducts();
  }, [statusFilter]);

  const loadProducts = async () => {
    try {
      const data = await getProducts(statusFilter);
      setProducts(data);
    } catch (err) {
      console.error('Load products error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (formData) => {
    try {
      if (editingProduct) {
        await updateProduct(editingProduct.id, formData);
      } else {
        await createProduct(formData);
      }
      setShowModal(false);
      setEditingProduct(null);
      loadProducts();
    } catch (err) {
      alert('Error saving product: ' + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this product?')) return;
    try {
      await deleteProduct(id);
      loadProducts();
    } catch (err) {
      alert('Error deleting product: ' + err.message);
    }
  };

  const handleBoost = async (id) => {
    if (!confirm('Boost this product for 7 days? Fee: $5 (input) or $10 (machinery)')) return;
    try {
      await boostProduct(id, 7);
      loadProducts();
    } catch (err) {
      alert('Error boosting product: ' + err.message);
    }
  };

  const filtered = products.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="text-center py-12">Loading products...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-black text-earth-800">Product Management</h2>
        <button
          onClick={() => { setEditingProduct(null); setShowModal(true); }}
          className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white font-bold px-4 py-2 rounded-xl"
        >
          <Plus className="w-5 h-5" /> Add Product
        </button>
      </div>

      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-earth-400" />
          <input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="draft">Draft</option>
          <option value="out_of_stock">Out of Stock</option>
        </select>
      </div>

      <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-earth-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Product</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Category</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Price</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Stock</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-earth-200">
            {filtered.map((product) => (
              <tr key={product.id} className="hover:bg-earth-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    {product.photo_urls?.[0] && (
                      <img src={product.photo_urls[0]} alt="" className="w-12 h-12 rounded-lg object-cover" />
                    )}
                    <div>
                      <p className="font-bold text-earth-800">{product.name}</p>
                      <p className="text-xs text-earth-500">{product.sku}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-earth-600 capitalize">
                  {product.input_category || product.machinery_category || '-'}
                </td>
                <td className="px-6 py-4 font-bold text-earth-800">${product.price.toFixed(2)}</td>
                <td className="px-6 py-4 text-sm text-earth-600">{product.quantity_available}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                    product.status === 'active' ? 'bg-green-100 text-green-700' :
                    product.status === 'draft' ? 'bg-gray-100 text-gray-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {product.status}
                  </span>
                  {product.is_boosted && <Zap className="w-4 h-4 text-yellow-500 inline ml-1" />}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <button onClick={() => { setEditingProduct(product); setShowModal(true); }} className="p-2 hover:bg-earth-100 rounded-lg">
                      <Edit className="w-4 h-4 text-earth-600" />
                    </button>
                    <button onClick={() => handleBoost(product.id)} className="p-2 hover:bg-yellow-100 rounded-lg" title="Boost">
                      <Zap className="w-4 h-4 text-yellow-600" />
                    </button>
                    <button onClick={() => handleDelete(product.id)} className="p-2 hover:bg-red-100 rounded-lg">
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-earth-500">No products found</div>
        )}
      </div>

      {showModal && (
        <ProductModal
          product={editingProduct}
          onClose={() => { setShowModal(false); setEditingProduct(null); }}
          onSave={handleSave}
        />
      )}
    </div>
  );
}

function ProductModal({ product, onClose, onSave }) {
  const [formData, setFormData] = useState(product || {
    product_type: 'input',
    input_category: '',
    machinery_category: '',
    name: '',
    description: '',
    price: '',
    quantity_available: 0,
    unit_type: 'piece',
    min_stock_level: 5,
    manufacturer: '',
    condition: 'new',
    warranty_months: '',
    delivery_included: false,
    photo_urls: [],
    status: 'draft',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = {
      ...formData,
      price: parseFloat(formData.price),
      quantity_available: parseInt(formData.quantity_available),
      min_stock_level: parseInt(formData.min_stock_level),
      warranty_months: formData.warranty_months ? parseInt(formData.warranty_months) : null,
    };
    onSave(data);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
        <h3 className="text-xl font-black text-earth-800 mb-4">{product ? 'Edit Product' : 'Add Product'}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Product Type *</label>
              <select
                value={formData.product_type}
                onChange={(e) => setFormData({ ...formData, product_type: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                required
              >
                <option value="input">Input (Seeds, Fertilizer, etc.)</option>
                <option value="machinery">Machinery</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                required
              />
            </div>
          </div>

          {formData.product_type === 'input' ? (
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Category</label>
              <select
                value={formData.input_category}
                onChange={(e) => setFormData({ ...formData, input_category: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              >
                <option value="">Select...</option>
                <option value="seeds">Seeds</option>
                <option value="fertilizer">Fertilizer</option>
                <option value="pesticides">Pesticides</option>
                <option value="herbicides">Herbicides</option>
                <option value="fungicides">Fungicides</option>
                <option value="animal_feed">Animal Feed</option>
              </select>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Category</label>
              <select
                value={formData.machinery_category}
                onChange={(e) => setFormData({ ...formData, machinery_category: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              >
                <option value="">Select...</option>
                <option value="tractor">Tractor</option>
                <option value="sprayer">Sprayer</option>
                <option value="irrigation">Irrigation</option>
                <option value="tiller">Tiller</option>
                <option value="harvester">Harvester</option>
                <option value="tools">Tools</option>
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm font-bold text-earth-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Price (USD) *</label>
              <input
                type="number"
                step="0.01"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Quantity *</label>
              <input
                type="number"
                value={formData.quantity_available}
                onChange={(e) => setFormData({ ...formData, quantity_available: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Unit</label>
              <input
                type="text"
                value={formData.unit_type}
                onChange={(e) => setFormData({ ...formData, unit_type: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Min Stock Level</label>
              <input
                type="number"
                value={formData.min_stock_level}
                onChange={(e) => setFormData({ ...formData, min_stock_level: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-1">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              >
                <option value="draft">Draft</option>
                <option value="active">Active</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button type="submit" className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-bold py-2 rounded-xl">
              Save Product
            </button>
            <button type="button" onClick={onClose} className="flex-1 bg-earth-200 hover:bg-earth-300 text-earth-800 font-bold py-2 rounded-xl">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
