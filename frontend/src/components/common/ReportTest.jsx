import { useState } from 'react';
import ReviewActions from './ReviewActions';

const ReportTest = () => {
  const [mockReview] = useState({
    id: 1,
    content:
      'Đây là một review test để demo chức năng báo cáo. Review này chứa nội dung mẫu để test.',
    reviewer_name: 'Test User',
    helpful_votes: 5,
    total_votes: 10,
    can_vote: true,
    can_edit: false,
    user_vote: null,
  });

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 text-2xl font-bold text-white">Test Report Functionality</h1>

        <div className="mb-4 rounded-lg bg-gray-800 p-4">
          <h3 className="mb-2 font-medium text-white">Review Test</h3>
          <p className="mb-4 text-gray-300">{mockReview.content}</p>

          <ReviewActions
            review={mockReview}
            onVoteUpdate={(reviewId, result) => {
              console.log('Vote updated:', result);
            }}
          />
        </div>

        <div className="text-sm text-gray-400">
          <p>Hướng dẫn test:</p>
          <ul className="mt-2 list-inside list-disc space-y-1">
            <li>Click vào icon 3 chấm (⋮) bên cạnh review</li>
            <li>Chọn "Báo cáo"</li>
            <li>Chọn lý do báo cáo và nhập mô tả (tùy chọn)</li>
            <li>Click "Gửi báo cáo"</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ReportTest;
