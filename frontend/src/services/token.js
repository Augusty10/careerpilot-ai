/**
 * Token management helper for CareerPilot AI.
 * Stores JWT in-memory with localStorage persistence for current sessions.
 * Encapsulated in this single module so authentication storage can easily be
 * swapped for httpOnly cookies in future security hardening phases.
 */

const TOKEN_KEY = 'careerpilot_auth_token';

let inMemoryToken = null;

export const tokenStorage = {
  getToken: () => {
    if (inMemoryToken) {
      return inMemoryToken;
    }
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      inMemoryToken = stored;
    }
    return inMemoryToken;
  },

  setToken: (token) => {
    inMemoryToken = token;
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  },

  removeToken: () => {
    inMemoryToken = null;
    localStorage.removeItem(TOKEN_KEY);
  },

  hasToken: () => {
    return Boolean(tokenStorage.getToken());
  }
};

export default tokenStorage;

