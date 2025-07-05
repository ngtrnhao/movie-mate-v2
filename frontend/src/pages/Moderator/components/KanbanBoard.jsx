import React, { useState, useEffect } from 'react';

const KanbanBoard = ({ selectedItems, onSelectItem, onBulkAction, isAdmin }) => {
  const [columns, setColumns] = useState({
    backlog: { id: 'backlog', title: 'Hàng đợi', items: [] },
    inProgress: { id: 'inProgress', title: 'Đang xử lý', items: [] },
    review: { id: 'review', title: 'Đang xem xét', items: [] },
    completed: { id: 'completed', title: 'Hoàn thành', items: [] },
  });

  const [draggedItem, setDraggedItem] = useState(null);
  const [draggedFrom, setDraggedFrom] = useState(null);
  const [loading, setLoading] = useState(true);

  // Mock data - replace with actual API calls
  useEffect(() => {
    const mockData = {
      backlog: {
        id: 'backlog',
        title: 'Hàng đợi',
        items: [
          {
            id: 'item-1',
            title: 'Review phim "The Matrix"',
            content: 'Đánh giá phim có nội dung không phù hợp',
            type: 'review',
            priority: 'high',
            assignee: 'Unassigned',
            createdAt: '2024-01-15T10:00:00Z',
            reporter: 'user123',
          },
          {
            id: 'item-2',
            title: 'Báo cáo spam comment',
            content: 'Người dùng spam nhiều comment không liên quan',
            type: 'report',
            priority: 'medium',
            assignee: 'Unassigned',
            createdAt: '2024-01-15T09:30:00Z',
            reporter: 'user456',
          },
          {
            id: 'item-3',
            title: 'Poster phim không phù hợp',
            content: 'Poster phim có nội dung bạo lực',
            type: 'content',
            priority: 'low',
            assignee: 'Unassigned',
            createdAt: '2024-01-15T08:45:00Z',
            reporter: 'system',
          },
        ],
      },
      inProgress: {
        id: 'inProgress',
        title: 'Đang xử lý',
        items: [
          {
            id: 'item-4',
            title: 'Xem xét tài khoản nghi vấn',
            content: 'Tài khoản có hành vi bất thường',
            type: 'user',
            priority: 'high',
            assignee: 'Moderator A',
            createdAt: '2024-01-15T07:20:00Z',
            reporter: 'system',
          },
          {
            id: 'item-5',
            title: 'Review nội dung đánh giá',
            content: 'Đánh giá có từ ngữ không phù hợp',
            type: 'review',
            priority: 'medium',
            assignee: 'Moderator B',
            createdAt: '2024-01-15T06:15:00Z',
            reporter: 'user789',
          },
        ],
      },
      review: {
        id: 'review',
        title: 'Đang xem xét',
        items: [
          {
            id: 'item-6',
            title: 'Phê duyệt thay đổi thông tin phim',
            content: 'Yêu cầu cập nhật thông tin phim',
            type: 'content',
            priority: 'low',
            assignee: 'Admin',
            createdAt: '2024-01-15T05:30:00Z',
            reporter: 'user321',
          },
        ],
      },
      completed: {
        id: 'completed',
        title: 'Hoàn thành',
        items: [
          {
            id: 'item-7',
            title: 'Xử lý báo cáo spam',
            content: 'Đã xử lý và cảnh báo người dùng',
            type: 'report',
            priority: 'high',
            assignee: 'Moderator C',
            createdAt: '2024-01-15T04:00:00Z',
            reporter: 'user654',
            resolvedAt: '2024-01-15T10:30:00Z',
          },
        ],
      },
    };

    setTimeout(() => {
      setColumns(mockData);
      setLoading(false);
    }, 1000);
  }, []);

  const getItemTypeColor = type => {
    switch (type) {
      case 'review':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'report':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'content':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'user':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityColor = priority => {
    switch (priority) {
      case 'high':
        return 'bg-red-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getTypeIcon = type => {
    switch (type) {
      case 'review':
        return '📝';
      case 'report':
        return '🚨';
      case 'content':
        return '🎬';
      case 'user':
        return '👤';
      default:
        return '📋';
    }
  };

  const handleDragStart = (e, item, columnId) => {
    setDraggedItem(item);
    setDraggedFrom(columnId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = e => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, targetColumnId) => {
    e.preventDefault();

    if (!draggedItem || !draggedFrom || draggedFrom === targetColumnId) {
      return;
    }

    // Update columns state
    setColumns(prev => {
      const newColumns = { ...prev };

      // Remove item from source column
      newColumns[draggedFrom].items = newColumns[draggedFrom].items.filter(
        item => item.id !== draggedItem.id
      );

      // Add item to target column
      newColumns[targetColumnId].items.push(draggedItem);

      return newColumns;
    });

    // Reset drag state
    setDraggedItem(null);
    setDraggedFrom(null);
  };

  const handleDragEnd = () => {
    setDraggedItem(null);
    setDraggedFrom(null);
  };

  const formatDate = dateString => {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Kanban Board</h2>
        <p className="text-gray-600">Quản lý workflow kiểm duyệt bằng drag-and-drop</p>
      </div>

      {/* Kanban Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 h-full">
        {Object.values(columns).map(column => (
          <div
            key={column.id}
            className="bg-gray-50 rounded-lg p-4 flex flex-col"
            onDragOver={handleDragOver}
            onDrop={e => handleDrop(e, column.id)}
          >
            {/* Column Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <h3 className="font-semibold text-gray-900">{column.title}</h3>
                <span className="ml-2 bg-gray-200 text-gray-700 text-sm px-2 py-1 rounded-full">
                  {column.items.length}
                </span>
              </div>
              <button className="text-gray-500 hover:text-gray-700">
                <span className="text-lg">⋮</span>
              </button>
            </div>

            {/* Column Items */}
            <div className="flex-1 space-y-3 overflow-y-auto">
              {column.items.map(item => (
                <div
                  key={item.id}
                  draggable
                  onDragStart={e => handleDragStart(e, item, column.id)}
                  onDragEnd={handleDragEnd}
                  className={`bg-white rounded-lg p-4 shadow-sm border cursor-move hover:shadow-md transition-shadow ${
                    selectedItems.includes(item.id) ? 'ring-2 ring-indigo-500' : ''
                  }`}
                  onClick={() => onSelectItem(item.id)}
                >
                  {/* Item Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center">
                      <span className="text-lg mr-2">{getTypeIcon(item.type)}</span>
                      <div
                        className={`w-2 h-2 rounded-full ${getPriorityColor(item.priority)}`}
                      ></div>
                    </div>
                    <input
                      type="checkbox"
                      checked={selectedItems.includes(item.id)}
                      onChange={() => onSelectItem(item.id)}
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      onClick={e => e.stopPropagation()}
                    />
                  </div>

                  {/* Item Content */}
                  <h4 className="font-medium text-gray-900 mb-2 text-sm">{item.title}</h4>
                  <p className="text-xs text-gray-600 mb-3 line-clamp-2">{item.content}</p>

                  {/* Item Meta */}
                  <div className="space-y-2">
                    <div
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getItemTypeColor(item.type)}`}
                    >
                      {item.type}
                    </div>

                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{formatDate(item.createdAt)}</span>
                      <span className="font-medium">{item.assignee}</span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>👤 {item.reporter}</span>
                      {item.resolvedAt && <span className="text-green-600">✅ Resolved</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Add New Button */}
            <button className="mt-4 flex items-center justify-center px-4 py-2 text-sm text-gray-600 bg-white rounded-lg border border-dashed border-gray-300 hover:border-gray-400 hover:bg-gray-50 transition-colors">
              <span className="mr-2">+</span>
              Thêm mới
            </button>
          </div>
        ))}
      </div>

      {/* Drag Overlay */}
      {draggedItem && (
        <div className="fixed inset-0 pointer-events-none z-50">
          <div className="absolute top-0 left-0 bg-white rounded-lg p-4 shadow-lg border transform -translate-x-1/2 -translate-y-1/2 opacity-80">
            <div className="flex items-center">
              <span className="text-lg mr-2">{getTypeIcon(draggedItem.type)}</span>
              <span className="font-medium text-gray-900">{draggedItem.title}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KanbanBoard;
