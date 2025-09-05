const RecommendedInfo = ({ match, recommendReason }) => {
  if (!match && !recommendReason) return null;
  return (
    <div className="mt-2 flex flex-col gap-1">
      {match && (
        <span className="inline-block w-fit rounded bg-green-600/80 px-2 py-0.5 text-xs font-semibold text-white">
          {match}% match
        </span>
      )}
      {recommendReason && <span className="text-xs italic text-gray-300">{recommendReason}</span>}
    </div>
  );
};

export default RecommendedInfo;
