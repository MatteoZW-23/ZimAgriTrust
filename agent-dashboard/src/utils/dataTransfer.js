/**
 * Institutional Data Transfer Utility for AgriTrust National Network
 * Handles high-fidelity export to CSV/JSON and secure data ingestion (Import).
 */

export const exportToCSV = (data, filename = 'agritrust_export.csv') => {
  if (!data || !data.length) return;

  const headers = Object.keys(data[0]);
  const csvRows = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const val = row[header];
        // Handle cases where value contains commas or quotes
        const escaped = ('' + (val ?? '')).replace(/"/g, '""');
        return `"${escaped}"`;
      }).join(',')
    )
  ];

  const csvContent = "data:text/csv;charset=utf-8," + csvRows.join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const exportToJSON = (data, filename = 'agritrust_export.json') => {
  const jsonContent = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
  const link = document.createElement("a");
  link.setAttribute("href", jsonContent);
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const handleImport = (file, callback) => {
  const reader = new FileReader();
  reader.onload = (e) => {
    const content = e.target.result;
    const extension = file.name.split('.').pop().toLowerCase();
    
    if (extension === 'json') {
      try {
        const data = JSON.parse(content);
        callback(data);
      } catch (err) {
        alert("CRITICAL_ERROR: Failed to parse JSON manifest.");
      }
    } else if (extension === 'csv') {
      const rows = content.split('\n').filter(r => r.trim());
      const headers = rows[0].split(',').map(h => h.replace(/^"|"$/g, ''));
      const data = rows.slice(1).map(row => {
        const values = row.split(',').map(v => v.replace(/^"|"$/g, ''));
        return headers.reduce((acc, header, i) => {
          acc[header] = values[i];
          return acc;
        }, {});
      });
      callback(data);
    } else {
      alert("UNSUPPORTED_FORMAT: System only accepts .csv or .json protocols.");
    }
  };
  reader.readAsText(file);
};
