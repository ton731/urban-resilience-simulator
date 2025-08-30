import React from 'react';

const Card = ({ 
  children, 
  title, 
  className = '',
  padding = 'default',
  ...props 
}) => {
  const baseStyles = 'bg-white rounded-lg shadow-md border border-gray-200';
  
  const paddings = {
    none: '',
    small: 'p-3',
    default: 'p-4',
    large: 'p-6'
  };
  
  const finalClassName = [
    baseStyles,
    paddings[padding],
    className
  ].join(' ');

  return (
    <div className={finalClassName} {...props}>
      {title && (
        <div className="border-b border-gray-200 pb-3 mb-4">
          <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        </div>
      )}
      {children}
    </div>
  );
};

export default Card;