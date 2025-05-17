const Rating = ({ voteAverage, voteCount }) => {
  const formatVoteCount = (count) => {
    if (count >= 1_000_000) {
      return `${(count / 1_000_000).toFixed(1)}M`;
    }
    if (count >= 1_000) {
      return `${(count / 1_000).toFixed(1)}K`;
    }
    return count.toString();
  };

  return (
    <div className="mt-2 flex items-center gap-2">
      {/* Star Icon */}
      <div className="flex items-center gap-1">
        <span className="text-yellow-400">★</span>
        <span className="font-medium text-white">{voteAverage?.toFixed(1) || 'N/A'}</span>
      </div>

      {/* Vote Count */}
      {voteCount > 0 && (
        <span className="text-sm text-gray-400">({formatVoteCount(voteCount)})</span>
      )}
    </div>
  );
};

export default Rating;
