import logging
import random
import os
import datetime
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from fastapi.middleware.cors import CORSMiddleware

#load in enviorment variables
load_dotenv()

# get credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = "user-top-read playlist-modify-private user-read-private ugc-image-upload"

#SUPABASE Credentials
url: str = os.getenv("SUPABASE_URL")  # Supabase project URL
key: str = os.getenv("SUPABASE_KEY")  # Supabase service role key
supabase: Client = create_client(url, key)

# intialize the spotify oauth manager
sp_auth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
)

# intialize the client with the manager
sp = spotipy.Spotify(auth_manager=sp_auth)

app = FastAPI()

logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://songsync-git-main-aj-das-projects.vercel.app",
                   "https://songsync-aj-das-projects.vercel.app",
                   "https://songsync-official.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

 ## MOOD SCORE CALCULATIONS:
 ##Mood Map and Calculations
mood_adjectives = {
    "happy": ["Uplifting", "Sunny", "Bright"],
    "introspective": ["Reflective", "Deep", "Soulful"],
    "energetic": ["Powerful", "Pumping", "Vibrant"],
    "relaxed": ["Chill", "Mellow", "Smooth", "Calm"]
}

mood_map = {
    "energetic": {
        "energy": (0.6, 1.0),          # Lowered to include moderately high energy tracks
        "valence": (0.4, 1.0),         # Broad range to include less cheerful energetic tracks
        "danceability": (0.5, 1.0),    # Ensuring it captures rhythmic tracks
        "loudness": (-8.0, 0.0),       # Adjusted to include tracks that aren't extremely loud
        "tempo": (130, 200),           # Adjusted lower bound to capture the actual tempo
        "weights": {
            "energy": 4,               # Increased emphasis on energy
            "valence": 2,
            "danceability": 3,
            "loudness": 3,             # Greater emphasis on loudness
            "tempo": 5,                # High emphasis on tempo
            "key": 1
        }
    },

    "happy": {
        "energy": (0.4, 1.0),         # Broad range to include moderate to high energy
        "valence": (0.5, 1.0),        # Higher valence indicating positivity
        "danceability": (0.5, 1.0),   # High danceability as an important factor
        "loudness": (-10.0, 0.0),     # Including a wider range of loudness
        "tempo": (90, 160),           # Adjusted to include typical tempos for upbeat songs
        "weights": {
            "energy": 3,
            "valence": 5,             # Increased weight to valence as it strongly indicates mood
            "danceability": 4,
            "loudness": 2,
            "tempo": 3,
            "key": 1
        }
    },

    "introspective": {
        "energy": (0.0, 0.45),  # increased upper limit
        "valence": (0.0, 0.3),  # increased upper limit
        "danceability": (0.0, 0.5),  # increased upper limit
        "liveness": (0.0, 0.3),  # slightly increased
        "loudness": (-20.0, -10.0),  # increased upper limit
        "tempo": (60, 140),  # significantly increased upper limit
        "key": [1, 3, 6, 8, 10],
        "weights": {
            "energy": 2,  # slightly more weight
            "valence": 3,  # increased weight
            "danceability": 1,
            "liveness": 1,
            "loudness": 5,  # more emphasis on loudness
            "tempo": 3,
            "key": 5  # increased weight for key
        }
    },
    "relaxed": {
        "energy": (0.0, 0.7),  # increased upper limit
        "valence": (0.2, 0.6),  # increased upper limit
        "danceability": (0.0, 0.6),
        "liveness": (0.0, 0.5),
        "loudness": (-15.0, -5.0),  # increased upper limit
        "tempo": (70, 90),  # consider half-tempo adjustment in function
        "key": list(range(12)),  # Any key
        "weights": {
            "energy": 1,
            "valence": 3,
            "danceability": 2,
            "liveness": 2,
            "loudness": 4,
            "tempo": 4,
            "key": 1
        }
    }
}

