// Product catalog — populated from backend API at runtime.
// No hardcoded data. Fetch from /api/v1/products or equivalent endpoint.

export const ZIMBABWE_CROP_DATABASE = [];
export const ZIMBABWE_LIVESTOCK_DATABASE = [];
export const ZIMBABWE_AGRI_CATALOG = [];

export const CATEGORY_METRICS = {
  'Field Crops': { icon: 'fa-wheat-awn', color: '#f59e0b' },
  'Cash Crops': { icon: 'fa-coins', color: '#10b981' },
  'Legumes': { icon: 'fa-seedling', color: '#3b82f6' },
  'Horticulture': { icon: 'fa-leaf', color: '#14b8a6' },
  'Fruits': { icon: 'fa-apple-whole', color: '#ef4444' },
  'Livestock': { icon: 'fa-cow', color: '#8b5cf6' },
  'Poultry': { icon: 'fa-feather', color: '#f43f5e' },
  'Aquaculture': { icon: 'fa-fish', color: '#0ea5e9' },
  'Specialty': { icon: 'fa-jar', color: '#d946ef' },
  'Crops': { icon: 'fa-wheat-awn', color: '#f59e0b' }
};

export const isValidZimbabweProduct = (name, catalog = []) => {
  return catalog.some(p => p.name.toLowerCase() === name.toLowerCase());
};

export const getProductDetails = (name, catalog = []) => {
  return catalog.find(p => p.name.toLowerCase() === name.toLowerCase());
};
