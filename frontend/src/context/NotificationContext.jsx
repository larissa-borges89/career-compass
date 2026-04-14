import { createContext, useContext, useState, useCallback } from 'react';
import { Snackbar, Alert } from '@mui/material';

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const [notification, setNotification] = useState(null);

  const notify = useCallback((message, severity = 'info') => {
    setNotification({ message, severity });
  }, []);

  const success = useCallback((msg) => notify(msg, 'success'), [notify]);
  const error   = useCallback((msg) => notify(msg, 'error'),   [notify]);
  const warning = useCallback((msg) => notify(msg, 'warning'), [notify]);
  const info    = useCallback((msg) => notify(msg, 'info'),    [notify]);

  const handleClose = () => setNotification(null);

  return (
    <NotificationContext.Provider value={{ notify, success, error, warning, info }}>
      {children}
      <Snackbar
        open={!!notification}
        autoHideDuration={4000}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        {notification && (
          <Alert onClose={handleClose} severity={notification.severity} variant="filled" sx={{ width: '100%' }}>
            {notification.message}
          </Alert>
        )}
      </Snackbar>
    </NotificationContext.Provider>
  );
}

export const useNotification = () => useContext(NotificationContext);
