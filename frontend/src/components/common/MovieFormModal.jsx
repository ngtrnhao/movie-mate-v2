import React, { useState, useEffect } from 'react';
import Modal from './Modal';

const defaultMovie = {
  title: '',
  title_en: '',
  title_vi: '',
  overview_en: '',
  overview_vi: '',
  release_date: '',
  genres: '',
  poster_path: '',
  backdrop_path: '',
  runtime: '',
  status: '',
};

const MovieFormModal = ({ open, onClose, onSubmit, movie }) => {
  const [form, setForm] = useState(defaultMovie);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (movie) {
      setForm({
        ...defaultMovie,
        ...movie,
        genres: movie.genres ? movie.genres.map(g => g.name).join(', ') : '',
        poster_path: movie.poster_path || movie.poster_url || '',
        backdrop_path: movie.backdrop_path || movie.backdrop_url || '',
      });
    } else {
      setForm(defaultMovie);
    }
    setErrors({});
  }, [movie, open]);

  const validate = () => {
    const errs = {};
    if (!form.title) errs.title = 'Vui lòng nhập tiêu đề phim';
    if (!form.release_date) errs.release_date = 'Vui lòng nhập ngày phát hành';
    if (!form.genres) errs.genres = 'Vui lòng nhập thể loại';
    return errs;
  };

  const handleChange = e => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = e => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    // Chuyển genres thành mảng nếu cần
    const submitData = {
      ...form,
      genres: form.genres
        .split(',')
        .map(s => s.trim())
        .filter(Boolean),
      poster_path: form.poster_path,
      backdrop_path: form.backdrop_path,
    };
    onSubmit(submitData);
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={movie ? 'Chỉnh sửa phim' : 'Thêm phim mới'}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Tiêu đề *</label>
          <input
            name="title"
            value={form.title}
            onChange={handleChange}
            className="mt-1 block w-full rounded text-black  border-gray-300"
          />
          {errors.title && <div className="text-red-500 text-xs mt-1">{errors.title}</div>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Tiêu đề tiếng Anh</label>
          <input
            name="title_en"
            value={form.title_en}
            onChange={handleChange}
            className="mt-1 block w-full rounded text-black border-gray-300"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Tiêu đề tiếng Việt</label>
          <input
            name="title_vi"
            value={form.title_vi}
            onChange={handleChange}
            className="mt-1 block w-full rounded text-black border-gray-300"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Mô tả tiếng Anh</label>
          <textarea
            name="overview_en"
            value={form.overview_en}
            onChange={handleChange}
            className="mt-1 block w-full rounded text-black border-gray-300"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Mô tả tiếng Việt</label>
          <textarea
            name="overview_vi"
            value={form.overview_vi}
            onChange={handleChange}
            className="mt-1 block w-full rounded text-black border-gray-300"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Ngày phát hành *</label>
          <input
            type="date"
            name="release_date"
            value={form.release_date}
            onChange={handleChange}
            className="mt-1 block w-full rounded text-black border-gray-300"
          />
          {errors.release_date && (
            <div className="text-red-500 text-xs mt-1">{errors.release_date}</div>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Thể loại (phân cách bằng dấu phẩy) *
          </label>
          <input
            name="genres"
            value={form.genres}
            onChange={handleChange}
            className="mt-1 block w-full rounded text-black border-gray-300"
          />
          {errors.genres && <div className="text-red-500 text-xs mt-1">{errors.genres}</div>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Poster Path *</label>
          <input
            name="poster_path"
            value={form.poster_path}
            onChange={handleChange}
            className="mt-1 block w-full rounded text-black border-gray-300"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Backdrop Path</label>
          <input
            name="backdrop_path"
            value={form.backdrop_path}
            onChange={handleChange}
            className="mt-1 block w-full text-black rounded border-gray-300"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Thời lượng (phút)</label>
          <input
            name="runtime"
            value={form.runtime}
            onChange={handleChange}
            className="mt-1 block w-full rounded text-black border-gray-300"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Trạng thái</label>
          <input
            name="status"
            value={form.status}
            onChange={handleChange}
            className="mt-1 block w-full rounded text-black border-gray-300"
          />
        </div>
        <div className="flex justify-end space-x-2 mt-6">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded bg-gray-200 text-gray-700 hover:bg-gray-300"
          >
            Hủy
          </button>
          <button
            type="submit"
            className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            Lưu
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default MovieFormModal;
