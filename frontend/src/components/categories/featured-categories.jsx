import { Link } from 'react-router-dom';

const categories = [
  {
    id: 1,
    name: 'Action',
    image:
      'https://images.unsplash.com/photo-1536440136628-849c177e76a1?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1025&q=80',
    slug: 'action',
    count: 245,
  },
  {
    id: 2,
    name: 'Drama',
    image:
      'https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1170&q=80',
    slug: 'drama',
    count: 189,
  },
  {
    id: 3,
    name: 'Comedy',
    image:
      'https://images.unsplash.com/photo-1512070679279-8988d32161be?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1170&q=80',
    slug: 'comedy',
    count: 156,
  },
  {
    id: 4,
    name: 'Horror',
    image:
      'https://images.unsplash.com/photo-1509347528160-9a9e33742cdb?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1170&q=80',
    slug: 'horror',
    count: 98,
  },
];

const FeaturedCategories = () => {
  return (
    <section className="relative mt-12 w-full overflow-x-hidden pb-12">
      <div className="ml-14">
        <h2 className="mb-8 text-3xl font-bold text-white">Featured Categories</h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {categories.map((category) => (
            <Link
              key={category.id}
              to={`/category/${category.slug}`}
              className="group relative overflow-hidden rounded-lg shadow-lg transition-all duration-300 hover:scale-105"
            >
              <div className="aspect-w-16 aspect-h-9">
                <img
                  src={category.image}
                  alt={category.name}
                  className="size-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
                <div className="absolute inset-x-0 bottom-0 p-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-bold text-white drop-shadow-lg">
                      {category.name}
                    </h3>
                    <span className="rounded-full bg-red-600/90 px-3 py-1 text-sm font-semibold text-white backdrop-blur-sm">
                      {category.count} movies
                    </span>
                  </div>
                  <div className="mt-2 flex items-center text-gray-300">
                    <span className="text-sm">Explore collection</span>
                    <svg
                      className="ml-2 size-4 transition-transform duration-300 group-hover:translate-x-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
        <div className="mt-8 flex justify-center">
          <Link
            to="/categories"
            className="rounded bg-red-600 px-8 py-3 text-lg font-semibold text-white shadow-lg transition hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2"
          >
            View All Categories
          </Link>
        </div>
      </div>
    </section>
  );
};

export default FeaturedCategories;
