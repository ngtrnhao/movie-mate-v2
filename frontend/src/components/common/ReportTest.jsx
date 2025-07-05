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
    <div className="p-6 bg-gray-900 min-h-screen">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-6">Test Report Functionality</h1>

        <div className="bg-gray-800 rounded-lg p-4 mb-4">
          <h3 className="text-white font-medium mb-2">Review Test</h3>
          <p className="text-gray-300 mb-4">{mockReview.content}</p>

          <ReviewActions
            review={mockReview}
            onVoteUpdate={(reviewId, result) => {
              console.log('Vote updated:', result);
            }}
          />
        </div>

        <div className="text-gray-400 text-sm">
          <p>Hướng dẫn test:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
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
