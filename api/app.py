import os
import tempfile
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import yt_dlp
import re

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'vercel-video-downloader-2025')

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
        
        # Enhanced yt-dlp options with anti-bot measures
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiefile': None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Connection': 'keep-alive'
            },
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['js'],
                    'comment_sort': ['top']
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
        except Exception as e:
            error_msg = str(e)
            
            # If it's a bot detection error, try with different options
            if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
                try:
                    # Fallback with minimal options
                    fallback_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': True,  # Get basic info only
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                        }
                    }
                    
                    with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        
                except Exception as fallback_error:
                    return jsonify({
                        'success': False, 
                        'error': 'YouTube is blocking requests. This is common on serverless platforms. Try using the URL directly with yt-dlp or youtube-dl locally.',
                        'original_error': error_msg,
                        'suggestion': 'For downloads, use: yt-dlp "' + url + '"'
                    })
            else:
                return jsonify({'success': False, 'error': f'Error extracting info: {error_msg}'})
        
        # Process the extracted info
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
