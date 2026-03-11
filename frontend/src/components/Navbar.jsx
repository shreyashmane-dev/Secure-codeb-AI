import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

const links = [
  { to: "/", label: "Home" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/scan", label: "Scan" },
  { to: "/reports", label: "Reports" },
  { to: "/about", label: "About" },
];

const Navbar = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  return (
    <header className="topbar">
      <div className="brand">
        <span className="brand-badge">SC</span>
        <div>
          <p className="brand-title">SecureCode AI</p>
          <p className="brand-subtitle">Code Risk & Quality Analyzer</p>
        </div>
      </div>
      <nav className="nav-links">
        {user &&
          links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => (isActive ? "nav-link nav-link-active" : "nav-link")}
            >
              {link.label}
            </NavLink>
          ))}
        {!user && (
          <>
            <NavLink to="/login" className={({ isActive }) => (isActive ? "nav-link nav-link-active" : "nav-link")}>
              Login
            </NavLink>
            <NavLink
              to="/signup"
              className={({ isActive }) => (isActive ? "nav-link nav-link-active" : "nav-link")}
            >
              Signup
            </NavLink>
          </>
        )}
      </nav>
      <div className="topbar-actions">
        <button className="theme-toggle" onClick={toggleTheme} type="button">
          {theme === "dark" ? "Light Mode" : "Dark Mode"}
        </button>
        {user && (
          <button className="ghost-btn" onClick={logout} type="button">
            Logout
          </button>
        )}
      </div>
    </header>
  );
};

export default Navbar;
