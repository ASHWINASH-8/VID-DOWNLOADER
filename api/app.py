import os
import tempfile
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import yt_dlp
import re

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

# Simple URL validation
def is_valid_url(url):
    """Check if URL is from supported platforms"""
    supported_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel)/[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in supported_patterns)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'video-downloader',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/video_info', methods=['POST'])
def get_video_info():
    """Get video information from URL"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        if not is_valid_url(url):
            return jsonify({'success': False, 'error': 'Unsupported URL format'})
        
        # Basic yt-dlp info extraction
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check if it's a playlist
            if 'entries' in info and info['entries']:
                playlist_info = {
                    'title': info.get('title', 'Unknown Playlist'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'video_count': len(info['entries']),
                    'is_playlist': True,
                    'videos': []
                }
                
                # Get first few videos info
                for i, entry in enumerate(info['entries'][:10]):  # Limit to 10 for demo
                    if entry:
                        playlist_info['videos'].append({
                            'title': entry.get('title', 'Unknown'),
                            'duration': entry.get('duration'),
                            'thumbnail': entry.get('thumbnail')
                        })
                
                return jsonify({'success': True, 'data': playlist_info})
            
            else:
                # Single video
                formats = []
                if 'formats' in info:
                    for f in info['formats'][-5:]:  # Last 5 formats
                        if f.get('height') and f.get('ext'):
                            formats.append({
                                'format_id': f['format_id'],
                                'resolution': f"{f.get('height', 'N/A')}p",
                                'ext': f.get('ext', 'mp4'),
                                'filesize': f.get('filesize'),
                                'has_audio': bool(f.get('acodec') and f.get('acodec') != 'none'),
                                'has_video': bool(f.get('vcodec') and f.get('vcodec') != 'none')
                            })
                
                video_info = {
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'view_count': info.get('view_count'),
                    'formats': formats,
                    'is_playlist': False
                }
                
                return jsonify({'success': True, 'data': video_info})
                
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error extracting info: {str(e)}'})

@app.route('/download_info', methods=['POST'])
def download_info():
    """Provide download information (Vercel doesn't support actual file downloads)"""
    return jsonify({
        'success': False, 
        'error': 'Direct downloads not supported on Vercel. Use this tool to get video information and download URLs.',
        'message': 'Copy the video URL and use a local downloader or another service for actual downloading.'
    })

# For Vercel
def handler(request):
    return app

if __name__ == '__main__':
    app.run(debug=True)
