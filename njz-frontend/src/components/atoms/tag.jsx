import { X } from "lucide-react";
import Icon from "./icons";

const Tag = ({ children, onRemove, className = "" }) => {
  return (
    <div
      className={`relative inline-flex items-center px-3 py-1 rounded-xl bg-gray-900 text-gray-800 text-sm border border-cyan-300 dark:bg-[#2e2e2e] dark:text-gray-200 w-full max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg ${className}`}
    >
      <span className="truncate overflow-hidden whitespace-nowrap pr-6">
        {children}
      </span>
      {onRemove && (
        <button
          onClick={onRemove}
          className="absolute right-1 hover:bg-gray-700 dark:hover:bg-gray-600 rounded-full p-0.5"
        >
          <Icon icon={X} size="sm" />
        </button>
      )}
    </div>
  );
};

export default Tag;