@app.post("/compute-mood-scores")
async def compute_mood_scores(request: Request):
    access_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not access_token:
        raise HTTPException(status_code=403, detail="Access Token is missing from headers.")

    try:
        # Directly calling the function to compute mood scores
        fetch_and_compute_mood_scores(access_token)
        return JSONResponse(content={"message": "Mood score calculation completed"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute mood scores: {str(e)}")

def fetch_and_compute_mood_scores(access_token):
    sp = spotipy.Spotify(auth=access_token)
    top_artists = sp.current_user_top_artists(limit=5)['items']
    for artist in top_artists:
        compute_artist_mood_scores(artist['id'], artist['name'], sp)

def compute_artist_mood_scores(artist_id, artist_name, sp_client):

    # Check if mood scores for this artist are already computed and stored
    existing_scores = supabase.table("mood_scores").select("artist_id").eq("artist_id", artist_id).execute()

    # If scores exist, skip computation
    if existing_scores.data:
        logging.info(f"Mood scores already exist for artist: {artist_name}. Skipping re-computation.")
        return
    

    albums = sp_client.artist_albums(artist_id, album_type='album')['items']
    for album in albums:
        if is_album_recent(album['release_date']):
            unique_tracks = {}
            tracks = sp_client.album_tracks(album['id'])['items']
            for track in tracks:
                if track['name'] not in unique_tracks and is_track_eligible(track):
                    unique_tracks[track['name']] = track
            for track_name, track in unique_tracks.items():
                track_id = track['id']
                audio_features = sp_client.audio_features(track_id)[0]
                if audio_features:
                    mood, score = compute_best_mood_score(audio_features)
                    store_mood_score(track_id, track_name, artist_id, artist_name, album['name'], mood, score)

def is_album_recent(release_date):
    release_year = int(release_date[:4])
    current_year = datetime.datetime.now().year
    return current_year - release_year <= 5

def is_track_eligible(track):
    exclude_keywords = ["instrumental", "commentary", "remix", "interlude", "edit", "version", "acapella"]
    return not any(keyword in track['name'].lower() for keyword in exclude_keywords)

def compute_best_mood_score(audio_features):
    highest_score = float('-inf')
    best_mood = None
    for mood, criteria in mood_map.items():
        score = mood_score(audio_features, criteria)
        if score > highest_score:
            highest_score = score
            best_mood = mood
    return best_mood, highest_score

def store_mood_score(track_id, track_name, artist_id, artist_name, album_name, mood, score):
    if None not in [track_id, track_name, artist_id, artist_name, album_name, mood, score]:
        supabase.table("mood_scores").insert({
            "track_id": track_id,
            "track_name": track_name,
            "artist_id": artist_id,
            "artist_name": artist_name,
            "album_name": album_name,
            "mood": mood,
            "score": score,
            "computed_at": datetime.datetime.now().isoformat()
        }).execute()
    else:
        logging.error("Attempted to store incomplete mood score data.")


def mood_score(track, mood_criteria):
    total_score = 0
    total_weight = 0

    for feature, criteria in mood_criteria.items():
        if feature == "weights":
            continue  # Skip the weights dictionary

        feature_value = track.get(feature)
        weight = mood_criteria["weights"].get(feature, 1)  # Fetch the weight, defaulting to 1 if not specified

        if feature == 'key':
            # Binary match for key, score 1 if it matches, 0 otherwise
            score = 1 if feature_value in criteria else 0
        elif feature == 'tempo':
            # Handle tempo separately to account for half-tempo
            half_tempo = feature_value / 2
            score = any(min_val <= tempo <= max_val for tempo in (feature_value, half_tempo) for min_val, max_val in [criteria])
        else:
            # Standard scoring for other features
            min_val, max_val = criteria
            if min_val <= feature_value <= max_val:
                score = 1  # Perfect score if within the range
            else:
                # Penalize based on distance from the nearest bound, scaled by the range size
                if feature_value < min_val:
                    score = max(0, 1 - (min_val - feature_value) / (max_val - min_val))
                elif feature_value > max_val:
                    score = max(0, 1 - (feature_value - max_val) / (max_val - min_val))
                else:
                    score = 0  # Fallback case, though should not be necessary

        # Accumulate the weighted score
        total_score += score * weight
        total_weight += weight

    # Normalize the total score by the total weight
    return total_score / total_weight if total_weight > 0 else 0


#LOGIN
@app.get("/login")
def login():
    auth_url = sp_auth.get_authorize_url()
    return RedirectResponse(auth_url)

#CALLBACK, GET ACCESS TOKEN
@app.get("/callback")
def callback(code: str):
    try:
        token_info = sp_auth.get_access_token(code)
        access_token = token_info['access_token']
        response = RedirectResponse(url=f"https://songsync-git-main-aj-das-projects.vercel.app/load?token={access_token}")
        response.set_cookie(key="spotify_access_token", value=access_token, httponly=True)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#GET TOP 5 ARTISTS    
@app.get("/get-top-artists")
def get_top_artists():
    try:
        # Use the Spotipy client to get top artists
        results = sp.current_user_top_artists(limit=5)
        top_artists = [{
            "id": artist['id'],
            "name": artist['name'],
            "image": artist['images'][0]['url'] if artist['images'] else None,
            "spotify_url": f"https://open.spotify.com/artist/{artist['id']}"  # Add Spotify URL
        } for artist in results['items']]
        return JSONResponse(content={"top_artists": top_artists})
    except spotipy.exceptions.SpotifyException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


## GENERATE PLAYLIST (main function)
@app.post("/generate-playlist")
def generate_playlist(mood: str, request: Request) -> JSONResponse:

    logging.info(f"Entered generate_playlist with mood: {mood}")
    access_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    logging.info(f"Using access token: {access_token}")

    if not access_token:
        raise HTTPException(status_code=403, detail="Access Token is missing from headers.")

    if mood not in mood_map:
        raise HTTPException(status_code=400, detail="Invalid mood specified")

    try:
        user_profile = sp.current_user()
        user_id = user_profile['id']
        user_name = user_profile['display_name']
    
        top_artists = sp.current_user_top_artists(limit=5)['items']
        artist_ids = [artist['id'] for artist in top_artists]

        all_tracks = []
        artist_tracks_dict = {}
        track_titles_seen = set()  # Set to keep track of titles to avoid duplicates

        for artist_id in artist_ids:
            # Fetch tracks for each artist based on mood, limited to 50 per artist
            tracks = supabase.table("mood_scores").select("*").eq("mood", mood).eq("artist_id", artist_id).limit(75).execute()
            if tracks.data:
                # Filter out tracks with titles that have been seen before
                filtered_tracks = [track for track in tracks.data if track['track_name'] not in track_titles_seen]
                # Update seen titles
                track_titles_seen.update([track['track_name'] for track in filtered_tracks])
                # Randomly sample 5 tracks from the filtered list, ensuring unique titles
                selected_tracks = random.sample(filtered_tracks, min(5, len(filtered_tracks)))
                artist_tracks_dict[artist_id] = selected_tracks

        # Collect tracks from each artist to maintain a certain order
        for artist_id in artist_ids:
            if artist_id in artist_tracks_dict:
                all_tracks.extend(artist_tracks_dict[artist_id])

        track_ids = [track['track_id'] for track in all_tracks]

        # Create and populate the playlist
        playlist_name = f"{user_name}'s {random.choice(mood_adjectives.get(mood, ['Special']))} {mood.title()} Playlist"
        playlist_description = f"A personalized playlist to enhance your {mood} mood. Enjoy the vibes!"
        playlist = sp.user_playlist_create(user_id, playlist_name, public=False, description=playlist_description)

        print(f"Playlist ID: {playlist['id']}")  # Debug to check the playlist ID
        sp.playlist_add_items(playlist['id'], track_ids)

        return JSONResponse(status_code=200, 
                            content={"playlist_id": playlist['id'], 
                                     "playlist_name": playlist_name, 
                                     "tracks": [track['track_name'] for track in all_tracks]})

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Use the PORT environment variable or default to 8000
    uvicorn.run(app, host="0.0.0.0", port=port)