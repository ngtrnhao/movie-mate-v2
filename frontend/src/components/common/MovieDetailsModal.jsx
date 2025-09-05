import {
  ClockIcon,
  CalendarIcon,
  TagIcon,
  ChartBarIcon,
  DocumentCheckIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  StarIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  FilmIcon,
  PhotoIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import Modal from './Modal';

const MetricItem = ({ icon: Icon, label, value, className = '' }) => (
  <div className={`flex items-center space-x-2 ${className}`}>
    <Icon className="size-5 shrink-0 text-gray-400" />
    <span className="text-sm text-gray-500">{label}:</span>
    <span className="text-sm font-medium text-gray-900">{value}</span>
  </div>
);

const Section = ({ title, icon: Icon, children, className = '' }) => (
  <div className={`space-y-4 ${className}`}>
    <div className="flex items-center space-x-2 border-b border-gray-200 pb-2">
      <Icon className="size-5 text-blue-600" />
      <h4 className="text-lg font-semibold text-gray-900">{title}</h4>
    </div>
    {children}
  </div>
);

const Badge = ({ children, color = 'gray' }) => {
  const colors = {
    gray: 'bg-gray-100 text-gray-800',
    green: 'bg-green-100 text-green-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    red: 'bg-red-100 text-red-800',
    blue: 'bg-blue-100 text-blue-800',
    orange: 'bg-orange-100 text-orange-800',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[color] || colors.gray}`}
    >
      {children}
    </span>
  );
};

const RatingDisplay = ({ rating, className = '' }) => {
  if (!rating) return <span className="text-gray-400">N/A</span>;
  return (
    <div className={`flex items-center space-x-1 ${className}`}>
      <StarIconSolid className="size-4 text-yellow-400" />
      <span className="font-medium text-gray-600">{rating}</span>
    </div>
  );
};

const MovieDetailsModal = ({ movie, open, onClose }) => {
  if (!movie) {
    console.log('MovieDetailsModal: No movie provided');
    return null;
  }

  console.log('MovieDetailsModal opened with movie:', movie?.title || 'Unknown Movie');

  const {
    title,
    title_en,
    title_vi,
    original_title,
    release_date,
    runtime,
    genres,
    overviews,
    poster_path,
    poster_url,
    backdrop_path,
    status,
    popularity,
    is_adult,
    adult,
    rating,
    cached_imdb_rating,
    vote_average,
    vote_count,
    combined_rating_score,
    trailers,
    approval_info,
    admin_control,
    production_metrics,
  } = movie;

  const getProductionMetrics = () =>
    production_metrics || {
      homepage_views: 0,
      detail_page_views: 0,
      engagement_rate: 0.0,
      performance_score: 0,
      trending_category: 'stable',
      review_count: 0,
      average_user_rating: null,
      trailer_plays: 0,
      positive_review_ratio: 0.0,
    };

  const metricsData = getProductionMetrics();

  const formatDateShort = date => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('vi-VN');
  };

  const getApprovalStatusColor = status => {
    const colors = {
      APPROVED: 'text-green-600 bg-green-50 border border-green-200 px-3 py-1 rounded-full',
      PENDING: 'text-yellow-600 bg-yellow-50 border border-yellow-200 px-3 py-1 rounded-full',
      REJECTED: 'text-red-600 bg-red-50 border border-red-200 px-3 py-1 rounded-full',
      NEEDS_REVIEW: 'text-orange-600 bg-orange-50 border border-orange-200 px-3 py-1 rounded-full',
    };
    return (
      colors[status] || 'text-gray-600 bg-gray-50 border border-gray-200 px-3 py-1 rounded-full'
    );
  };

  const getApprovalIcon = status => {
    const icons = {
      APPROVED: CheckCircleIcon,
      PENDING: ClockIcon,
      REJECTED: XCircleIcon,
      NEEDS_REVIEW: ExclamationTriangleIcon,
    };
    return icons[status] || ClockIcon;
  };

  const getTrendingColor = category => {
    const colors = {
      hot: 'red',
      trending: 'orange',
      rising: 'yellow',
      stable: 'blue',
      declining: 'gray',
    };
    return colors[category] || 'gray';
  };

  const ApprovalIcon = getApprovalIcon(approval_info?.status || admin_control?.approval_status);

  return (
    <Modal open={open} onClose={onClose} title="Chi tiết phim" size="max">
      <div className="space-y-8">
        {/* Header Section */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-3xl font-bold text-gray-900">{title}</h3>
            <div className="mt-2 space-y-1">
              {title_en && title_en !== title && (
                <p className="text-lg text-gray-600">English: {title_en}</p>
              )}
              {title_vi && title_vi !== title && title_vi !== title_en && (
                <p className="text-lg text-gray-600">Tiếng Việt: {title_vi}</p>
              )}
              {original_title &&
                original_title !== title &&
                original_title !== title_en &&
                original_title !== title_vi && (
                  <p className="text-sm text-gray-500">Original: {original_title}</p>
                )}
            </div>
          </div>
          <div className="flex flex-col items-end space-y-2">
            <div
              className={`flex items-center ${getApprovalStatusColor(approval_info?.status || admin_control?.approval_status)}`}
            >
              <ApprovalIcon className="mr-1.5 size-5" />
              <span className="text-sm font-medium">
                {approval_info?.status || admin_control?.approval_status || 'PENDING'}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* Column 1: Basic Info & Content */}
          <div className="space-y-6">
            {/* Basic Information */}
            <Section title="Thông tin cơ bản" icon={FilmIcon}>
              <div className="space-y-3">
                <MetricItem
                  icon={CalendarIcon}
                  label="Ngày phát hành"
                  value={formatDateShort(release_date)}
                />
                <MetricItem
                  icon={ClockIcon}
                  label="Thời lượng"
                  value={runtime ? `${runtime} phút` : 'N/A'}
                />
                <MetricItem
                  icon={TagIcon}
                  label="Thể loại"
                  value={genres?.map(g => g.name).join(', ') || 'N/A'}
                />
                <MetricItem
                  icon={GlobeAltIcon}
                  label="Trạng thái"
                  value={status || admin_control?.visibility_status || 'DRAFT'}
                />
                <MetricItem
                  icon={ChartBarIcon}
                  label="Độ phổ biến"
                  value={popularity ? popularity.toFixed(2) : 'N/A'}
                />
                <MetricItem
                  icon={ShieldCheckIcon}
                  label="Người lớn"
                  value={is_adult || adult ? 'Có' : 'Không'}
                />
              </div>
            </Section>

            {/* Rating Information */}
            <Section title="Đánh giá" icon={StarIcon}>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">IMDB:</span>
                  <RatingDisplay
                    className="text-gray-600"
                    rating={rating?.imdb || cached_imdb_rating}
                  />
                </div>
                {rating?.imdb_votes && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">IMDB Votes:</span>
                    <span className="text-sm font-medium text-gray-600">
                      {rating.imdb_votes.toLocaleString()}
                    </span>
                  </div>
                )}
                {rating?.tmdb && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">TMDB:</span>
                    <RatingDisplay className="text-gray-600" rating={rating.tmdb} />
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Combined Score:</span>
                  <span className="text-sm font-medium text-gray-600">
                    {combined_rating_score || rating?.combined_score}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Vote Average:</span>
                  <span className="text-sm font-medium text-gray-600">{vote_average}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Vote Count:</span>
                  <span className="text-sm font-medium text-gray-600">
                    {vote_count?.toLocaleString() || 'N/A'}
                  </span>
                </div>
              </div>
            </Section>

            {/* Content Overview */}
            <Section title="Nội dung" icon={DocumentCheckIcon}>
              <div className="space-y-3">
                {overviews?.vi ? (
                  <div>
                    <span className="text-sm font-medium text-gray-700">Tiếng Việt:</span>
                    <p className="mt-1 rounded-lg bg-gray-50 p-3 text-sm text-gray-900">
                      {overviews.vi}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm italic text-gray-500">Chưa có mô tả tiếng Việt</p>
                )}
                {overviews?.en ? (
                  <div>
                    <span className="text-sm font-medium text-gray-700">English:</span>
                    <p className="mt-1 rounded-lg bg-gray-50 p-3 text-sm text-gray-900">
                      {overviews.en}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm italic text-gray-500">Chưa có mô tả tiếng Anh</p>
                )}
                {trailers && trailers.length > 0 ? (
                  <MetricItem
                    icon={FilmIcon}
                    label="Trailers"
                    value={`${trailers.length} video(s)`}
                  />
                ) : (
                  <p className="text-sm italic text-gray-500">Chưa có trailer</p>
                )}
              </div>
            </Section>

            {/* Assets Information */}
            <Section title="Media Assets" icon={PhotoIcon}>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Poster:</span>
                  <Badge color={poster_path || poster_url ? 'green' : 'red'}>
                    {poster_path || poster_url ? 'Available' : 'Missing'}
                  </Badge>
                </div>
                {(poster_path || poster_url) && (
                  <div className="mt-2">
                    <img
                      src={poster_url || poster_path}
                      alt={title}
                      className="h-28 w-20 rounded-lg border border-gray-200 object-cover"
                    />
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Backdrop:</span>
                  <Badge color={backdrop_path ? 'green' : 'red'}>
                    {backdrop_path ? 'Available' : 'Missing'}
                  </Badge>
                </div>
                {backdrop_path && (
                  <div className="mt-2">
                    <img
                      src={`https://image.tmdb.org/t/p/original${backdrop_path}`}
                      alt={title}
                      className="h-28 w-20 rounded-lg border border-gray-200 object-cover"
                    />
                  </div>
                )}
              </div>
            </Section>
          </div>

          {/* Column 2: Production Metrics */}
          <div className="space-y-6">
            <Section title="Hiệu suất sản xuất" icon={ChartBarIcon}>
              {/* Enhanced Production Metrics */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg bg-blue-50 p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {metricsData.homepage_views?.toLocaleString() || '0'}
                    </div>
                    <div className="text-sm text-blue-700">Homepage Views</div>
                  </div>
                  <div className="rounded-lg bg-green-50 p-4 text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {metricsData.detail_page_views?.toLocaleString() || '0'}
                    </div>
                    <div className="text-sm text-green-700">Detail Views</div>
                  </div>
                  <div className="rounded-lg bg-purple-50 p-4 text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {metricsData.trailer_plays?.toLocaleString() || '0'}
                    </div>
                    <div className="text-sm text-purple-700">Trailer Plays</div>
                  </div>
                  <div className="rounded-lg bg-orange-50 p-4 text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {(metricsData.engagement_rate * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-orange-700">Engagement</div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Performance Score:</span>
                    <span className="text-sm font-medium text-gray-600">
                      {metricsData.performance_score?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Trending:</span>
                    <Badge color={getTrendingColor(metricsData.trending_category)}>
                      {metricsData.trending_category}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Reviews:</span>
                    <span className="text-sm font-medium text-gray-600">
                      {metricsData.review_count || 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Avg User Rating:</span>
                    <RatingDisplay rating={metricsData.average_user_rating} />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Positive Ratio:</span>
                    <span className="text-sm font-medium text-gray-600">
                      {(metricsData.positive_review_ratio * 100).toFixed(1)}%
                    </span>
                  </div>

                  {metricsData.click_through_rate > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">CTR:</span>
                      <span className="text-sm font-medium">
                        {(metricsData.click_through_rate * 100).toFixed(2)}%
                      </span>
                    </div>
                  )}

                  {metricsData.trailer_completion_rate > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">Trailer Completion:</span>
                      <span className="text-sm font-medium">
                        {(metricsData.trailer_completion_rate * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </Section>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default MovieDetailsModal;
