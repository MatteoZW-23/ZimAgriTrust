import React from 'react';

export const Button = ({ children, variant = 'primary', size = 'md', fullWidth = false, loading = false, className = '', disabled, ...props }) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-xl font-bold transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100';
  
  const variants = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 shadow-lg shadow-primary-200',
    secondary: 'bg-secondary-500 text-white hover:bg-secondary-600 shadow-lg shadow-secondary-200',
    outline: 'border-2 border-earth-200 text-earth-700 hover:bg-earth-50',
    danger: 'bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-200',
    ghost: 'text-earth-600 hover:bg-earth-100',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-6 py-3 text-sm',
    lg: 'px-8 py-4 text-base',
  };

  const widthStyle = fullWidth ? 'w-full' : '';

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${widthStyle} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="mr-2 animate-spin">⏳</span>}
      {children}
    </button>
  );
};
