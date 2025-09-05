import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import { useAdminMovieFormData } from '../../hooks/useAdminMovieForm';
import LoadingSpinner from './LoadingSpinner';
import Select from './Select';
import toast from 'react-hot-toast';

const defaultMovie = {
  title: '',
  title_en: '',
  title_vi: '',
  overview_en: '',
  overview_vi: '',
  release_date: '',
  genres: [],
  poster_path: '',
  backdrop_path: '',
  runtime: '',
  status: '',
};

const MovieFormModal = ({ open, onClose, onSubmit, movie }) => {
  const [form, setForm] = useState(defaultMovie);
  const [errors, setErrors] = useState({});
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch form data
  const { genres, movieStatusOptions, isLoading, error } = useAdminMovieFormData();

  useEffect(() => {
    if (movie) {
      const movieGenres = movie.genres ? movie.genres.map(g => g.id || g) : [];
      setForm({
        ...defaultMovie,
        ...movie,
        genres: movieGenres,
        poster_path: movie.poster_path || movie.poster_url || '',
        backdrop_path: movie.backdrop_path || movie.backdrop_url || '',
      });
      setSelectedGenres(movieGenres);
    } else {
      setForm(defaultMovie);
      setSelectedGenres([]);
    }
    setErrors({});
    setIsSubmitting(false);
  }, [movie, open]);

  const showToast = (type, message) => {
    switch (type) {
      case 'success':
        toast.success(message);
        break;
      case 'error':
        toast.error(message);
        break;
      case 'warning':
        toast(message, { icon: '⚠️' });
        break;
      case 'info':
        toast(message, { icon: 'ℹ️' });
        break;
      default:
        toast(message);
    }
  };

  const validate = () => {
    const errs = {};
    if (!form.title) errs.title = 'Vui lòng nhập tiêu đề phim';
    if (!form.release_date) errs.release_date = 'Vui lòng nhập ngày phát hành';
    if (selectedGenres.length === 0) errs.genres = 'Vui lòng chọn ít nhất một thể loại';
    return errs;
  };

  const handleChange = e => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleGenreChange = genreId => {
    setSelectedGenres(prev => {
      const isSelected = prev.includes(genreId);
      if (isSelected) {
        return prev.filter(id => id !== genreId);
      } else {
        return [...prev, genreId];
      }
    });
  };

  const handleSubmit = async e => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      showToast('error', 'Vui lòng kiểm tra lại thông tin đã nhập');
      return;
    }

    setIsSubmitting(true);
    try {
      // Chỉ gửi các trường cần thiết và đã được điền
      const submitData = {
        title: form.title,
        title_en: form.title_en,
        title_vi: form.title_vi,
        overview_en: form.overview_en,
        overview_vi: form.overview_vi,
        release_date: form.release_date,
        genres: selectedGenres,
        poster_path: form.poster_path,
        backdrop_path: form.backdrop_path,
        runtime: form.runtime,
        status: form.status,
      };

      // Loại bỏ các trường rỗng
      Object.keys(submitData).forEach(key => {
        if (submitData[key] === '' || submitData[key] === null || submitData[key] === undefined) {
          delete submitData[key];
        }
      });

      const result = await onSubmit(submitData);

      // Success toast
      showToast('success', movie ? 'Cập nhật phim thành công!' : 'Tạo phim mới thành công!');

      // Đóng modal sau 1 giây để user thấy toast
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (error) {
      console.error('Error submitting movie form:', error);

      // Error toast
      const errorMessage =
        error?.response?.data?.message ||
        error?.message ||
        (movie ? 'Không thể cập nhật phim' : 'Không thể tạo phim mới');
      showToast('error', errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (isSubmitting) {
      showToast('warning', 'Vui lòng đợi quá trình xử lý hoàn tất');
      return;
    }
    onClose();
  };

  if (isLoading) {
    return (
      <Modal open={open} onClose={onClose} title="Đang tải..." size="md">
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner />
        </div>
      </Modal>
    );
  }

  if (error) {
    return (
      <Modal open={open} onClose={onClose} title="Lỗi" size="md">
        <div className="text-center py-8">
          <p className="text-red-500 mb-4">Không thể tải dữ liệu form</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Thử lại
          </button>
        </div>
      </Modal>
    );
  }

  return (
    <>
      <Modal
        open={open}
        onClose={handleClose}
        title={movie ? 'Chỉnh sửa phim' : 'Thêm phim mới'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Tiêu đề *</label>
            <input
              name="title"
              value={form.title}
              onChange={handleChange}
              disabled={isSubmitting}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-black focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            {errors.title && <div className="text-red-500 text-xs mt-1">{errors.title}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Tiêu đề tiếng Anh</label>
            <input
              name="title_en"
              value={form.title_en}
              onChange={handleChange}
              disabled={isSubmitting}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-black focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Tiêu đề tiếng Việt</label>
            <input
              name="title_vi"
              value={form.title_vi}
              onChange={handleChange}
              disabled={isSubmitting}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-black focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Mô tả tiếng Anh</label>
            <textarea
              name="overview_en"
              value={form.overview_en}
              onChange={handleChange}
              rows={3}
              disabled={isSubmitting}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-black focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Mô tả tiếng Việt</label>
            <textarea
              name="overview_vi"
              value={form.overview_vi}
              onChange={handleChange}
              rows={3}
              disabled={isSubmitting}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-black focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Ngày phát hành *</label>
            <input
              type="date"
              name="release_date"
              value={form.release_date}
              onChange={handleChange}
              disabled={isSubmitting}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-black focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            {errors.release_date && (
              <div className="text-red-500 text-xs mt-1">{errors.release_date}</div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Thể loại *</label>
            <div className="mt-1 max-h-40 overflow-y-auto border border-gray-300 rounded p-2">
              {/* Nhóm genres theo ngôn ngữ */}
              {(() => {
                const genresByLanguage = genres.reduce((acc, genre) => {
                  const lang = genre.language || 'en';
                  if (!acc[lang]) acc[lang] = [];
                  acc[lang].push(genre);
                  return acc;
                }, {});

                return Object.entries(genresByLanguage).map(([lang, langGenres]) => (
                  <div key={lang} className="mb-3">
                    <div className="text-xs font-medium text-gray-500 mb-2 uppercase">
                      {lang === 'vi' ? 'Tiếng Việt' : 'English'}
                    </div>
                    {langGenres.map(genre => (
                      <label key={genre.id} className="flex items-center space-x-2 py-1 ml-2">
                        <input
                          type="checkbox"
                          checked={selectedGenres.includes(genre.id)}
                          onChange={() => handleGenreChange(genre.id)}
                          disabled={isSubmitting}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <span className="text-sm text-gray-700">{genre.name}</span>
                      </label>
                    ))}
                  </div>
                ));
              })()}
            </div>
            {errors.genres && <div className="text-red-500 text-xs mt-1">{errors.genres}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Poster Path</label>
            <input
              name="poster_path"
              value={form.poster_path}
              onChange={handleChange}
              placeholder="https://example.com/poster.jpg"
              disabled={isSubmitting}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-black focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Backdrop Path</label>
            <input
              name="backdrop_path"
              value={form.backdrop_path}
              onChange={handleChange}
              placeholder="https://example.com/backdrop.jpg"
              disabled={isSubmitting}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-black focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Thời lượng (phút)</label>
            <input
              type="number"
              name="runtime"
              value={form.runtime}
              onChange={handleChange}
              min="0"
              disabled={isSubmitting}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-black focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Trạng thái</label>
            <Select
              name="status"
              value={form.status}
              onChange={handleChange}
              options={movieStatusOptions}
              placeholder="Chọn trạng thái"
              disabled={isSubmitting}
            />
          </div>

          <div className="flex justify-end space-x-2 mt-6">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isSubmitting && <LoadingSpinner />}
              <span>{isSubmitting ? (movie ? 'Đang cập nhật...' : 'Đang tạo...') : 'Lưu'}</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* Toast notifications are handled by react-hot-toast */}
    </>
  );
};

export default MovieFormModal;
