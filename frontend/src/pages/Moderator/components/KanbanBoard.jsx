import React, { useState, useEffect } from 'react';
import {
  getUnifiedModerationQueue,
  updateTaskStatus,
  moderateReview,
} from '../../../api/movieService';

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

  // Fetch moderation data from API
  useEffect(() => {
    const fetchModerationData = async () => {
      try {
        setLoading(true);
        const data = await getUnifiedModerationQueue(1, 100); // Get more items for kanban

        // Use kanban_data from API response
        const kanbanData = data.kanban_data || {};

        // Ensure no duplicate items across columns
        const usedItemIds = new Set();

        const columnsData = {
          backlog: {
            id: 'backlog',
            title: 'Hàng đợi',
            items: (kanbanData.backlog || []).filter(item => {
              if (usedItemIds.has(item.id)) return false;
              usedItemIds.add(item.id);
              return true;
            }),
          },
          inProgress: {
            id: 'inProgress',
            title: 'Đang xử lý',
            items: (kanbanData.in_progress || []).filter(item => {
              if (usedItemIds.has(item.id)) return false;
              usedItemIds.add(item.id);
              return true;
            }),
          },
          review: {
            id: 'review',
            title: 'Đang xem xét',
            items: (kanbanData.review || []).filter(item => {
              if (usedItemIds.has(item.id)) return false;
              usedItemIds.add(item.id);
              return true;
            }),
          },
          completed: {
            id: 'completed',
            title: 'Hoàn thành',
            items: (kanbanData.completed || []).filter(item => {
              if (usedItemIds.has(item.id)) return false;
              usedItemIds.add(item.id);
              return true;
            }),
          },
        };

        setColumns(columnsData);
      } catch (error) {
        console.error('Error fetching moderation data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchModerationData();
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
      case 'spoiler':
        return '⚠️';
      case 'both':
        return '🔥';
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

  const handleDrop = async (e, targetColumnId) => {
    e.preventDefault();

    if (!draggedItem || !draggedFrom || draggedFrom === targetColumnId) {
      return;
    }

    try {
      // Update task status via API
      const newStatus = targetColumnId === 'inProgress' ? 'in_progress' : targetColumnId;
      await updateTaskStatus(draggedItem.id, newStatus);

      // Update columns state
      setColumns(prev => {
        const newColumns = { ...prev };

        // Remove item from source column
        newColumns[draggedFrom].items = newColumns[draggedFrom].items.filter(
          item => item.id !== draggedItem.id
        );

        // Update item status and add to target column
        const updatedItem = { ...draggedItem, status: newStatus };
        newColumns[targetColumnId].items.push(updatedItem);

        return newColumns;
      });
    } catch (error) {
      console.error('Error updating task status:', error);
      // Don't update UI if API call failed
    }

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
      <style>{`
        .scrollbar-thin::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        .scrollbar-thin::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 3px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Kanban Board</h2>
            <p className="text-gray-600">Quản lý workflow kiểm duyệt bằng drag-and-drop</p>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <span>Scroll dọc trong mỗi cột để xem tất cả items</span>
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
          </div>
        </div>
      </div>

      {/* Kanban Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 h-[calc(205vh-400px)]">
        {Object.values(columns).map(column => (
          <div
            key={column.id}
            className="bg-gray-50 rounded-lg border border-gray-200 shadow-sm flex flex-col h-full"
            onDragOver={handleDragOver}
            onDrop={e => handleDrop(e, column.id)}
          >
            {/* Column Header - Fixed */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 flex-shrink-0">
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

            {/* Column Items - Scrollable with fixed height */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
              {column.items.length === 0 ? (
                <div className="text-center py-8 text-gray-500 text-sm">
                  <div className="w-12 h-12 mx-auto mb-2 bg-gray-100 rounded-full flex items-center justify-center">
                    <span className="text-lg">📋</span>
                  </div>
                  Không có items nào
                </div>
              ) : (
                column.items.map(item => (
                  <div
                    key={`${column.id}-${item.id}`}
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
                        <span>{formatDate(item.created_at)}</span>
                        <span className="font-medium">{item.user || 'Unassigned'}</span>
                      </div>

                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>🎬 {item.movie_title || 'No Movie'}</span>
                        {item.status === 'completed' && (
                          <span className="text-green-600">✅ Completed</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
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
