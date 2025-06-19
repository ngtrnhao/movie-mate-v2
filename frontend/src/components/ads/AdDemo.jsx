import { useState } from 'react';
import AdBannerTop from './AdBannerTop';
import AdBannerSidebar from './AdBannerSidebar';
import AdBannerFooter from './AdBannerFooter';
import AdContent from './AdContent';
import usePropellerAds from '../../hooks/usePropellerAds';

const AdDemo = () => {
  const [activeTab, setActiveTab] = useState('banner');
  const { showPopup, showInterstitial, getStats } = usePropellerAds('DEMO');

  const tabs = [
    { id: 'banner', label: 'Banner Ads' },
    { id: 'content', label: 'Content Ads' },
    { id: 'popup', label: 'Popup/Interstitial' },
    { id: 'stats', label: 'Statistics' },
  ];

  const handleShowPopup = () => {
    showPopup();
  };

  const handleShowInterstitial = () => {
    showInterstitial();
  };

  const handleGetStats = () => {
    const stats = getStats();
    console.log('Ad Statistics:', stats);
    alert('Check console for ad statistics');
  };

  return (
    <div className="ad-demo-container min-h-screen bg-gray-900 p-8">
      <div className="mx-auto max-w-6xl">
        <h1 className="mb-8 text-3xl font-bold text-white">PropellerAds Demo</h1>

        {/* Tab Navigation */}
        <div className="mb-8 flex space-x-4">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-lg px-4 py-2 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="rounded-lg bg-gray-800 p-6">
          {activeTab === 'banner' && (
            <div className="space-y-8">
              <h2 className="mb-4 text-2xl font-bold text-white">Banner Ads</h2>

              <div>
                <h3 className="mb-2 text-lg font-semibold text-white">Top Banner</h3>
                <AdBannerTop />
              </div>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                <div>
                  <h3 className="mb-2 text-lg font-semibold text-white">Sidebar Banner</h3>
                  <AdBannerSidebar />
                </div>
                <div className="lg:col-span-2">
                  <h3 className="mb-2 text-lg font-semibold text-white">Content Area</h3>
                  <div className="bg-gray-700 p-4 rounded">
                    <p className="text-gray-300 mb-4">
                      This is a sample content area. The sidebar banner should appear on the left.
                    </p>
                    <p className="text-gray-300">
                      Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
                      incididunt ut labore et dolore magna aliqua.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Footer Banner</h3>
                <AdBannerFooter />
              </div>
            </div>
          )}

          {activeTab === 'content' && (
            <div className="space-y-8">
              <h2 className="text-2xl font-bold text-white mb-4">Content Ads</h2>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Top Content Ad</h3>
                <AdContent position="TOP" />
              </div>

              <div className="bg-gray-700 p-6 rounded">
                <h3 className="text-lg font-semibold text-white mb-4">Sample Content</h3>
                <p className="text-gray-300 mb-4">
                  This is sample content to demonstrate how content ads work. They appear naturally
                  within the content flow.
                </p>
                <p className="text-gray-300">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
                  incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
                  exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Middle Content Ad</h3>
                <AdContent position="MIDDLE" />
              </div>

              <div className="bg-gray-700 p-6 rounded">
                <h3 className="text-lg font-semibold text-white mb-4">More Content</h3>
                <p className="text-gray-300">
                  Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
                  fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Bottom Content Ad</h3>
                <AdContent position="BOTTOM" />
              </div>
            </div>
          )}

          {activeTab === 'popup' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-white mb-4">Popup & Interstitial Ads</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-700 p-6 rounded">
                  <h3 className="text-lg font-semibold text-white mb-4">Popup Ad</h3>
                  <p className="text-gray-300 mb-4">
                    Click the button below to trigger a popup ad. Popup ads typically appear after a
                    delay or user interaction.
                  </p>
                  <button
                    onClick={handleShowPopup}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded font-medium transition-colors"
                  >
                    Show Popup Ad
                  </button>
                </div>

                <div className="bg-gray-700 p-6 rounded">
                  <h3 className="text-lg font-semibold text-white mb-4">Interstitial Ad</h3>
                  <p className="text-gray-300 mb-4">
                    Click the button below to trigger an interstitial ad. Interstitial ads typically
                    appear between page transitions.
                  </p>
                  <button
                    onClick={handleShowInterstitial}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded font-medium transition-colors"
                  >
                    Show Interstitial Ad
                  </button>
                </div>
              </div>

              <div className="bg-yellow-900/20 border border-yellow-600/30 p-4 rounded">
                <h4 className="text-yellow-400 font-semibold mb-2">Note:</h4>
                <p className="text-yellow-200 text-sm">
                  Popup and interstitial ads may be blocked by browser popup blockers. Make sure to
                  allow popups for this site if ads don't appear.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-white mb-4">Ad Statistics</h2>

              <div className="bg-gray-700 p-6 rounded">
                <h3 className="text-lg font-semibold text-white mb-4">Performance Metrics</h3>
                <p className="text-gray-300 mb-4">
                  Click the button below to view ad statistics in the browser console. This includes
                  load events, clicks, and errors.
                </p>
                <button
                  onClick={handleGetStats}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium transition-colors"
                >
                  View Statistics
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-700 p-4 rounded">
                  <h4 className="text-white font-semibold mb-2">Zone Types</h4>
                  <ul className="text-gray-300 text-sm space-y-1">
                    <li>• BANNER_TOP</li>
                    <li>• BANNER_SIDEBAR</li>
                    <li>• BANNER_FOOTER</li>
                    <li>• CONTENT_TOP</li>
                    <li>• CONTENT_MIDDLE</li>
                    <li>• CONTENT_BOTTOM</li>
                    <li>• POPUP</li>
                    <li>• INTERSTITIAL</li>
                  </ul>
                </div>

                <div className="bg-gray-700 p-4 rounded">
                  <h4 className="text-white font-semibold mb-2">Event Types</h4>
                  <ul className="text-gray-300 text-sm space-y-1">
                    <li>• load</li>
                    <li>• click</li>
                    <li>• error</li>
                    <li>• show (popup/interstitial)</li>
                  </ul>
                </div>

                <div className="bg-gray-700 p-4 rounded">
                  <h4 className="text-white font-semibold mb-2">Features</h4>
                  <ul className="text-gray-300 text-sm space-y-1">
                    <li>• Responsive design</li>
                    <li>• Analytics tracking</li>
                    <li>• Performance optimized</li>
                    <li>• Development placeholders</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdDemo;
