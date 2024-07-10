import React, { useState } from 'react';
import { Container, Typography, TextField, Button, CircularProgress, Alert } from '@mui/material';
import axios from 'axios';
import { ThemeProvider, createTheme } from '@mui/material/styles';
function App() {
  const [youtubeLink, setYoutubeLink] = useState('');
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
 

  const handleGoToYouTube = () => {
    const youtubeMainURL = 'https://www.youtube.com/';
    window.open(youtubeMainURL, '_blank'); // Open YouTube main page in a new tab
  };
  

  const outerTheme = createTheme({
    palette: {
        primary: {
            dark: '#0D1B3A',
            main: '#0D1B2A'
        },
        secondary: {
            main: '#FF0001',
        },
    },
});
  const handleGenerateSummary = async () => {
    setLoading(true);
    setError('');
    setSummary('');
    try {
      const response = await axios.post('http://localhost:8000/generate-summary', { youtube_link: youtubeLink });
      setSummary(response.data.summary);
    } catch (err) {
      setError('Failed to generate summary.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadSummary = () => {
    const element = document.createElement("a");
    const file = new Blob([summary], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = "summary.txt";
    document.body.appendChild(element);
    element.click();
  };

  

  return (
    <ThemeProvider theme={outerTheme}>
    <Container maxWidth="md" style={{ marginTop: '2rem' }}>
      <Typography variant="h4" gutterBottom>
        YouTube Video Summary Generator
      </Typography>
      <Button
  variant="contained"
  color="secondary"
  onClick={handleGoToYouTube}
  // disabled={!youtubeLink}
>
  Go to YouTube
</Button>
      
      <TextField
        label="Enter YouTube Link"
        variant="outlined"
        fullWidth
        value={youtubeLink}
        onChange={(e) => setYoutubeLink(e.target.value)}
        style={{ marginBottom: '1rem' ,marginTop: '23px'}}
      />
      <Button
        variant="contained"
        color="primary"
        onClick={handleGenerateSummary}
        disabled={loading || !youtubeLink}
        style={{ marginRight: '1rem' }}
      >
        {loading ? <CircularProgress size={24} /> : 'Generate Summary'}
      </Button>
    
      {error && <Alert severity="error" style={{ marginTop: '1rem' }}>{error}</Alert>}
      {summary && (
        <div style={{ marginTop: '2rem' }}>
          <Typography variant="h6">Summary:</Typography>
          <Typography variant="body1" style={{ whiteSpace: 'pre-line', marginBottom: '1rem' }}>
            {summary}
          </Typography>
          <Button variant="contained" color="primary" onClick={handleDownloadSummary}>
            Download Summary
          </Button>
        </div>
      )}
    </Container>
    </ThemeProvider>
  );
}

export default App;
