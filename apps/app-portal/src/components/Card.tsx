import React from 'react';

export const Card = ({ children, className = '', ...props }) => {
  return (
    <div
      className={`bg-white rounded-3xl shadow-xl ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
