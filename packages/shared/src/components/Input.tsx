import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  icon,
  className = '',
  ...props
}) => {
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
            w-full bg-white dark:bg-earth-700 border-2 border-earth-100 dark:border-earth-600 rounded-xl px-4 py-3 text-sm font-bold text-earth-800 dark:text-white
            placeholder:text-earth-300 dark:placeholder:text-earth-500 outline-none transition-all
            focus:border-primary-500 focus:shadow-lg focus:shadow-primary-100 dark:focus:shadow-none
            ${icon ? 'pl-12' : ''}
            ${error ? 'border-red-400 focus:border-red-500 focus:shadow-red-100' : ''}
          `}
          {...props}
        />
      </div>
      {error && <p className="mt-1.5 text-xs font-bold text-red-500">{error}</p>}
    </div>
  );
};
