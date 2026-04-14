import { useState, useCallback } from 'react';
import {
  Box, Card, CardContent, Typography, Button, CircularProgress,
  Alert, Chip, Divider, LinearProgress, List, ListItem, ListItemText
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PersonIcon from '@mui/icons-material/Person';
import { uploadResume, getProfile } from '../services/api';

export default function Resume() {
  const [profile, setProfile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [message, setMessage] = useState(null); // { type: 'success'|'error', text: '' }
  const [dragging, setDragging] = useState(false);

  const loadProfile = async () => {
    setLoadingProfile(true);
    try {
      const res = await getProfile();
      setProfile(res.data);
    } catch {
      setProfile(null);
    }
    setLoadingProfile(false);
  };

  const handleFile = async (file) => {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx'].includes(ext)) {
      setMessage({ type: 'error', text: 'Only PDF and DOCX files are supported.' });
      return;
    }
    setUploading(true);
    setMessage(null);
    try {
      await uploadResume(file);
      setMessage({ type: 'success', text: `✅ "${file.name}" uploaded successfully! Loading your profile...` });
      await loadProfile();
    } catch (e) {
      setMessage({ type: 'error', text: 'Upload failed. Please try again.' });
    }
    setUploading(false);
  };

  const handleInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }, []);

  const handleDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const handleDragLeave = () => setDragging(false);

  return (
    <Box p={3} maxWidth={800} mx="auto">
      <Typography variant="h4" fontWeight="bold" gutterBottom>📄 Resume</Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Upload your resume so Career Compass can find jobs that match your skills.
        Supports PDF and DOCX. Your profile is parsed by AI and cached — no extra API calls on re-uploads.
      </Typography>

      {/* Upload Area */}
      <Card
        sx={{
          borderRadius: 3, mb: 3, border: '2px dashed',
          borderColor: dragging ? 'primary.main' : 'divider',
          bgcolor: dragging ? 'primary.50' : 'background.paper',
          transition: '0.2s',
          cursor: 'pointer',
        }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => document.getElementById('resume-input').click()}
      >
        <CardContent sx={{ textAlign: 'center', py: 5 }}>
          {uploading ? (
            <>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography color="text.secondary">Uploading and parsing resume…</Typography>
            </>
          ) : (
            <>
              <UploadFileIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" gutterBottom>Drop your resume here</Typography>
              <Typography variant="body2" color="text.secondary">or click to browse</Typography>
              <Typography variant="caption" color="text.disabled" display="block" mt={1}>
                PDF or DOCX · Max 10MB
              </Typography>
            </>
          )}
        </CardContent>
      </Card>

      <input
        id="resume-input"
        type="file"
        accept=".pdf,.docx"
        style={{ display: 'none' }}
        onChange={handleInputChange}
      />

      {message && (
        <Alert severity={message.type} sx={{ mb: 3, borderRadius: 2 }}>
          {message.text}
        </Alert>
      )}

      {/* Load Profile Button */}
      {!profile && !uploading && (
        <Button
          variant="outlined"
          startIcon={loadingProfile ? <CircularProgress size={16} /> : <PersonIcon />}
          onClick={loadProfile}
          disabled={loadingProfile}
          sx={{ mb: 3 }}
        >
          {loadingProfile ? 'Loading...' : 'Load Existing Profile'}
        </Button>
      )}

      {/* Profile Display */}
      {profile && (
        <Card sx={{ borderRadius: 3, boxShadow: 2 }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <CheckCircleIcon color="success" />
              <Typography variant="h6" fontWeight="bold">Parsed Profile</Typography>
            </Box>

            {profile.name && (
              <Typography variant="h5" fontWeight="bold" gutterBottom>{profile.name}</Typography>
            )}
            {profile.email && (
              <Typography variant="body2" color="text.secondary">{profile.email}</Typography>
            )}
            {profile.title && (
              <Typography variant="body2" color="primary" fontWeight="bold" mb={2}>{profile.title}</Typography>
            )}

            <Divider sx={{ my: 2 }} />

            {/* Skills */}
            {profile.skills?.length > 0 && (
              <Box mb={2}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>🛠 Skills</Typography>
                <Box display="flex" flexWrap="wrap" gap={0.5}>
                  {profile.skills.map(skill => (
                    <Chip key={skill} label={skill} size="small" variant="outlined" color="primary" />
                  ))}
                </Box>
              </Box>
            )}

            {/* Experience */}
            {profile.experience?.length > 0 && (
              <Box mb={2}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>💼 Experience</Typography>
                <List dense disablePadding>
                  {profile.experience.slice(0, 5).map((exp, i) => (
                    <ListItem key={i} disableGutters>
                      <ListItemText
                        primary={typeof exp === 'string' ? exp : `${exp.title} @ ${exp.company}`}
                        primaryTypographyProps={{ variant: 'body2' }}
                        secondary={typeof exp === 'object' ? exp.duration : null}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {/* Education */}
            {profile.education?.length > 0 && (
              <Box>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>🎓 Education</Typography>
                <List dense disablePadding>
                  {profile.education.map((edu, i) => (
                    <ListItem key={i} disableGutters>
                      <ListItemText
                        primary={typeof edu === 'string' ? edu : `${edu.degree} — ${edu.institution}`}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {/* Match score indicator */}
            {profile.years_experience && (
              <>
                <Divider sx={{ my: 2 }} />
                <Box display="flex" alignItems="center" gap={2}>
                  <Box flex={1}>
                    <Typography variant="caption" color="text.secondary">
                      Experience level: {profile.years_experience} years
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min((profile.years_experience / 15) * 100, 100)}
                      sx={{ height: 6, borderRadius: 2, mt: 0.5 }}
                    />
                  </Box>
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
