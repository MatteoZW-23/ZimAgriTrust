import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({ children, className = '', onClick }) => {
  return (
    <div
      onClick={onClick}
      className={`
        bg-white dark:bg-earth-800 border-2 border-earth-100 dark:border-earth-700 rounded-3xl p-6 shadow-sm shadow-earth-100/50 dark:shadow-none
        transition-all duration-300
        ${onClick ? 'cursor-pointer hover:border-primary-200 dark:hover:border-primary-600 hover:shadow-xl hover:shadow-primary-50 dark:hover:shadow-none active:scale-[0.98]' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
};
