import {
  browserSessionPersistence,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  setPersistence,
  signInWithEmailAndPassword,
  signOut,
} from "firebase/auth";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { setAuthTokenProvider } from "../api/client";
import { firebaseAuth } from "../auth/firebase";

const AuthContext = createContext({
  user: null,
  token: "",
  loading: true,
  login: async () => {},
  signup: async () => {},
  logout: async () => {},
  refreshToken: async () => "",
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(sessionStorage.getItem("securecode_id_token") || "");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setPersistence(firebaseAuth, browserSessionPersistence).catch(() => null);
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(firebaseAuth, async (nextUser) => {
      setUser(nextUser || null);
      if (!nextUser) {
        sessionStorage.removeItem("securecode_id_token");
        setToken("");
        setLoading(false);
        return;
      }
      const idToken = await nextUser.getIdToken();
      sessionStorage.setItem("securecode_id_token", idToken);
      setToken(idToken);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      if (!firebaseAuth.currentUser) {
        return;
      }
      try {
        const refreshed = await firebaseAuth.currentUser.getIdToken(true);
        setToken(refreshed);
        sessionStorage.setItem("securecode_id_token", refreshed);
      } catch {
        // refresh will naturally retry on next cycle
      }
    }, 50 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    setAuthTokenProvider(async () => {
      if (firebaseAuth.currentUser) {
        try {
          const latest = await firebaseAuth.currentUser.getIdToken();
          setToken(latest);
          sessionStorage.setItem("securecode_id_token", latest);
          return latest;
        } catch {
          return token || "";
        }
      }
      return token || "";
    });
  }, [token]);

  const login = async (email, password) => {
    const credential = await signInWithEmailAndPassword(firebaseAuth, email, password);
    const idToken = await credential.user.getIdToken();
    setToken(idToken);
    sessionStorage.setItem("securecode_id_token", idToken);
    return credential.user;
  };

  const signup = async (email, password) => {
    const credential = await createUserWithEmailAndPassword(firebaseAuth, email, password);
    const idToken = await credential.user.getIdToken();
    setToken(idToken);
    sessionStorage.setItem("securecode_id_token", idToken);
    return credential.user;
  };

  const logout = async () => {
    await signOut(firebaseAuth);
    setToken("");
    sessionStorage.removeItem("securecode_id_token");
    setUser(null);
  };

  const refreshToken = async () => {
    if (!firebaseAuth.currentUser) return "";
    const refreshed = await firebaseAuth.currentUser.getIdToken(true);
    setToken(refreshed);
    sessionStorage.setItem("securecode_id_token", refreshed);
    return refreshed;
  };

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      login,
      signup,
      logout,
      refreshToken,
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
