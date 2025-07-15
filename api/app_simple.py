import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import re
import requests

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

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:v=)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

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
    """Get video information from URL - Simplified for Vercel"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        if not is_valid_url(url):
            return jsonify({'success': False, 'error': 'Unsupported URL format'})
        
        # For YouTube URLs, provide basic info without yt-dlp
        if 'youtube.com' in url or 'youtu.be' in url:
            video_id = extract_video_id(url)
            if video_id:
                # Return basic info structure
                if 'playlist' in url or 'list=' in url:
                    return jsonify({
                        'success': True,
                        'data': {
                            'title': 'YouTube Playlist',
                            'uploader': 'YouTube',
                            'video_count': 'Multiple videos',
                            'is_playlist': True,
                            'videos': [],
                            'message': 'Playlist detected. Use yt-dlp locally for full playlist info.',
                            'command': f'yt-dlp "{url}"'
                        }
                    })
                else:
                    return jsonify({
                        'success': True,
                        'data': {
                            'title': f'YouTube Video (ID: {video_id})',
                            'uploader': 'YouTube',
                            'duration': 'Unknown',
                            'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
                            'view_count': 'Unknown',
                            'formats': [
                                {'format_id': 'best', 'resolution': 'Best available', 'ext': 'mp4', 'has_audio': True, 'has_video': True},
                                {'format_id': 'worst', 'resolution': 'Lowest quality', 'ext': 'mp4', 'has_audio': True, 'has_video': True}
                            ],
                            'is_playlist': False,
                            'message': 'Basic info only. Use yt-dlp locally for detailed info.',
                            'command': f'yt-dlp "{url}"'
                        }
                    })
        
        # For Instagram
        elif 'instagram.com' in url:
            return jsonify({
                'success': True,
                'data': {
                    'title': 'Instagram Content',
                    'uploader': 'Instagram User',
                    'duration': 'Unknown',
                    'thumbnail': 'https://via.placeholder.com/400x400?text=Instagram+Content',
                    'formats': [
                        {'format_id': 'best', 'resolution': 'Best available', 'ext': 'mp4', 'has_audio': True, 'has_video': True}
                    ],
                    'is_playlist': False,
                    'message': 'Instagram content detected. Use yt-dlp locally for download.',
                    'command': f'yt-dlp "{url}"'
                }
            })
        
        # Fallback - try with yt-dlp as last resort
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Minimal extraction
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return jsonify({
                    'success': True,
                    'data': {
                        'title': info.get('title', 'Unknown Title'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'duration': info.get('duration'),
                        'thumbnail': info.get('thumbnail'),
                        'is_playlist': 'entries' in info,
                        'message': 'Limited info extracted. Use yt-dlp locally for full features.',
                        'command': f'yt-dlp "{url}"'
                    }
                })
                
        except Exception as yt_error:
            return jsonify({
                'success': False,
                'error': 'YouTube/platform blocking detected on serverless environment.',
                'message': 'This is normal for Vercel deployment. Use yt-dlp locally for downloads.',
                'suggestion': f'Run locally: yt-dlp "{url}"',
                'install_guide': 'Install: pip install yt-dlp'
            })
                
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Error: {str(e)}',
            'message': 'Serverless limitations. Use yt-dlp locally for reliable extraction.',
            'command': f'yt-dlp "{url}"'
        })

@app.route('/download_info', methods=['POST'])
def download_info():
    """Provide download information"""
    return jsonify({
        'success': False, 
        'error': 'Direct downloads not supported on Vercel serverless platform.',
        'solution': 'Use yt-dlp locally for downloads',
        'install': 'pip install yt-dlp',
        'usage': 'yt-dlp [URL]'
    })

# For Vercel
def handler(request):
    return app

if __name__ == '__main__':
    app.run(debug=True)
