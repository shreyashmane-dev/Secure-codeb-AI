import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (event) => {
    event.preventDefault();
    try {
      setLoading(true);
      setError("");
      await login(email, password);
      const redirectPath = location.state?.from || "/dashboard";
      navigate(redirectPath, { replace: true });
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page auth-page">
      <section className="auth-card glass-card">
        <h1>SecureCode AI Login</h1>
        <p>Authenticate with Firebase email/password to access protected scanning APIs.</p>
        <form onSubmit={onSubmit}>
          <label className="input-label">
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="input-label">
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          {error && <p className="error-text">{error}</p>}
          <button type="submit" className="primary-btn" disabled={loading}>
            {loading ? "Signing In..." : "Login"}
          </button>
        </form>
        <p className="auth-switch">
          No account? <Link to="/signup">Create one</Link>
        </p>
      </section>
    </main>
  );
};

export default LoginPage;
