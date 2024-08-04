'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';

const Load = () => {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState('');

  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    const token = queryParams.get('token');

    if (token) {
      console.log("Token from URL:", token);
      setAccessToken(token);
      localStorage.setItem('spotify_access_token', token);
      postTokenActions(token);
    } else {
      console.error("Token is missing from the URL");
      router.push('/login');
    }
  }, [router]);

  const postTokenActions = (token) => {
    validateTokenAndFetchUser(token);
  };

  const validateTokenAndFetchUser = async (token) => {
    try {
      const response = await axios.get('https://api.spotify.com/v1/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        }
      });

      const userName = response.data.display_name;
      console.log("Fetched User Name:", userName);

      computeMoodScores(token);  // Trigger mood score computation
      console.log("Mood Score calculations started");

      router.push(`/welcome?name=${encodeURIComponent(userName)}&token=${token}`);
    } 

    catch (error) {
      console.error("Failed to fetch user profile or validate token:", error);
      router.push('/login');
    }
  };

  const computeMoodScores = async (token) => {
    try {
      await axios.post('https://songsyncbackend-production.up.railway.app/compute-mood-scores', {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      console.log("Mood score computation initiated.");
    } catch (error) {
      console.error("Failed to initiate mood score computation:", error);
    }
  };

  return (
    <div className="loading-container">
      {accessToken ? <div className="loading">Loading your experience...</div> : <div>Token not found, redirecting...</div>}
    </div>
  );
};

export default Load;