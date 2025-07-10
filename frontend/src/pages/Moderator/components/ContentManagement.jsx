import { useState } from 'react';
import {
  EyeIcon,
  FunnelIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  DocumentIcon,
  PhotoIcon,
  DocumentArrowDownIcon,
} from '@heroicons/react/24/outline';

const ContentManagement = () => {
  const [activeTab, setActiveTab] = useState('reviews');
  const [selectedItems, setSelectedItems] = useState([]);

  const tabs = [
    { id: 'reviews', label: 'Reviews', icon: DocumentTextIcon, count: 15 },
    { id: 'comments', label: 'Comments', icon: ChatBubbleLeftRightIcon, count: 8 },
    { id: 'posts', label: 'Posts', icon: DocumentIcon, count: 3 },
    { id: 'media', label: 'Media', icon: PhotoIcon, count: 2 },
  ];

  const contentItems = [
    {
      id: 1,
      type: 'review',
      title: 'Review: Avengers: Endgame',
      content: 'Một bộ phim tuyệt vời với cốt truyện hoàn hảo...',
      author: 'user123',
      status: 'pending',
      priority: 'high',
      createdAt: '2 giờ trước',
      rating: 5,
    },
    {
      id: 2,
      type: 'comment',
      title: 'Comment on Inception',
      content: 'Phim này thật sự rất hay và đáng xem...',
      author: 'user456',
      status: 'flagged',
      priority: 'medium',
      createdAt: '1 giờ trước',
    },
    {
      id: 3,
      type: 'post',
      title: 'Top 10 phim hay nhất 2024',
      content: 'Danh sách những bộ phim đáng xem nhất...',
      author: 'user789',
      status: 'pending',
      priority: 'low',
      createdAt: '30 phút trước',
    },
  ];

  const getStatusColor = status => {
    switch (status) {
      case 'pending':
        return 'bg-pink-100 text-pink-700';
      case 'reviewing':
        return 'bg-amber-100 text-amber-700';
      case 'approved':
        return 'bg-purple-100 text-purple-700';
      case 'rejected':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getPriorityColor = priority => {
    switch (priority) {
      case 'high':
        return 'bg-pink-100 text-pink-700';
      case 'medium':
        return 'bg-amber-100 text-amber-700';
      case 'low':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getTypeColor = type => {
    switch (type) {
      case 'review':
        return 'bg-pink-100 text-pink-700';
      case 'comment':
        return 'bg-amber-100 text-amber-700';
      case 'rating':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const handleSelectItem = itemId => {
    setSelectedItems(prev =>
      prev.includes(itemId) ? prev.filter(id => id !== itemId) : [...prev, itemId]
    );
  };

  const handleSelectAll = () => {
    setSelectedItems(contentItems.map(item => item.id));
  };

  const handleClearSelection = () => {
    setSelectedItems([]);
  };

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map(tab => {
            const TabIcon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center border-b-2 px-1 py-2 text-sm font-medium ${
                  activeTab === tab.id
                    ? 'border-pink-500 text-pink-700'
                    : 'border-transparent text-purple-400 hover:border-pink-700 hover:text-pink-700'
                }`}
              >
                <TabIcon className="mr-2 size-4" />
                {tab.label}
                <span className="ml-2 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-900">
                  {tab.count}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Filters and Actions */}
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <FunnelIcon className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-gray-400" />
          <select className="rounded-md border border-gray-300 py-2 pl-10 pr-3 text-sm">
            <option>Tất cả trạng thái</option>
            <option>Chờ duyệt</option>
            <option>Đang xem xét</option>
            <option>Đã duyệt</option>
            <option>Đã từ chối</option>
          </select>
        </div>
        <div className="relative flex-1">
          <FunnelIcon className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-gray-400" />
          <select className="rounded-md border border-gray-300 py-2 pl-10 pr-3 text-sm">
            <option>Tất cả loại</option>
            <option>Review</option>
            <option>Comment</option>
            <option>Rating</option>
          </select>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center rounded-md bg-gradient-to-r from-amber-400 to-pink-400 px-4 py-2 text-sm text-white hover:from-amber-500 hover:to-pink-500">
            <DocumentArrowDownIcon className="mr-2 size-4" />
            Xuất
          </button>
          <button className="flex items-center rounded-md bg-gradient-to-r from-pink-400 to-purple-400 px-4 py-2 text-sm text-white hover:from-pink-500 hover:to-purple-500">
            <ChatBubbleLeftRightIcon className="mr-2 size-4" />
            Bulk Action
          </button>
          <button
            onClick={handleSelectAll}
            className="rounded-md bg-gray-400 px-4 py-2 text-sm text-white hover:bg-gray-500"
          >
            Chọn tất cả
          </button>
        </div>
      </div>

      {/* Content List */}
      <div className="rounded-lg bg-white shadow">
        <div className="border-b border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-purple-900">
              {tabs.find(tab => tab.id === activeTab)?.label}
            </h3>
            <button onClick={handleSelectAll} className="text-sm text-pink-600 hover:text-pink-700">
              Chọn tất cả
            </button>
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {contentItems.map(item => (
            <div key={item.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-start space-x-4">
                <input
                  type="checkbox"
                  checked={selectedItems.includes(item.id)}
                  onChange={() => handleSelectItem(item.id)}
                  className="mt-1 size-4 rounded border-gray-300 text-pink-600 focus:ring-pink-500"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="truncate text-sm font-medium text-purple-900">{item.title}</h4>
                    <span
                      className={`rounded-full px-2 py-1 text-xs ${getStatusColor(item.status)}`}
                    >
                      {item.status}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center space-x-2">
                    <span
                      className={`rounded-full px-2 py-1 text-xs ${getPriorityColor(
                        item.priority
                      )}`}
                    >
                      {item.priority}
                    </span>
                    <span className={`rounded-full px-2 py-1 text-xs ${getTypeColor(item.type)}`}>
                      {item.type}
                    </span>
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-gray-700">{item.content}</p>
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span>Bởi {item.author}</span>
                    <span>{item.createdAt}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="flex items-center text-xs font-medium text-pink-600 hover:text-pink-700">
                    <EyeIcon className="mr-1 size-4" />
                    Xem
                  </button>
                  <button className="flex items-center text-xs font-medium text-purple-600 hover:text-purple-700">
                    <ChatBubbleLeftRightIcon className="mr-1 size-4" />
                    Phản hồi
                  </button>
                  <button className="flex items-center text-xs font-medium text-gray-600 hover:text-gray-700">
                    <DocumentArrowDownIcon className="mr-1 size-4" />
                    Chi tiết
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Pagination */}
        <div className="border-t border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Hiển thị 1-10 của {contentItems.length} kết quả
            </div>
            <div className="flex items-center space-x-2">
              <button className="flex items-center rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50">
                Trước
              </button>
              <button className="rounded-md bg-pink-600 px-3 py-2 text-sm text-white">1</button>
              <button className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50">
                2
              </button>
              <button className="flex items-center rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50">
                Sau
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContentManagement;
