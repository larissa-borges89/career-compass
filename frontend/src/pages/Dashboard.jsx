import { useEffect, useState } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Chip, CircularProgress,
  LinearProgress, IconButton, Tooltip, Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import WorkIcon from '@mui/icons-material/Work';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ScheduleIcon from '@mui/icons-material/Schedule';
import CancelIcon from '@mui/icons-material/Cancel';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import EditIcon from '@mui/icons-material/Edit';
import { getApplications, getStats, updateApplication } from '../services/api';

const STATUS_COLORS = {
  applied: 'primary',
  interview_scheduled: 'warning',
  offer: 'success',
  rejected: 'error',
};

const STATUS_LABELS = {
  applied: 'Applied',
  interview_scheduled: 'Interview',
  offer: 'Offer',
  rejected: 'Rejected',
};

const STATUS_ICONS = {
  applied: <WorkIcon fontSize="small" />,
  interview_scheduled: <ScheduleIcon fontSize="small" />,
  offer: <CheckCircleIcon fontSize="small" />,
  rejected: <CancelIcon fontSize="small" />,
};

function StatCard({ title, value, color, icon }) {
  return (
    <Card sx={{ borderRadius: 3, boxShadow: 2 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="body2" color="text.secondary">{title}</Typography>
            <Typography variant="h4" fontWeight="bold" color={color}>{value}</Typography>
          </Box>
          <Box sx={{ color, opacity: 0.8, fontSize: 40 }}>{icon}</Box>
        </Box>
      </CardContent>
    </Card>
  );
}

function ApplicationCard({ app, onStatusUpdate }) {
  const [editing, setEditing] = useState(false);
  const [status, setStatus] = useState(app.status);

  const handleStatusChange = async (newStatus) => {
    setStatus(newStatus);
    setEditing(false);
    await updateApplication(app.id, { status: newStatus });
    onStatusUpdate();
  };

  return (
    <Card sx={{ borderRadius: 3, boxShadow: 1, '&:hover': { boxShadow: 3 }, transition: '0.2s' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box flex={1}>
            <Typography variant="h6" fontWeight="bold" noWrap>{app.role}</Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>{app.company}</Typography>
            {app.location && (
              <Typography variant="caption" color="text.secondary">📍 {app.location}</Typography>
            )}
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            {app.match_score > 0 && (
              <Chip
                label={`${Math.round(app.match_score)}%`}
                size="small"
                color={app.match_score >= 80 ? 'success' : app.match_score >= 60 ? 'warning' : 'default'}
                icon={<TrendingUpIcon />}
              />
            )}
            <Tooltip title="Change status">
              <IconButton size="small" onClick={() => setEditing(!editing)}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {editing ? (
          <FormControl size="small" fullWidth sx={{ mt: 1 }}>
            <InputLabel>Status</InputLabel>
            <Select value={status} label="Status" onChange={(e) => handleStatusChange(e.target.value)}>
              {Object.entries(STATUS_LABELS).map(([key, label]) => (
                <MenuItem key={key} value={key}>{label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        ) : (
          <Box mt={1}>
            <Chip
              icon={STATUS_ICONS[status]}
              label={STATUS_LABELS[status] || status}
              color={STATUS_COLORS[status] || 'default'}
              size="small"
            />
          </Box>
        )}

        {app.match_reason && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {app.match_reason}
          </Typography>
        )}

        <Typography variant="caption" color="text.disabled" sx={{ mt: 0.5, display: 'block' }}>
          {app.created_at ? new Date(app.created_at).toLocaleDateString() : ''}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [apps, setApps] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const loadData = async () => {
    setLoading(true);
    try {
      const [appsRes, statsRes] = await Promise.all([getApplications(), getStats()]);
      setApps(appsRes.data);
      setStats(statsRes.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const filtered = filter === 'all' ? apps : apps.filter(a => a.status === filter);

  if (loading) return <Box display="flex" justifyContent="center" mt={10}><CircularProgress /></Box>;

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight="bold" gutterBottom>🧭 My Applications</Typography>

      {/* Stats */}
      {stats && (
        <Grid container spacing={2} mb={3}>
          <Grid item xs={6} sm={3}>
            <StatCard title="Total" value={stats.total} color="primary.main" icon={<WorkIcon />} />
          </Grid>
          <Grid item xs={6} sm={3}>
            <StatCard title="Interviews" value={stats.by_status?.interview_scheduled || 0} color="warning.main" icon={<ScheduleIcon />} />
          </Grid>
          <Grid item xs={6} sm={3}>
            <StatCard title="Offers" value={stats.by_status?.offer || 0} color="success.main" icon={<CheckCircleIcon />} />
          </Grid>
          <Grid item xs={6} sm={3}>
            <StatCard title="Response Rate" value={`${stats.response_rate}%`} color="info.main" icon={<TrendingUpIcon />} />
          </Grid>
        </Grid>
      )}

      {/* Filter */}
      <Box display="flex" gap={1} mb={2} flexWrap="wrap">
        {['all', 'applied', 'interview_scheduled', 'offer', 'rejected'].map(s => (
          <Chip
            key={s}
            label={s === 'all' ? 'All' : STATUS_LABELS[s]}
            onClick={() => setFilter(s)}
            color={filter === s ? 'primary' : 'default'}
            variant={filter === s ? 'filled' : 'outlined'}
          />
        ))}
      </Box>

      {/* Applications Grid */}
      {filtered.length === 0 ? (
        <Box textAlign="center" mt={6}>
          <Typography color="text.secondary">No applications yet. Start by searching for jobs!</Typography>
        </Box>
      ) : (
        <Grid container spacing={2}>
          {filtered.map(app => (
            <Grid item xs={12} sm={6} md={4} key={app.id}>
              <ApplicationCard app={app} onStatusUpdate={loadData} />
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}
