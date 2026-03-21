import { useState, useCallback } from 'react';

const STORAGE_KEY = 'torn_api_key';
const VALIDATE_URL = (key) =>
  `https://api.torn.com/user/?selections=basic&key=${key}`;

export function useApiKey() {
  const [apiKey, setApiKeyState] = useState(
    () => localStorage.getItem(STORAGE_KEY) || ''
  );
  const [validating, setValidating] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [playerInfo, setPlayerInfo] = useState(null);

  const saveKey = useCallback((key) => {
    localStorage.setItem(STORAGE_KEY, key);
    setApiKeyState(key);
  }, []);

  const clearKey = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setApiKeyState('');
    setPlayerInfo(null);
    setValidationError('');
  }, []);

  const validateKey = useCallback(async (key) => {
    if (!key || key.trim().length < 8) {
      setValidationError('API key must be at least 8 characters.');
      return false;
    }
    setValidating(true);
    setValidationError('');
    try {
      const res = await fetch(VALIDATE_URL(key.trim()));
      const data = await res.json();
      if (data.error) {
        setValidationError(`API error: ${data.error.error}`);
        setValidating(false);
        return false;
      }
      setPlayerInfo({ name: data.name, level: data.level });
      saveKey(key.trim());
      setValidating(false);
      return true;
    } catch {
      setValidationError('Network error — check your connection.');
      setValidating(false);
      return false;
    }
  }, [saveKey]);

  return {
    apiKey,
    playerInfo,
    validating,
    validationError,
    validateKey,
    clearKey,
    isSet: Boolean(apiKey),
  };
}
