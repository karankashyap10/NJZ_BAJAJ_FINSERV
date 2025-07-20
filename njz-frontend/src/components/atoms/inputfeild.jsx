const InputField = ({
  type = "text",
  placeholder = "",
  value,
  onChange,
  className = "",
  multiline = false,
  rows = 3,
  ...props
}) => {
  const baseClasses =
    "w-full px-3 py-2 border border-[#23232b] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6366f1] focus:border-[#6366f1] bg-[#23232b] text-[#e5e7eb] placeholder:text-[#a1a1aa]";

  if (multiline) {
    return (
      <textarea
        className={`${baseClasses} resize-none ${className}`}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        rows={rows}
        {...props}
      />
    );
  }

  return (
    <input
      type={type}
      className={`${baseClasses} ${className}`}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      {...props}
    />
  );
};
export default InputField;
