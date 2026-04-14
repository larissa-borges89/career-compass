import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Button, Box, IconButton,
  Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText,
  useMediaQuery, useTheme, Chip
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SearchIcon from '@mui/icons-material/Search';
import DescriptionIcon from '@mui/icons-material/Description';
import MenuIcon from '@mui/icons-material/Menu';
import CompassIcon from '@mui/icons-material/Explore';

const NAV_ITEMS = [
  { label: 'My Applications', path: '/dashboard', icon: <DashboardIcon /> },
  { label: 'Job Search', path: '/jobs', icon: <SearchIcon /> },
  { label: 'Resume', path: '/resume', icon: <DescriptionIcon /> },
];

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [drawerOpen, setDrawerOpen] = useState(false);

  const isActive = (path) => location.pathname === path;

  const handleNav = (path) => {
    navigate(path);
    setDrawerOpen(false);
  };

  return (
    <>
      <AppBar position="sticky" elevation={0} sx={{ bgcolor: 'white', borderBottom: '1px solid', borderColor: 'divider' }}>
        <Toolbar>
          {/* Logo */}
          <Box
            display="flex" alignItems="center" gap={1} mr={4}
            sx={{ cursor: 'pointer' }}
            onClick={() => handleNav('/dashboard')}
          >
            <CompassIcon sx={{ color: 'primary.main', fontSize: 28 }} />
            <Typography variant="h6" fontWeight="bold" color="primary.main">
              Career Compass
            </Typography>
            <Chip label="beta" size="small" color="primary" variant="outlined" sx={{ height: 18, fontSize: 10 }} />
          </Box>

          {isMobile ? (
            <>
              <Box flex={1} />
              <IconButton onClick={() => setDrawerOpen(true)} sx={{ color: 'text.primary' }}>
                <MenuIcon />
              </IconButton>
            </>
          ) : (
            <Box display="flex" gap={1}>
              {NAV_ITEMS.map(item => (
                <Button
                  key={item.path}
                  startIcon={item.icon}
                  onClick={() => handleNav(item.path)}
                  variant={isActive(item.path) ? 'contained' : 'outlined'}
                  color="primary"
                  sx={{
                    borderRadius: 2,
                    textTransform: 'none',
                    fontWeight: isActive(item.path) ? 'bold' : 'normal',
                    opacity: isActive(item.path) ? 1 : 0.75,
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer anchor="right" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <Box width={240} pt={2}>
          <Box px={2} pb={2} display="flex" alignItems="center" gap={1}>
            <CompassIcon color="primary" />
            <Typography fontWeight="bold" color="primary">Career Compass</Typography>
          </Box>
          <List>
            {NAV_ITEMS.map(item => (
              <ListItem key={item.path} disablePadding>
                <ListItemButton
                  selected={isActive(item.path)}
                  onClick={() => handleNav(item.path)}
                  sx={{ borderRadius: 2, mx: 1 }}
                >
                  <ListItemIcon sx={{ color: isActive(item.path) ? 'primary.main' : 'inherit' }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
    </>
  );
}
