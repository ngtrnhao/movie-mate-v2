const TabGroup = ({ tabs, activeTab, onTabChange }) => {
  return (
    <div className="mb-8 flex justify-center gap-2" role="tablist">
      {tabs.map(tab => (
        <button
          key={tab.key}
          role="tab"
          aria-selected={activeTab === tab.key}
          tabIndex={activeTab === tab.key ? 0 : -1}
          onClick={() => onTabChange(tab.key)}
          className={`rounded px-2 py-1 font-sans transition-colors
            ${
              activeTab === tab.key
                ? 'bg-red-600 font-semibold text-white shadow'
                : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};
export default TabGroup;
