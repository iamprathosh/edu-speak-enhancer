import { useState, useEffect, useCallback } from 'react';
import { getApiUrl, handleApiError } from '../services/backendConfig'; // Import API config

interface User {
  username: string;
  history_count?: number; // Optional based on /api/me response
}

interface LoginCredentials {
  username: string;
  password: string;
}

interface RegisterCredentials {
  username: string;
  password: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<boolean>;
  loading: boolean; // General loading state for auth operations
  authChecked: boolean; // To know if initial auth check is done
  error: string | null;
}

export const useAuth = (): AuthContextType => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(false); // For specific actions like login/register/logout
  const [authChecked, setAuthChecked] = useState<boolean>(false); // Tracks if initial session check is done
  const [error, setError] = useState<string | null>(null);

  const checkSession = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(getApiUrl('/api/me'), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important for session cookies
      });
      if (response.ok) {
        const data = await response.json();
        setUser({ username: data.username, history_count: data.history_count });
      } else {
        setUser(null);
        if (response.status !== 401) { // Don't set error for "not logged in"
          const errorData = await response.json().catch(() => null);
          setError(errorData?.error || `Session check failed: ${response.statusText}`);
        }
      }
    } catch (e: any) {
      setUser(null);
      const specificError = handleApiError(e);
      setError(specificError.message || 'Failed to connect to server for session check.');
      console.error("Check session error:", specificError);
    } finally {
      setLoading(false);
      setAuthChecked(true);
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  const login = useCallback(async (credentials: LoginCredentials): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(getApiUrl('/api/login'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(credentials),
      });
      const data = await response.json();
      if (response.ok) {
        setUser({ username: data.user.username });
        return true;
      } else {
        setError(data.error || 'Login failed.');
        return false;
      }
    } catch (e: any) {
      const specificError = handleApiError(e);
      setError(specificError.message || 'Login request failed.');
      console.error("Login error:", specificError);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(getApiUrl('/api/logout'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      if (response.ok) {
        setUser(null);
      } else {
        const data = await response.json().catch(() => null);
        setError(data?.error || 'Logout failed.');
      }
    } catch (e: any) {
      const specificError = handleApiError(e);
      setError(specificError.message || 'Logout request failed.');
      console.error("Logout error:", specificError);
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (credentials: RegisterCredentials): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(getApiUrl('/api/register'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Though not strictly necessary for register, good practice
        body: JSON.stringify(credentials),
      });
      const data = await response.json();
      if (response.ok) {
        // User registered, typically they would login next.
        // You could auto-login here or set a success message.
        // For now, just return true.
        setUser({ username: data.user.username }); // Set user on successful registration
        return true;
      } else {
        setError(data.error || 'Registration failed.');
        return false;
      }
    } catch (e: any) {
      const specificError = handleApiError(e);
      setError(specificError.message || 'Registration request failed.');
      console.error("Register error:", specificError);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    register,
    loading,
    authChecked,
    error,
  };
};
