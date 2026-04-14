import { useEffect, useState } from 'react';
import {
  Box, Grid, Card, CardContent, CardActions, Typography, Chip, Button,
  CircularProgress, TextField, Slider, Accordion, AccordionSummary,
  AccordionDetails, Alert, Divider, LinearProgress
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SearchIcon from '@mui/icons-material/Search';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { getJobs, searchJobs, applyToJob, getApplications } from '../services/api';
import { useNotification } from '../context/NotificationContext';

const VERDICT_COLOR = {
  strong_match: 'success',
  good_match: 'warning',
  weak_match: 'default',
  no_match: 'error',
};

const VERDICT_LABEL = {
  strong_match: 'Strong Match',
  good_match: 'Good Match',
  weak_match: 'Weak Match',
  no_match: 'No Match',
};

function JobCard({ job, onApply, savedIds, onSaved, onNotify }) {
  const [loading, setLoading] = useState(false);
  const applied = savedIds.has(job.id);
  const score = Math.round(job.match_score || 0);
  const matchingSkills = typeof job.matching_skills === 'string'
    ? JSON.parse(job.matching_skills || '[]')
    : job.matching_skills || [];
  const missingSkills = typeof job.missing_skills === 'string'
    ? JSON.parse(job.missing_skills || '[]')
    : job.missing_skills || [];

  const handleApply = async () => {
    setLoading(true);
    try {
      await applyToJob(job.id);
      onSaved(job.id);
      onNotify('success', `"${job.title}" added to your tracker!`);
    } catch (e) {
      onNotify('error', e.friendlyMessage || 'Failed to add to tracker.');
    }
    setLoading(false);
  };

  return (
    <Card sx={{ borderRadius: 3, boxShadow: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
          <Box flex={1} pr={1}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>{job.title}</Typography>
            <Typography variant="body2" color="text.secondary">{job.company}</Typography>
            <Typography variant="caption" color="text.disabled">📍 {job.location}</Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="h4" fontWeight="bold"
              color={score >= 80 ? 'success.main' : score >= 60 ? 'warning.main' : 'text.secondary'}>
              {score}
            </Typography>
            <Typography variant="caption" color="text.secondary">/ 100</Typography>
          </Box>
        </Box>

        {/* Score Bar */}
        <LinearProgress
          variant="determinate"
          value={score}
          color={score >= 80 ? 'success' : score >= 60 ? 'warning' : 'inherit'}
          sx={{ borderRadius: 2, mb: 1.5, height: 6 }}
        />

        {/* Verdict */}
        <Box display="flex" gap={1} mb={1.5} flexWrap="wrap">
          <Chip
            label={VERDICT_LABEL[job.match_verdict] || job.match_verdict}
            color={VERDICT_COLOR[job.match_verdict] || 'default'}
            size="small"
            icon={<TrendingUpIcon />}
          />
          {job.source && <Chip label={job.source === 'adzuna' ? 'Adzuna' : 'Google Jobs'} size="small" variant="outlined" />}
          {job.date_posted && <Chip label={job.date_posted} size="small" variant="outlined" />}
        </Box>

        {/* Reason */}
        <Typography variant="body2" color="text.secondary" mb={1.5}>
          {job.match_reason}
        </Typography>

        {/* Skills */}
        {matchingSkills.length > 0 && (
          <Box mb={1}>
            <Typography variant="caption" color="success.main" fontWeight="bold">✅ Matching:</Typography>
            <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
              {matchingSkills.slice(0, 5).map(skill => (
                <Chip key={skill} label={skill} size="small" color="success" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {missingSkills.length > 0 && (
          <Box mb={1}>
            <Typography variant="caption" color="error.main" fontWeight="bold">⚠️ Missing:</Typography>
            <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
              {missingSkills.slice(0, 3).map(skill => (
                <Chip key={skill} label={skill} size="small" color="error" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {/* Description */}
        {job.description && (
          <Accordion elevation={0} sx={{ mt: 1, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="caption" fontWeight="bold">View Description</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" color="text.secondary">{job.description}</Typography>
            </AccordionDetails>
          </Accordion>
        )}
      </CardContent>

      <CardActions sx={{ p: 2, pt: 0, gap: 1 }}>
        <Button
          variant="contained"
          size="small"
          fullWidth
          onClick={handleApply}
          disabled={applied || loading}
          color={applied ? 'success' : 'primary'}
          startIcon={applied ? <CheckCircleIcon /> : null}
        >
          {loading ? <CircularProgress size={16} /> : applied ? 'Saved to Tracker' : 'Add to Tracker'}
        </Button>
        {job.url && (
          <Button
            variant="outlined"
            size="small"
            href={job.url}
            target="_blank"
            endIcon={<OpenInNewIcon />}
          >
            Apply
          </Button>
        )}
      </CardActions>
    </Card>
  );
}

export default function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [location, setLocation] = useState('New York');
  const [maxDays, setMaxDays] = useState(2);
  const [minScore, setMinScore] = useState(60);
  const [message, setMessage] = useState('');
  const [savedIds, setSavedIds] = useState(new Set());
  const { success, error: notifyError, info } = useNotification();

  const handleSaved = (id) => setSavedIds(prev => new Set([...prev, id]));

  const loadJobs = async () => {
    setLoading(true);
    try {
      const [jobsRes, appsRes] = await Promise.all([getJobs(), getApplications()]);
      const jobs = jobsRes.data;
      const apps = appsRes.data;

      const savedSet = new Set();
      jobs.forEach(job => {
        const alreadySaved = apps.some(
          app => app.company === job.company && app.role === job.title
        );
        if (alreadySaved) savedSet.add(job.id);
      });

      setJobs(jobs);
      setSavedIds(savedSet);
    } catch (e) {
      notifyError(e.friendlyMessage || 'Failed to load jobs.');
    }
    setLoading(false);
  };

  useEffect(() => { loadJobs(); }, []);

  const handleSearch = async () => {
    setSearching(true);
    setMessage('');
    try {
      const res = await searchJobs({ location, max_days: maxDays, min_score: minScore });
      setJobs(res.data.jobs || []);
      const msg = `Found ${res.data.found} matches using keywords: ${res.data.keywords?.join(', ')}`;
      setMessage(msg);
      info(msg);
    } catch (e) {
      const msg = e.friendlyMessage || 'Error searching jobs. Make sure your resume is uploaded.';
      setMessage(msg);
      notifyError(msg);
    }
    setSearching(false);
  };

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight="bold" gutterBottom>🔍 Job Search</Typography>

      {/* Search Panel */}
      <Card sx={{ borderRadius: 3, mb: 3, p: 2 }}>
        <Typography variant="h6" gutterBottom>Search Settings</Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <TextField
              label="Location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              fullWidth
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Typography variant="caption" color="text.secondary">
              Max job age: {maxDays} day{maxDays > 1 ? 's' : ''}
            </Typography>
            <Slider value={maxDays} onChange={(_, v) => setMaxDays(v)} min={1} max={14} step={1} size="small" />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Typography variant="caption" color="text.secondary">
              Min match score: {minScore}%
            </Typography>
            <Slider value={minScore} onChange={(_, v) => setMinScore(v)} min={40} max={90} step={5} size="small" />
          </Grid>
          <Grid item xs={12} sm={2}>
            <Button
              variant="contained"
              fullWidth
              startIcon={searching ? <CircularProgress size={16} color="inherit" /> : <SearchIcon />}
              onClick={handleSearch}
              disabled={searching}
            >
              {searching ? 'Searching...' : 'Search'}
            </Button>
          </Grid>
        </Grid>
        {message && <Alert severity="info" sx={{ mt: 2 }}>{message}</Alert>}
      </Card>

      {/* Jobs Grid */}
      {loading || searching ? (
        <Box display="flex" justifyContent="center" mt={6}>
          <CircularProgress />
        </Box>
      ) : jobs.length === 0 ? (
        <Box textAlign="center" mt={6}>
          <Typography color="text.secondary">No jobs yet. Click Search to find matching opportunities!</Typography>
        </Box>
      ) : (
        <>
          <Typography variant="body2" color="text.secondary" mb={2}>
            {jobs.length} job{jobs.length !== 1 ? 's' : ''} found — sorted by match score
          </Typography>
          <Grid container spacing={2}>
            {jobs.map(job => (
              <Grid item xs={12} sm={6} md={4} key={job.id}>
                <JobCard job={job} savedIds={savedIds} onSaved={handleSaved} onNotify={(sev, msg) => sev === 'success' ? success(msg) : notifyError(msg)} />
              </Grid>
            ))}
          </Grid>
        </>
      )}
    </Box>
  );
}
