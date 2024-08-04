'use client';

import React, { Suspense, useState, useEffect } from 'react';
import axios from 'axios';
import Link from 'next/link';

const GeneratePage = () => {
  const [playlistId, setPlaylistId] = useState('');
  const [topArtists, setTopArtists] = useState([]);
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [isPlaylistReady, setIsPlaylistReady] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const playlistIdParam = urlParams.get('playlist_id');
      setPlaylistId(playlistIdParam);
    }
  }, []);

  useEffect(() => {
    const checkMobileStatus = () => {
      if (typeof window !== 'undefined') {
        setIsMobile(window.innerWidth <= 500);
      }
    };

    window.addEventListener('resize', checkMobileStatus);
    return () => window.removeEventListener('resize', checkMobileStatus);
  }, []);

  // Function to fetch top artists and set playlist URL
  const fetchAndSetPlaylistUrl = async () => {
    try {
      const response = await axios.get('https://songsyncbackend-production.up.railway.app/get-top-artists', {
        withCredentials: true,
      });
      if (response.status === 200) {
        setTopArtists(response.data.top_artists);
      } else {
        console.error(`Failed to fetch top artists: ${response.status}`);
      }

      if (playlistId) {
        setPlaylistUrl(`https://open.spotify.com/playlist/${playlistId}`);
        setIsPlaylistReady(true);
      }
    } catch (error) {
      console.error("Error during fetching artists or setting playlist URL:", error);
    }
  };

  useEffect(() => {
    if (!hasFetched) {
      fetchAndSetPlaylistUrl();
      setHasFetched(true);
    }
  }, [hasFetched]);

  useEffect(() => {
    // Check if playlistId is set, then update isPlaylistReady
    if (playlistId) {
      setPlaylistUrl(`https://open.spotify.com/playlist/${playlistId}`);
      setIsPlaylistReady(true);
    }
  }, [playlistId]);

  return (
    <div className="container glowing-background">
      <Link href="/">
        <h1 className="title3 animate-title">SongSync</h1>
      </Link>
      <div className="syncMessageContainer">
        {!isPlaylistReady && (
          <>
            <h2 className="syncMessage animate-message">
              Your top 5 artists are synced!
            </h2>
            <h2 className="loading-container animate-message">
              <span className="loading-text">Loading....... <span className="spinner">🔄</span></span>
            </h2>
          </>
        )}
        {isPlaylistReady && (
          <div className="link-container">
            <a href={playlistUrl} target="_blank" rel="noopener noreferrer" className="playlist-link">
              OPEN Playlist!
            </a>
          </div>
        )}
      </div>

      <div className="artist-container">
        {topArtists.map((artist, index) => (
          <a href={isMobile ? null : artist.spotify_url} target="_blank" rel="noopener noreferrer" key={index} className="card-link">
            <div className="card animate-card" style={{ animationDelay: `${index * 0.5}s` }}>
              <img src={artist.image} alt={artist.name} className="background" />
              <div className="card-content">
                <h3 className="title">{artist.name}</h3>
              </div>
            </div>
          </a>
        ))}
      </div>

      <div className="absolute-bottom">
        <span>copyright, SongSync 2024</span>
      </div>
    </div>
  );
};

const WrappedGeneratePage = () => (
  <Suspense fallback={<div>Loading...</div>}>
    <GeneratePage />
  </Suspense>
);

export default WrappedGeneratePage;