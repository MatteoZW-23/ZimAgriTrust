import { useState, useEffect } from 'react';
import { getSuppliersList, getAllSupplierProducts } from '../api';
import { Search, Filter, Star, MapPin, ChevronDown, Grid, List } from 'lucide-react';

interface Product {
  id: string;
  name: string;
  description?: string;
  price: number;
  category: string;
  product_type: string;
  quantity_available: number;
  supplier_name?: string;
}

interface Supplier {
  id: string;
  business_name: string;
  location?: string;
  rating?: number;
}

interface SupplierMarketplaceProps {
  onProductSelect?: (productId: string) => void;
}

interface ProductCardProps {
  product: Product;
  onProductSelect?: (productId: string) => void;
}

interface SupplierCardProps {
  supplier: Supplier;
}

export function SupplierMarketplace({ onProductSelect }: SupplierMarketplaceProps) {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('products'); // 'suppliers' or 'products'
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [productTypeFilter, setProductTypeFilter] = useState('all');
  const [viewMode, setViewMode] = useState('grid');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    loadData();
  }, [view]);

  const loadData = async () => {
    try {
      if (view === 'suppliers') {
        const data = await getSuppliersList(100);
        setSuppliers(data);
      } else {
        const data = await getAllSupplierProducts({ limit: '100' });
        setProducts(data);
      }
    } catch (err) {
      console.error('Load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(p => 
    p.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.description?.toLowerCase().includes(searchTerm.toLowerCase())
  ).filter(p => {
    if (categoryFilter !== 'all' && p.category !== categoryFilter) return false;
    if (productTypeFilter !== 'all' && p.product_type !== productTypeFilter) return false;
    return true;
  });

  const filteredSuppliers = suppliers.filter(s =>
    s.business_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.location?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const categories = [...new Set(products.map(p => p.category).filter(Boolean))];
  const productTypes = [...new Set(products.map(p => p.product_type).filter(Boolean))];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-black text-earth-800">Supplier Marketplace</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setView('products')}
            className={`px-4 py-2 rounded-xl font-medium transition-colors ${
              view === 'products' ? 'bg-primary-600 text-white' : 'bg-earth-100 text-earth-700'
            }`}
          >
            Products
          </button>
          <button
            onClick={() => setView('suppliers')}
            className={`px-4 py-2 rounded-xl font-medium transition-colors ${
              view === 'suppliers' ? 'bg-primary-600 text-white' : 'bg-earth-100 text-earth-700'
            }`}
          >
            Suppliers
          </button>
        </div>
      </div>

      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-earth-400" />
          <input
            type="text"
            placeholder={view === 'products' ? "Search products..." : "Search suppliers..."}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
          />
        </div>
        {view === 'products' && (
          <>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border-2 border-earth-200 hover:border-primary-500"
            >
              <Filter className="w-5 h-5" /> Filters
              <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
            </button>
            <div className="flex items-center gap-1 bg-earth-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-white shadow' : ''}`}
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-white shadow' : ''}`}
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </>
        )}
      </div>

      {showFilters && view === 'products' && (
        <div className="bg-white rounded-xl p-4 grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-bold text-earth-700 mb-1">Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
            >
              <option value="all">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-bold text-earth-700 mb-1">Product Type</label>
            <select
              value={productTypeFilter}
              onChange={(e) => setProductTypeFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
            >
              <option value="all">All Types</option>
              <option value="input">Inputs</option>
              <option value="machinery">Machinery</option>
            </select>
          </div>
        </div>
      )}

      {view === 'products' ? (
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          {filteredProducts.length === 0 ? (
            <div className="text-center py-12 text-earth-500">No products found</div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
              {filteredProducts.map(product => (
                <ProductCard key={product.id} product={product} onProductSelect={onProductSelect} />
              ))}
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-earth-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Product</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Supplier</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Stock</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-earth-200">
                {filteredProducts.map(product => (
                  <tr key={product.id} className="hover:bg-earth-50">
                    <td className="px-6 py-4 font-bold text-earth-800">{product.name}</td>
                    <td className="px-6 py-4 text-sm text-earth-600">{product.supplier_name || 'Unknown'}</td>
                    <td className="px-6 py-4 text-sm text-earth-600">{product.category}</td>
                    <td className="px-6 py-4 font-bold text-green-600">${product.price?.toFixed(2)}</td>
                    <td className="px-6 py-4 text-sm text-earth-600">{product.quantity_available || 0}</td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => onProductSelect?.(product.id)}
                        className="text-primary-600 hover:text-primary-700 font-medium text-sm"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSuppliers.map(supplier => (
            <SupplierCard key={supplier.id} supplier={supplier} />
          ))}
        </div>
      )}
    </div>
  );
}

function ProductCard({ product, onProductSelect }: ProductCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6">
      <h3 className="font-bold text-earth-800 mb-2 line-clamp-1">{product.name}</h3>
      <p className="text-green-600 font-bold mb-2">${product.price?.toFixed(2)}</p>
      <p className="text-xs text-earth-500 mb-3">{product.category}</p>
      <p className={`text-xs font-medium mb-3 ${product.quantity_available > 0 ? 'text-green-600' : 'text-red-600'}`}>
        {product.quantity_available > 0 ? `${product.quantity_available} in stock` : 'Out of stock'}
      </p>
      <button
        onClick={() => onProductSelect?.(product.id)}
        className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-xl transition-colors"
      >
        View Details
      </button>
    </div>
  );
}

function SupplierCard({ supplier }: SupplierCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-bold text-earth-800 mb-1">{supplier.business_name}</h3>
          <div className="flex items-center gap-1 text-sm text-earth-600">
            <MapPin className="w-4 h-4" /> {supplier.location || 'Zimbabwe'}
          </div>
        </div>
        {supplier.rating && (
          <div className="flex items-center gap-1 text-sm">
            <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
            <span className="font-medium">{supplier.rating.toFixed(1)}</span>
          </div>
        )}
      </div>
      <button className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-xl transition-colors">
        View Products
      </button>
    </div>
  );
}
