import { Link } from 'react-router-dom';

const QuickLink = () => {
  const links = [
    { name: 'Home', path: '/' },
    { name: 'Discover Movies', path: '/movies' },
    { name: 'Watchlist', path: '/watchlist' },
    { name: 'About Us', path: '/about' },
  ];

  return (
    <div>
      <h3 className="mb-4 text-lg font-semibold text-foreground transition-colors duration-200">
        Quick Links
      </h3>
      <ul className="space-y-2">
        {links.map(link => (
          <li key={link.path}>
            <Link
              to={link.path}
              className="text-muted-foreground transition-colors duration-200 hover:text-red-600"
              onClick={() => window.scrollTo(0, 0)}
            >
              {link.name}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default QuickLink;
