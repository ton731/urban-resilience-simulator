import React, { useState } from 'react';

const Card = ({ 
  children, 
  title, 
  className = '',
  padding = 'default',
  collapsible = false,
  defaultCollapsed = false,
  ...props 
}) => {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  
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

  const toggleCollapsed = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={finalClassName} {...props}>
      {title && (
        <div className="border-b border-gray-200 pb-3 mb-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">{title}</h3>
            {collapsible && (
              <button
                onClick={toggleCollapsed}
                className="text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600 transition-colors duration-200"
                aria-label={isCollapsed ? '展開' : '收合'}
              >
                <svg 
                  className={`w-5 h-5 transform transition-transform duration-200 ${isCollapsed ? 'rotate-0' : 'rotate-180'}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            )}
          </div>
        </div>
      )}
      {!isCollapsed && children}
    </div>
  );
};

export default Card;