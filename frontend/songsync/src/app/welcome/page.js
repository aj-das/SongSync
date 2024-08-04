'use client';

import React, { useState, Suspense, useEffect } from 'react';
import axios from 'axios';
import Link from 'next/link';
import Head from 'next/head';

const WelcomeComponent = () => {
  const [name, setName] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [selectedMood, setSelectedMood] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const nameParam = urlParams.get('name');
      setName(nameParam);

      const storedAccessToken = localStorage.getItem('spotify_access_token');
      if (storedAccessToken) {
        setAccessToken(storedAccessToken);
      } else {
        console.error("Access token not found in local storage");
        window.location.href = '/login';
      }
    }
  }, []);

  const handleButtonClick = (mood) => {
    setSelectedMood(mood);
    console.log("Mood Selected: ", mood);
  };

  const handleGenerate = async () => {
    setLoading(true); // sets loading to true when generate button is clicked

    console.log(`Sending request with token: ${accessToken} and mood: ${selectedMood}`);

    try {
      const response = await axios.post(
        `https://songsyncbackend-production.up.railway.app/generate-playlist?mood=${encodeURIComponent(selectedMood)}`,
        null,
        {
          headers: { Authorization: `Bearer ${accessToken}` },
        }
      );

      if (response.status === 200 && response.data.playlist_id) {
        const playlistId = response.data.playlist_id;
        console.log('Navigating to generate page with playlistId:', playlistId);

        window.location.href = `/generate?name=${encodeURIComponent(name)}&mood=${encodeURIComponent(selectedMood)}&playlist_id=${playlistId}`;
      } else {
        console.error('Failed to generate playlist:', response.statusText);
        alert('Failed to generate playlist: ' + response.statusText);
      }
    } catch (error) {
      console.error('API request failed:', error);
      alert('API request failed: ' + error.message);
    } finally {
      setLoading(false); // Set loading to false after request completes
    }
  };

  return (
    <div className="container glowing-background">
      <Head>
        <title>SongSync - Welcome</title>
      </Head>

      <Link href="/">
        <h1 className="title2">SongSync</h1>
      </Link>

      {name && (
        <h2 className="welcome">Logged in! Welcome, {decodeURIComponent(name)}!</h2>
      )}

      <h3 className="moodmessage">Choose a mood for your Playlist:</h3>
      <div className="flex flex-col space-y-4 align-center">
        <button className={`moodButton ${selectedMood === 'happy' ? 'selected' : ''}`} onClick={() => handleButtonClick('happy')}>HAPPY</button>
        <button className={`moodButton ${selectedMood === 'introspective' ? 'selected' : ''}`} onClick={() => handleButtonClick('introspective')}>INTROSPECTIVE</button>
        <button className={`moodButton ${selectedMood === 'relaxed' ? 'selected' : ''}`} onClick={() => handleButtonClick('relaxed')}>RELAXED</button>
        <button className={`moodButton ${selectedMood === 'energetic' ? 'selected' : ''}`} onClick={() => handleButtonClick('energetic')}>ENERGETIC</button>
      </div>
      <div>
        <button className="generateButton" onClick={handleGenerate} disabled={loading}>
          {loading ? 'Loading...' : 'GENERATE'}
        </button>
      </div>

      <div className="absolute-bottom">
        <span>copyright, SongSync 2024</span>
      </div>

    </div>
  );
};

const Welcome = () => (
  <Suspense fallback={<div>Loading...</div>}>
    <WelcomeComponent />
  </Suspense>
);

export default Welcome;