export const ZIMBABWE_CROP_DATABASE = [
  { id: 'mz', name: 'Maize', category: 'Crops', grades: ['A', 'B', 'C'], basePrice: 0.45, unit: 'kg', description: 'Main staple crop in Zimbabwe.' },
  { id: 'tb', name: 'Tobacco', category: 'Crops', grades: ['Floor', 'Contract'], basePrice: 3.20, unit: 'kg', description: 'Gold leaf export variety.' },
  { id: 'sb', name: 'Soya Beans', category: 'Crops', grades: ['A', 'B'], basePrice: 0.60, unit: 'kg', description: 'Essential for oil and feed.' },
  { id: 'cn', name: 'Cotton', category: 'Crops', grades: ['A', 'B', 'C', 'D'], basePrice: 0.40, unit: 'kg', description: 'White gold industrial crop.' },
  { id: 'sg', name: 'Sorghum', category: 'Crops', grades: ['A', 'B'], basePrice: 0.35, unit: 'kg', description: 'Drought-tolerant cereal crop.' },
  { id: 'gn', name: 'Groundnuts', category: 'Crops', grades: ['A', 'B'], basePrice: 0.75, unit: 'kg', description: 'Protein-rich legume.' },
  { id: 'wh', name: 'Wheat', category: 'Crops', grades: ['A', 'B'], basePrice: 0.55, unit: 'kg', description: 'Winter-grown staple.' },
];

export const ZIMBABWE_LIVESTOCK_DATABASE = [
  { id: 'br', name: 'Brahman Cattle', category: 'Livestock', basePrice: 450, unit: 'head', description: 'Premium beef breed.' },
  { id: 'hr', name: 'Hereford Cattle', category: 'Livestock', basePrice: 500, unit: 'head', description: 'High-yield beef breed.' },
  { id: 'pg', name: 'Pig', category: 'Livestock', basePrice: 120, unit: 'head', description: 'Commercial pork production.' },
  { id: 'gt', name: 'Goat', category: 'Livestock', basePrice: 45, unit: 'head', description: 'Hardy livestock for dry regions.' },
  { id: 'ch', name: 'Broiler Chicken', category: 'Poultry', basePrice: 6, unit: 'bird', description: 'Standard poultry meat.' },
];

