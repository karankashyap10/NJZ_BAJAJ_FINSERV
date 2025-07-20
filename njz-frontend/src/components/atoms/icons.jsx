const Icon = ({ icon: IconComponent, size = "md", className = "" }) => {
  const sizes = {
    sm: "w-4 h-4",
    md: "w-5 h-5",
    lg: "w-6 h-6",
  };

  return <IconComponent className={`${sizes[size]} ${className}`} />;
};

export default Icon;
