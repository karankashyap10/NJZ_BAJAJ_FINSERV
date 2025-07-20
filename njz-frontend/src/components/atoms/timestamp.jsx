const Timestamp = ({ date, className = "" }) => {
  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <span className={`text-xs text-gray-500 dark:text-gray-400 ${className}`}>
      {formatTime(date)}
    </span>
  );
};

export default Timestamp;
