import { NavLink } from 'react-router-dom';

const Navigation = () => {
  return (
    <nav className="hidden items-center gap-8 md:flex">
      <NavLink
        to="/"
        className={({ isActive }) =>
          isActive ? 'text-primary' : 'text-muted-foreground hover:text-primary transition-colors'
        }
      >
        Home
      </NavLink>
      <NavLink
        to="/watchlist"
        className={({ isActive }) =>
          isActive ? 'text-primary' : 'text-muted-foreground hover:text-primary transition-colors'
        }
      >
        Watchlist
      </NavLink>
    </nav>
  );
};

export default Navigation;
