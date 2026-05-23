import React from 'react';

export const Input = ({ label, icon, error, className = '', ...props }) => {
  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label className="block text-xs font-black text-earth-400 uppercase tracking-wider mb-1.5">
          {label}
        </label>
      )}
      <div className="relative group">
        {icon && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-earth-400 group-focus-within:text-primary-500 transition-colors">
            {icon}
          </div>
        )}
        <input
          className={`
            w-full px-4 py-3 rounded-xl border-2 border-earth-100
            text-earth-800 placeholder:text-earth-300
            focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20
            transition-all
            ${icon ? 'pl-12' : ''}
            ${error ? 'border-red-300 focus:border-red-500 focus:ring-red-500/20' : ''}
          `}
          {...props}
        />
      </div>
      {error && <p className="mt-1.5 text-xs font-bold text-red-500">{error}</p>}
    </div>
  );
};
