import useUserTracking from '../../../hooks/useUserTracking';

const TabGroup = ({ tabs, activeTab, onTabChange }) => {
  const { trackInteraction } = useUserTracking();

  const handleTabClick = tabKey => {
    trackInteraction({
      action: 'tab_switch',
      metadata: {
        from_tab: activeTab,
        to_tab: tabKey,
        tab_label: tabs.find(tab => tab.key === tabKey)?.label || tabKey,
        context: 'tab_group',
        timestamp: new Date().toISOString(),
      },
    });
    onTabChange(tabKey);
  };

  return (
    <div className="mb-8 flex justify-center gap-2" role="tablist">
      {tabs.map(tab => (
        <button
          key={tab.key}
          role="tab"
          aria-selected={activeTab === tab.key}
          tabIndex={activeTab === tab.key ? 0 : -1}
          onClick={() => handleTabClick(tab.key)}
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
