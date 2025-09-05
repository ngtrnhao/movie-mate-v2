import React from 'react';

const Select = ({
  name,
  value,
  onChange,
  options = [],
  placeholder = 'Chọn...',
  className = '',
  disabled = false,
  required = false,
  error = null,
}) => {
  return (
    <div>
      <select
        name={name}
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        className={`
          mt-1 block w-full rounded border px-3 py-2 text-black
          focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
          ${error ? 'border-red-500' : 'border-gray-300'}
          ${className}
        `}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <div className="text-red-500 text-xs mt-1">{error}</div>}
    </div>
  );
};

export default Select;
