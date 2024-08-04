'use client';
import React, { useState } from 'react';
import Head from 'next/head';

const Login = () => {
  const [showModal, setShowModal] = useState(false);

  const handleLogin = () => {
    window.location.href = "https://songsyncbackend-production.up.railway.app/login";
  };

  const toggleModal = () => {
    setShowModal(!showModal);
  };

  return (
    <div className="container glowing-background2">
      <Head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="SongSync" content="Mood Playlist Generator" />
        <link rel="icon" href="public/favicon.ico" />
        <title>SongSync</title>
      </Head>

      <h1 className="title1">SongSync</h1>

      <p className="description-text">
        Struggling to find the perfect playlist that captures your mood and matches your music taste? 
        Tell us how you&apos;re feeling and based on your top five favorite artists, 
        SongSync will tailor a Spotify playlist precisely for you. 
      </p>

      <button onClick={handleLogin} className="button">Log in with SPOTIFY</button>

      <div className="absolute-top-right" onClick={toggleModal}>
        <a href="#" className="how-it-works">HOW IT WORKS</a>
      </div>

      <div className="absolute-bottom">
        <span>copyright, SongSync 2024</span>
      </div>

      {showModal && (
        <div className="modal-container">
          <div className="modal">
            <h2 className="text-2xl font-bold mb-4">How It Works!</h2>
            <p>Discover how SongSync crafts your personalized mood-based playlists.</p>
            <h3 className="text-xl font-semibold mt-4">1. Authentication</h3>
            <p>Log in with your Spotify account to let SongSync access your top artists and enable playlist creation directly on your profile.</p>
            <h3 className="text-xl font-semibold mt-4">2. Mood Selection</h3>
            <p>Select your mood to shape the playlist. SongSync uses advanced algorithms to match your mood with the perfect tracks from your favorite artists, analyzing factors like energy, tempo, and danceability.</p>
            <h3 className="text-xl font-semibold mt-4">3. Music Analysis and Selection</h3>
            <p>Based on your selected mood and top Spotify artists, SongSync computes mood scores for tracks to ensure they match your chosen vibe. Only the best-matching tracks are selected to curate your personalized playlist.</p>
            <h3 className="text-xl font-semibold mt-4">4. Playlist Creation</h3>
            <p>After selecting the best tracks, a new playlist is created under your Spotify account. SongSync also designs a custom playlist cover that visually represents the mood of your music, enhancing your listening experience.</p>
            <h3 className="text-xl font-semibold mt-4">5. Enjoy Your Music</h3>
            <p>Once the playlist is ready, you can immediately start listening through Spotify. Each playlist is unique, ensuring no two listening experiences are the same.</p>
            <h3 className="text-sm mt-4">Disclaimer:</h3>
            <p className="text-sm mt-4 italic"> The effectiveness of the mood matching can vary due to Spotify&apos;s categorization of tracks based on musical features.</p>
            <button onClick={toggleModal} className="close-button">Close</button>
          </div>
        </div>
      )}
      
    </div>
  );
};

export default Login;