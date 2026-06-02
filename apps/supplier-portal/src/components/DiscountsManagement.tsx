import React, { useState, useEffect } from 'react';
import { createDiscount, listDiscounts, getDiscount, updateDiscount, deleteDiscount, validateDiscount } from '../api.ts';
import { Plus, Edit, Trash2, Tag, Percent, DollarSign, Calendar, CheckCircle, XCircle } from 'lucide-react';

export function DiscountsManagement({ featureAccess }) {
  const [discounts, setDiscounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingDiscount, setEditingDiscount] = useState(null);
  const [formData, setFormData] = useState({
    code: '',
    discount_type: 'percentage',
    discount_value: '',
    min_order_value: '',
    max_discount_amount: '',
    max_uses: '',
    max_uses_per_user: '',
    start_date: '',
    end_date: '',
    description: '',
  });
  const [validationResult, setValidationResult] = useState(null);

  useEffect(() => {
    if (!featureAccess?.promotions) {
      setLoading(false);
      return;
    }
    loadDiscounts();
  }, [featureAccess]);

  const loadDiscounts = async () => {
    try {
      const data = await listDiscounts(false);
      setDiscounts(data || []);
    } catch (err) {
      console.error('Failed to load discounts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await createDiscount(formData);
      setShowModal(false);
      resetForm();
      loadDiscounts();
    } catch (err) {
      console.error('Failed to create discount:', err);
    }
  };

  const handleUpdate = async () => {
    try {
      await updateDiscount(editingDiscount.id, formData);
      setShowModal(false);
      resetForm();
      loadDiscounts();
    } catch (err) {
      console.error('Failed to update discount:', err);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this discount?')) return;
    try {
      await deleteDiscount(id);
      loadDiscounts();
    } catch (err) {
      console.error('Failed to delete discount:', err);
    }
  };

  const handleEdit = (discount) => {
    setEditingDiscount(discount);
    setFormData({
      code: discount.code,
      discount_type: discount.discount_type,
      discount_value: discount.discount_value,
      min_order_value: discount.min_order_value || '',
      max_discount_amount: discount.max_discount_amount || '',
      max_uses: discount.max_uses || '',
      max_uses_per_user: discount.max_uses_per_user || '',
      start_date: discount.start_date?.split('T')[0] || '',
      end_date: discount.end_date?.split('T')[0] || '',
      description: discount.description || '',
    });
    setShowModal(true);
  };

  const resetForm = () => {
    setFormData({
      code: '',
      discount_type: 'percentage',
      discount_value: '',
      min_order_value: '',
      max_discount_amount: '',
      max_uses: '',
      max_uses_per_user: '',
      start_date: '',
      end_date: '',
      description: '',
    });
    setEditingDiscount(null);
  };

  const handleValidate = async () => {
    const code = prompt('Enter discount code to validate:');
    if (!code) return;
    const orderTotal = prompt('Enter order total:');
    if (!orderTotal) return;
    try {
      const result = await validateDiscount(code, parseFloat(orderTotal), []);
      setValidationResult(result);
    } catch (err) {
      console.error('Failed to validate discount:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!featureAccess?.promotions) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <h2 className="text-2xl font-black text-earth-800">Discounts & Promotions</h2>
        <p className="mt-3 text-earth-600 font-bold">
          Promotional discounts are available on Pro and Enterprise supplier subscriptions.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-black text-earth-800">Discounts & Promotions</h3>
        <div className="flex gap-3">
          <button
            onClick={handleValidate}
            className="px-4 py-2 bg-earth-100 text-earth-800 font-bold rounded-xl hover:bg-earth-200 transition-colors"
          >
            Validate Code
          </button>
          <button
            onClick={() => {
              resetForm();
              setShowModal(true);
            }}
            className="px-4 py-2 bg-primary-600 text-white font-bold rounded-xl hover:bg-primary-700 transition-colors flex items-center gap-2"
          >
            <Plus size={16} />
            Create Discount
          </button>
        </div>
      </div>

      {validationResult && (
        <div className={`p-4 rounded-xl ${validationResult.valid ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="flex items-center gap-2 mb-2">
            {validationResult.valid ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600" />
            )}
            <span className={`font-bold ${validationResult.valid ? 'text-green-700' : 'text-red-700'}`}>
              {validationResult.valid ? 'Valid Code' : 'Invalid Code'}
            </span>
          </div>
          {validationResult.valid && (
            <div className="text-sm text-earth-700">
              <p>Discount Amount: ${validationResult.discount_amount}</p>
              <p>Final Total: ${validationResult.final_total}</p>
            </div>
          )}
          {!validationResult.valid && (
            <p className="text-sm text-red-700">{validationResult.error}</p>
          )}
          <button
            onClick={() => setValidationResult(null)}
            className="mt-2 text-sm text-earth-600 hover:text-earth-800"
          >
            Close
          </button>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-lg p-6">
        {discounts.length === 0 ? (
          <p className="text-earth-500 text-center py-8">No discounts yet</p>
        ) : (
          <div className="space-y-4">
            {discounts.map((discount) => (
              <DiscountCard
                key={discount.id}
                discount={discount}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-black text-earth-800 mb-4">
              {editingDiscount ? 'Edit Discount' : 'Create Discount'}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-earth-600 mb-2">Code</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
                  placeholder="DISCOUNT20"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-earth-600 mb-2">Type</label>
                  <select
                    value={formData.discount_type}
                    onChange={(e) => setFormData({ ...formData, discount_type: e.target.value })}
                    className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
                  >
                    <option value="percentage">Percentage</option>
                    <option value="fixed_amount">Fixed Amount</option>
                    <option value="buy_x_get_y">Buy X Get Y</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-bold text-earth-600 mb-2">Value</label>
                  <input
                    type="number"
                    value={formData.discount_value}
                    onChange={(e) => setFormData({ ...formData, discount_value: e.target.value })}
                    className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
                    placeholder="20"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-earth-600 mb-2">Min Order Value</label>
                  <input
                    type="number"
                    value={formData.min_order_value}
                    onChange={(e) => setFormData({ ...formData, min_order_value: e.target.value })}
                    className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-earth-600 mb-2">Max Discount</label>
                  <input
                    type="number"
                    value={formData.max_discount_amount}
                    onChange={(e) => setFormData({ ...formData, max_discount_amount: e.target.value })}
                    className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
                    placeholder="50"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-earth-600 mb-2">Max Uses</label>
                  <input
                    type="number"
                    value={formData.max_uses}
                    onChange={(e) => setFormData({ ...formData, max_uses: e.target.value })}
                    className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-earth-600 mb-2">Max Uses Per User</label>
                  <input
                    type="number"
                    value={formData.max_uses_per_user}
                    onChange={(e) => setFormData({ ...formData, max_uses_per_user: e.target.value })}
                    className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
                    placeholder="1"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-earth-600 mb-2">Start Date</label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-earth-600 mb-2">End Date</label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-bold text-earth-600 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none resize-none h-24"
                  placeholder="Description of the discount"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={editingDiscount ? handleUpdate : handleCreate}
                className="flex-1 py-3 bg-primary-600 text-white font-black rounded-xl hover:bg-primary-700 transition-colors"
              >
                {editingDiscount ? 'Update' : 'Create'}
              </button>
              <button
                onClick={() => {
                  setShowModal(false);
                  resetForm();
                }}
                className="flex-1 py-3 bg-earth-100 text-earth-800 font-black rounded-xl hover:bg-earth-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DiscountCard({ discount, onEdit, onDelete }) {
  const typeIcons = {
    percentage: Percent,
    fixed_amount: DollarSign,
    buy_x_get_y: Tag,
  };
  const Icon = typeIcons[discount.discount_type] || Tag;

  const now = new Date();
  const startDate = new Date(discount.start_date);
  const endDate = new Date(discount.end_date);
  const isActive = discount.is_active && startDate <= now && endDate >= now;

  return (
    <div className={`p-6 rounded-xl ${isActive ? 'bg-green-50' : 'bg-gray-50'}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 ${isActive ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-600'} rounded-xl flex items-center justify-center`}>
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <p className="text-2xl font-black text-earth-800">{discount.code}</p>
            <p className="text-sm text-earth-600 capitalize">{discount.discount_type}</p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-lg text-xs font-black uppercase ${isActive ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'}`}>
          {isActive ? 'Active' : 'Inactive'}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div>
          <p className="text-sm text-earth-500">Value</p>
          <p className="font-bold text-earth-800">
            {discount.discount_type === 'percentage' ? `${discount.discount_value}%` : `$${discount.discount_value}`}
          </p>
        </div>
        <div>
          <p className="text-sm text-earth-500">Uses</p>
          <p className="font-bold text-earth-800">{discount.current_uses}/{discount.max_uses || '∞'}</p>
        </div>
        <div>
          <p className="text-sm text-earth-500">Start</p>
          <p className="font-bold text-earth-800">{new Date(discount.start_date).toLocaleDateString()}</p>
        </div>
        <div>
          <p className="text-sm text-earth-500">End</p>
          <p className="font-bold text-earth-800">{new Date(discount.end_date).toLocaleDateString()}</p>
        </div>
      </div>

      {discount.description && (
        <p className="text-earth-600 text-sm mb-4">{discount.description}</p>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => onEdit(discount)}
          className="px-4 py-2 bg-blue-100 text-blue-700 font-bold text-sm rounded-lg hover:bg-blue-200 transition-colors flex items-center gap-2"
        >
          <Edit size={14} />
          Edit
        </button>
        <button
          onClick={() => onDelete(discount.id)}
          className="px-4 py-2 bg-red-100 text-red-700 font-bold text-sm rounded-lg hover:bg-red-200 transition-colors flex items-center gap-2"
        >
          <Trash2 size={14} />
          Delete
        </button>
      </div>
    </div>
  );
}
