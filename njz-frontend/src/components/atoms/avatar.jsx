const Avatar = ({ name = "User", type = "user", size = "md" }) => {
  const sizes = {
    sm: "w-6 h-6 text-xs",
    md: "w-8 h-8 text-sm",
    lg: "w-10 h-10 text-base",
  };

  const colors = {
    user: "bg-blue-500 text-white",
    ai: "bg-green-500 text-white",
  };

  return (
    <div
      className={`${sizes[size]} ${colors[type]} rounded-full flex items-center justify-center font-medium`}
    >
      {name.charAt(0).toUpperCase()}
    </div>
  );
};

export default Avatar;