export const ZIMBABWE_AGRI_CATALOG = [
  // FIELD CROPS
  { id: 'staple-maize', name: 'Maize', category: 'Field Crops', subcategory: 'Staple', unit: 'Metric Tonne', description: 'Main staple crop in Zimbabwe.' },
  { id: 'staple-sorghum', name: 'Sorghum', category: 'Field Crops', subcategory: 'Staple', unit: 'Metric Tonne' },
  { id: 'staple-millet', name: 'Pearl Millet (Mhunga)', category: 'Field Crops', subcategory: 'Staple', unit: 'Metric Tonne' },
  { id: 'staple-rapoko', name: 'Finger Millet (Rapoko)', category: 'Field Crops', subcategory: 'Staple', unit: 'Metric Tonne' },
  { id: 'staple-wheat', name: 'Wheat', category: 'Field Crops', subcategory: 'Staple', unit: 'Metric Tonne' },
  { id: 'staple-barley', name: 'Barley', category: 'Field Crops', subcategory: 'Cereal', unit: 'Metric Tonne' },
  { id: 'staple-rice', name: 'Rice', category: 'Field Crops', subcategory: 'Staple', unit: 'Metric Tonne' },

  // CASH CROPS
  { id: 'cash-tobacco', name: 'Tobacco (Gold Leaf)', category: 'Cash Crops', subcategory: 'Export', unit: 'Kilogram', description: 'Zimbabwes top export earner.' },
  { id: 'cash-cotton', name: 'Cotton (White Gold)', category: 'Cash Crops', subcategory: 'Industrial', unit: 'Kilogram' },
  { id: 'cash-sugarcane', name: 'Sugarcane', category: 'Cash Crops', subcategory: 'Industrial', unit: 'Tonne' },
  { id: 'cash-soyabeans', name: 'Soya Beans', category: 'Cash Crops', subcategory: 'Industrial', unit: 'Metric Tonne' },
  { id: 'cash-sunflower', name: 'Sunflower Seeds', category: 'Cash Crops', subcategory: 'Industrial', unit: 'Kilogram' },
  { id: 'cash-paprika', name: 'Paprika', category: 'Cash Crops', subcategory: 'Export', unit: 'Kilogram' },

  // LEGUMES
  { id: 'legume-groundnuts', name: 'Groundnuts (Peanuts)', category: 'Legumes', subcategory: 'Protein', unit: 'Crate/Bag' },
  { id: 'legume-sugarbeans', name: 'Sugar Beans', category: 'Legumes', subcategory: 'Protein', unit: 'Kilogram' },
  { id: 'legume-cowpeas', name: 'Cowpeas', category: 'Legumes', subcategory: 'Protein', unit: 'Kilogram' },
  { id: 'legume-nyimo', name: 'Bambara Nuts (Nyimo)', category: 'Legumes', subcategory: 'Staple', unit: 'Kilogram' },

  // HORTICULTURE
  { id: 'hort-tomatoes', name: 'Tomatoes', category: 'Horticulture', subcategory: 'Vegetables', unit: 'Crate' },
  { id: 'hort-onions', name: 'Onions', category: 'Horticulture', subcategory: 'Vegetables', unit: '10kg Bag' },
  { id: 'hort-cabbage', name: 'Cabbage', category: 'Horticulture', subcategory: 'Vegetables', unit: 'Head' },
  { id: 'hort-potatoes', name: 'Potatoes', category: 'Horticulture', subcategory: 'Vegetables', unit: '15kg Bag' },
  { id: 'hort-carrots', name: 'Carrots', category: 'Horticulture', subcategory: 'Vegetables', unit: 'Bundle' },
  { id: 'hort-greenbeans', name: 'Green Beans', category: 'Horticulture', subcategory: 'Vegetables', unit: 'Kilogram' },
  { id: 'hort-peas', name: 'Peas', category: 'Horticulture', subcategory: 'Vegetables', unit: 'Kilogram' },
  { id: 'hort-cucumbers', name: 'Cucumbers', category: 'Horticulture', subcategory: 'Vegetables', unit: 'Unit' },
  { id: 'hort-peppers', name: 'Sweet Peppers', category: 'Horticulture', subcategory: 'Vegetables', unit: 'Kilogram' },
  { id: 'hort-okra', name: 'Okra', category: 'Horticulture', subcategory: 'Vegetables', unit: 'Kilogram' },

  // FRUITS
  { id: 'fruit-bananas', name: 'Bananas', category: 'Fruits', subcategory: 'Local', unit: 'Crate' },
  { id: 'fruit-oranges', name: 'Oranges', category: 'Fruits', subcategory: 'Citrus', unit: 'Packet' },
  { id: 'fruit-apples', name: 'Apples', category: 'Fruits', subcategory: 'Local', unit: 'Kilogram' },
  { id: 'fruit-mangoes', name: 'Mangoes', category: 'Fruits', subcategory: 'Seasonal', unit: 'Unit' },
  { id: 'fruit-avocados', name: 'Avocados', category: 'Fruits', subcategory: 'Export', unit: 'Kilogram' },
  { id: 'fruit-blueberries', name: 'Blueberries', category: 'Fruits', subcategory: 'Export', unit: 'Punnet' },
  { id: 'fruit-macadamia', name: 'Macadamia Nuts', category: 'Fruits', subcategory: 'Export', unit: 'Kilogram' },
  { id: 'fruit-watermelon', name: 'Watermelon', category: 'Fruits', subcategory: 'Seasonal', unit: 'Unit' },

  // LIVESTOCK
  { id: 'live-cattle-beef', name: 'Cattle (Beef)', category: 'Livestock', subcategory: 'Animals', unit: 'Head' },
  { id: 'live-cattle-dairy', name: 'Cattle (Dairy)', category: 'Livestock', subcategory: 'Animals', unit: 'Head' },
  { id: 'live-goats', name: 'Goats', category: 'Livestock', subcategory: 'Animals', unit: 'Head' },
  { id: 'live-sheep', name: 'Sheep', category: 'Livestock', subcategory: 'Animals', unit: 'Head' },
  { id: 'live-pigs', name: 'Pigs', category: 'Livestock', subcategory: 'Animals', unit: 'Head' },
  { id: 'live-chickens-broiler', name: 'Broiler Chickens', category: 'Poultry', subcategory: 'Meat', unit: 'Bird' },
  { id: 'live-chickens-layer', name: 'Layer Chickens', category: 'Poultry', subcategory: 'Eggs', unit: 'Bird' },
  { id: 'live-eggs', name: 'Table Eggs', category: 'Poultry', subcategory: 'Eggs', unit: 'Crate (30)' },

  // AQUACULTURE & OTHERS
  { id: 'aqua-tilapia', name: 'Tilapia (Fish)', category: 'Aquaculture', subcategory: 'Fish', unit: 'Kilogram' },
  { id: 'other-honey', name: 'Honey', category: 'Specialty', subcategory: 'Apiculture', unit: '500g Bottle' }
];

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

export const isValidZimbabweProduct = (name) => {
  const all = [
    ...ZIMBABWE_CROP_DATABASE, 
    ...ZIMBABWE_LIVESTOCK_DATABASE,
    ...ZIMBABWE_AGRI_CATALOG
  ];
  return all.some(p => p.name.toLowerCase() === name.toLowerCase());
};

export const getProductDetails = (name) => {
  const all = [
    ...ZIMBABWE_CROP_DATABASE, 
    ...ZIMBABWE_LIVESTOCK_DATABASE,
    ...ZIMBABWE_AGRI_CATALOG
  ];
  return all.find(p => p.name.toLowerCase() === name.toLowerCase());
};
