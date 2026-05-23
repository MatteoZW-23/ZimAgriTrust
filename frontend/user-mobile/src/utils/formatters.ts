export function formatMoney(value, currency = 'USD') {
  const number = Number(value || 0);
  const prefix = currency === 'USD' ? '$' : `${currency} `;
  return `${prefix}${number.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

export function parseNumber(value) {
  if (value === '' || value === null || value === undefined) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function formatCropName(listing) {
  return listing.crop || listing.product_type || listing.product_subtype || 'Listing';
}

export function formatLocation(listing) {
  const parts = [listing.location_district, listing.location_province].filter(Boolean);
  return parts.length > 0 ? parts.join(', ') : listing.location || 'Location not provided';
}

export function formatGrade(value) {
  if (!value) return 'Ungraded';
  if (/^GRADE_[A-Z]$/i.test(value)) return `Grade ${String(value).split('_')[1].toUpperCase()}`;
  if (String(value).toUpperCase() === 'EXPORT') return 'Export';
  return String(value)
    .replace(/_/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase())
    .join(' ');
}
