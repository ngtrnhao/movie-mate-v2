import { useState, useEffect, useCallback } from 'react';
import { getUnifiedModerationQueue, updateTaskStatus } from '../../../api/movieService';

const KanbanBoard = ({
  selectedItems,
  onSelectItem,
  onBulkAction,
  isAdmin,
  // Add props for external data
  columns: externalColumns = null,
  disableInternalFetch = false,
  onDataFetch = null,
}) => {
  const [columns, setColumns] = useState(
    externalColumns || {
      backlog: { id: 'backlog', title: 'Hàng đợi', items: [] },
      inProgress: { id: 'inProgress', title: 'Đang xử lý', items: [] },
      review: { id: 'review', title: 'Đang xem xét', items: [] },
      completed: { id: 'completed', title: 'Hoàn thành', items: [] },
    }
  );

  const [draggedItem, setDraggedItem] = useState(null);
  const [draggedFrom, setDraggedFrom] = useState(null);
  const [loading, setLoading] = useState(!disableInternalFetch);
  const [lastFetchTime, setLastFetchTime] = useState(0);

  // Update columns when external data changes, and deduplicate tasks across columns
  useEffect(() => {
    if (externalColumns && disableInternalFetch) {
      // Remove duplicate tasks across columns
      const seen = new Set();
      const dedupedColumns = {};
      Object.entries(externalColumns).forEach(([colKey, col]) => {
        dedupedColumns[colKey] = {
          ...col,
          items: col.items.filter(item => {
            if (seen.has(item.id)) return false;
            seen.add(item.id);
            return true;
          }),
        };
      });
      setColumns(dedupedColumns);
      console.log('✅ KanbanBoard received external data (deduped):', {
        totalItems: Object.values(dedupedColumns).reduce((sum, col) => sum + col.items.length, 0),
      });
    }
  }, [externalColumns, disableInternalFetch]);

  // Fetch moderation data from API with caching (only if not disabled)
  const fetchModerationData = useCallback(async () => {
    if (disableInternalFetch) {
      console.log('🚫 KanbanBoard internal fetch disabled - using external data');
      return;
    }

    // Skip if data is fresh (less than 30 seconds old)
    const now = Date.now();
    if (
      now - lastFetchTime < 30000 &&
      Object.keys(columns).some(key => columns[key].items.length > 0)
    ) {
      console.log('🚫 Skipping API call for Kanban - data is fresh');
      return;
    }

    try {
      setLoading(true);
      console.log('🔄 Fetching unified moderation queue for Kanban...');

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
      setLastFetchTime(now);

      // Notify parent component about data fetch
      if (onDataFetch) {
        onDataFetch({
          columns: columnsData,
          timestamp: now,
        });
      }

      console.log('✅ Kanban data loaded:', {
        totalItems: Object.values(columnsData).reduce((sum, col) => sum + col.items.length, 0),
        fromCache: false,
      });
    } catch (error) {
      console.error('Error fetching moderation data:', error);
    } finally {
      setLoading(false);
    }
  }, [lastFetchTime, columns, onDataFetch, disableInternalFetch]);

  // Only fetch if we don't have external data and internal fetch is not disabled
  useEffect(() => {
    if (!disableInternalFetch) {
      fetchModerationData();
    } else {
      console.log('✅ KanbanBoard using external data - no internal fetch needed');
      setLoading(false);
    }
  }, [fetchModerationData, disableInternalFetch]);

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

  // In handleDrop, ensure task is only in one column after move
  const handleDrop = async (e, targetColumnId) => {
    e.preventDefault();

    if (!draggedItem || !draggedFrom || draggedFrom === targetColumnId) {
      return;
    }

    try {
      // Update task status via API
      const newStatus = targetColumnId === 'inProgress' ? 'in_progress' : targetColumnId;
      await updateTaskStatus(draggedItem.id, newStatus);

      // Update columns state: remove from all columns, add to target
      setColumns(prev => {
        const newColumns = {};
        Object.entries(prev).forEach(([colKey, col]) => {
          newColumns[colKey] = {
            ...col,
            items: col.items.filter(item => item.id !== draggedItem.id),
          };
        });
        newColumns[targetColumnId] = {
          ...newColumns[targetColumnId],
          items: [draggedItem, ...newColumns[targetColumnId].items],
        };
        return newColumns;
      });
    } catch (error) {
      console.error('Error updating task status:', error);
    } finally {
      setDraggedItem(null);
      setDraggedFrom(null);
    }
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
      <div className="flex h-64 items-center justify-center">
        <div className="size-12 animate-spin rounded-full border-b-2 border-indigo-600"></div>
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
        <div className="flex items-center justify-between">
          <div>
            <h2 className="mb-2 text-2xl font-bold text-gray-900">Kanban Board</h2>
            <p className="text-gray-600">Quản lý workflow kiểm duyệt bằng drag-and-drop</p>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <span>Scroll dọc trong mỗi cột để xem tất cả items</span>
            <div className="size-2 rounded-full bg-blue-500"></div>
          </div>
        </div>
      </div>

      {/* Kanban Columns */}
      <div className="grid h-[calc(205vh-400px)] grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {Object.values(columns).map(column => (
          <div
            key={column.id}
            className="flex h-full flex-col rounded-lg border border-gray-200 bg-gray-50 shadow-sm"
            onDragOver={handleDragOver}
            onDrop={e => handleDrop(e, column.id)}
          >
            {/* Column Header - Fixed */}
            <div className="flex shrink-0 items-center justify-between border-b border-gray-200 p-4">
              <div className="flex items-center">
                <h3 className="font-semibold text-gray-900">{column.title}</h3>
                <span className="ml-2 rounded-full bg-gray-200 px-2 py-1 text-sm text-gray-700">
                  {column.items.length}
                </span>
              </div>
              <button className="text-gray-500 hover:text-gray-700">
                <span className="text-lg">⋮</span>
              </button>
            </div>

            {/* Column Items - Scrollable with fixed height */}
            <div className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 flex-1 space-y-3 overflow-y-auto p-4">
              {column.items.length === 0 ? (
                <div className="py-8 text-center text-sm text-gray-500">
                  <div className="mx-auto mb-2 flex size-12 items-center justify-center rounded-full bg-gray-100">
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
                    className={`flex min-h-[140px] w-full max-w-full cursor-move flex-col gap-2 overflow-hidden break-words rounded-lg border bg-white p-4 shadow-sm transition-shadow hover:shadow-md md:min-h-[120px] ${
                      selectedItems.includes(item.id) ? 'ring-2 ring-indigo-500' : ''
                    }`}
                    onClick={() => onSelectItem(item.id)}
                    style={{ wordBreak: 'break-word' }}
                  >
                    {/* Item Header */}
                    <div className="mb-2 flex w-full items-start justify-between">
                      <div className="flex min-w-0 items-center">
                        <span className="mr-2 shrink-0 text-lg">{getTypeIcon(item.type)}</span>
                        <div
                          className={`size-2 shrink-0 rounded-full ${getPriorityColor(item.priority)}`}
                        ></div>
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(item.id)}
                        onChange={() => onSelectItem(item.id)}
                        className="ml-2 shrink-0 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        onClick={e => e.stopPropagation()}
                      />
                    </div>

                    {/* Item Content */}
                    <h4
                      className="mb-1 max-w-full truncate text-sm font-medium text-gray-900"
                      title={item.title}
                    >
                      {item.title}
                    </h4>
                    <p
                      className="mb-2 line-clamp-2 max-w-full break-words text-xs text-gray-600"
                      title={item.content}
                    >
                      {item.content}
                    </p>

                    {/* Item Meta */}
                    <div className="w-full space-y-2">
                      <div
                        className={`inline-flex items-center rounded-full border px-2 py-1 text-xs font-medium ${getItemTypeColor(item.type)} max-w-full truncate`}
                        title={item.type}
                      >
                        {item.type}
                      </div>

                      <div className="flex w-full flex-wrap items-center justify-between gap-x-2 text-xs text-gray-500">
                        <span className="max-w-[60%] truncate">{formatDate(item.created_at)}</span>
                        <span className="max-w-[40%] truncate font-medium">
                          {item.user || 'Unassigned'}
                        </span>
                      </div>

                      <div className="flex w-full flex-wrap items-center justify-between gap-x-2 text-xs text-gray-500">
                        <span className="max-w-[70%] truncate">
                          🎬 {item.movie_title || 'No Movie'}
                        </span>
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
            <button className="mt-4 flex items-center justify-center rounded-lg border border-dashed border-gray-300 bg-white px-4 py-2 text-sm text-gray-600 transition-colors hover:border-gray-400 hover:bg-gray-50">
              <span className="mr-2">+</span>
              Thêm mới
            </button>
          </div>
        ))}
      </div>

      {/* Drag Overlay */}
      {draggedItem && (
        <div className="pointer-events-none fixed inset-0 z-50">
          <div className="absolute left-0 top-0 -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-white p-4 opacity-80 shadow-lg">
            <div className="flex items-center">
              <span className="mr-2 text-lg">{getTypeIcon(draggedItem.type)}</span>
              <span className="font-medium text-gray-900">{draggedItem.title}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KanbanBoard;
