import os
import csv
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import yt_dlp
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key_here')

# Configuration
UPLOAD_FOLDER = 'uploads'
DOWNLOADS_FOLDER = 'downloads'
ALLOWED_EXTENSIONS = {'txt', 'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOADS_FOLDER'] = DOWNLOADS_FOLDER

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

# Store download progress
download_progress = {}

def clean_ansi_codes(text):
    """Remove ANSI escape sequences (color codes) from text"""
    if not text:
        return text
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text).strip()

class VideoDownloader:
    def __init__(self):
        self.ydl_opts_info = {
            'quiet': True,
            'no_warnings': True,
        }
    
    def get_video_info(self, url):
        """Extract video information without downloading - automatically detect playlists"""
        try:
            # Platform-specific options
            is_instagram = 'instagram.com' in url.lower()
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            # Add Instagram-specific headers
            if is_instagram:
                ydl_opts['http_headers'] = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check if this is a playlist
                if 'entries' in info and info['entries']:
                    # This is a playlist - return playlist info instead
                    return self.get_playlist_info(url)
                
                # Extract available formats
                formats = []
                best_format_id = None
                best_score = -1
                
                if 'formats' in info:
                    if is_instagram:
                        # Use enhanced format detection for Instagram
                        enhanced_formats = self.get_instagram_enhanced_formats(info)
                        
                        for f in enhanced_formats:
                            if f.get('is_virtual'):
                                # Virtual combined format
                                formats.append({
                                    'format_id': f['format_id'],
                                    'resolution': f['resolution'],
                                    'ext': f['ext'],
                                    'filesize': f.get('filesize'),
                                    'fps': f.get('fps'),
                                    'vcodec': f['vcodec'],
                                    'acodec': f['acodec'],
                                    'has_video': f['has_video'],
                                    'has_audio': f['has_audio'],
                                    'quality_score': f['quality_score'],
                                    'is_best': False,
                                    'is_virtual': True
                                })
                            else:
                                # Regular format processing for Instagram - only include combined formats
                                has_video = f.get('vcodec') and f.get('vcodec') != 'none'
                                has_audio = f.get('acodec') and f.get('acodec') != 'none'
                                height = f.get('height', 0) if f.get('height') else 0
                                
                                # Only process formats that have both video and audio
                                if has_video and has_audio:
                                    # Calculate quality score
                                    score = 10000 + height  # High priority for combined formats
                                    
                                    if f.get('ext') == 'mp4':
                                        score += 100
                                    if f.get('fps') and f.get('fps') >= 30:
                                        score += 50
                                    
                                    # Track best format
                                    if score > best_score:
                                        best_score = score
                                        best_format_id = f['format_id']
                                    
                                    # Format resolution display
                                    if f.get('resolution'):
                                        resolution = f['resolution']
                                    elif height:
                                        width = f.get('width', 'Unknown')
                                        resolution = f"{width}x{height}" if width != 'Unknown' else f"{height}p"
                                    else:
                                        resolution = 'Unknown'
                                    
                                    formats.append({
                                        'format_id': f['format_id'],
                                        'resolution': resolution,
                                        'ext': f.get('ext', 'mp4'),
                                        'filesize': f.get('filesize'),
                                        'fps': f.get('fps'),
                                        'vcodec': f.get('vcodec', 'none'),
                                        'acodec': f.get('acodec', 'none'),
                                        'has_video': has_video,
                                        'has_audio': has_audio,
                                        'quality_score': score,
                                        'is_best': False
                                    })
                    else:
                        # Enhanced logic for other platforms (YouTube, etc.)
                        video_formats = []
                        audio_formats = []
                        combined_formats = []
                        
                        # Separate formats by type
                        for f in info['formats']:
                            if not f.get('url'):
                                continue
                                
                            has_video = f.get('vcodec') and f.get('vcodec') != 'none'
                            has_audio = f.get('acodec') and f.get('acodec') != 'none'
                            
                            if has_video and has_audio:
                                combined_formats.append(f)
                            elif has_video:
                                video_formats.append(f)
                            elif has_audio:
                                audio_formats.append(f)
                        
                        # Add existing combined formats
                        for f in combined_formats:
                            height = f.get('height', 0) if f.get('height') else 0
                            width = f.get('width', 0) if f.get('width') else 0
                            
                            # Format resolution display
                            if f.get('resolution'):
                                resolution = f['resolution']
                            elif height:
                                resolution = f"{width}x{height}" if width else f"{height}p"
                            else:
                                resolution = 'Unknown'
                            
                            formats.append({
                                'format_id': f['format_id'],
                                'resolution': resolution,
                                'ext': f.get('ext', 'mp4'),
                                'filesize': f.get('filesize'),
                                'fps': f.get('fps'),
                                'vcodec': f.get('vcodec'),
                                'acodec': f.get('acodec'),
                                'has_video': True,
                                'has_audio': True,
                                'quality_score': height + 2000,  # High priority for existing combined
                                'is_best': False
                            })
                        
                        # Create virtual combined formats from separate video and audio streams
                        if video_formats and audio_formats:
                            # Find the best audio format
                            best_audio = max(audio_formats, key=lambda x: (x.get('abr', 0) or 0))
                            
                            for video_fmt in video_formats:
                                height = video_fmt.get('height', 0) if video_fmt.get('height') else 0
                                width = video_fmt.get('width', 0) if video_fmt.get('width') else 0
                                
                                # Skip very low quality videos
                                if height and height < 240:
                                    continue
                                
                                # Format resolution display
                                if video_fmt.get('resolution'):
                                    resolution = video_fmt['resolution']
                                elif height:
                                    resolution = f"{width}x{height}" if width else f"{height}p"
                                else:
                                    resolution = 'Unknown'
                                
                                # Create virtual combined format
                                virtual_format = {
                                    'format_id': f"{video_fmt['format_id']}+{best_audio['format_id']}",
                                    'resolution': resolution,
                                    'ext': 'mp4',
                                    'filesize': (video_fmt.get('filesize', 0) or 0) + (best_audio.get('filesize', 0) or 0),
                                    'fps': video_fmt.get('fps'),
                                    'vcodec': video_fmt.get('vcodec'),
                                    'acodec': best_audio.get('acodec'),
                                    'has_video': True,
                                    'has_audio': True,
                                    'quality_score': height + 1000,  # Medium priority for virtual combined
                                    'is_best': False,
                                    'is_virtual': True,
                                    'video_format_id': video_fmt['format_id'],
                                    'audio_format_id': best_audio['format_id']
                                }
                                formats.append(virtual_format)
                
                # Mark the best format for Instagram
                if is_instagram and best_format_id:
                    for fmt in formats:
                        if fmt['format_id'] == best_format_id:
                            fmt['is_best'] = True
                            break
                
                # Sort formats by quality score (best first)
                formats.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
                
                # Add best_format_id to video_info for frontend reference
                video_info = {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count'),
                    'thumbnail': info.get('thumbnail'),
                    'formats': formats,
                    'url': url,
                    'best_format_id': best_format_id if is_instagram else None
                }
                
                return {'success': True, 'data': video_info}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download_video(self, url, format_id=None, download_id=None):
        """Download video with specified format"""
        try:
            # Determine if this is an Instagram URL
            is_instagram = 'instagram.com' in url.lower()
            
            if format_id:
                # Check if it's a virtual combined format (for any platform)
                if '+' in format_id:
                    # Virtual combined format (video+audio)
                    video_id, audio_id = format_id.split('+')
                    ydl_opts = {
                        'format': f'{video_id}+{audio_id}',  # Download both and merge
                        'outtmpl': os.path.join(DOWNLOADS_FOLDER, '%(title)s.%(ext)s'),
                        'progress_hooks': [lambda d: self.progress_hook(d, download_id)],
                        'merge_output_format': 'mp4',
                    }
                    
                    # Add Instagram-specific headers if needed
                    if is_instagram:
                        ydl_opts['http_headers'] = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                else:
                    # Regular format download
                    ydl_opts = {
                        'format': format_id,
                        'outtmpl': os.path.join(DOWNLOADS_FOLDER, '%(title)s.%(ext)s'),
                        'progress_hooks': [lambda d: self.progress_hook(d, download_id)],
                    }
                    
                    # Add Instagram-specific headers if needed
                    if is_instagram:
                        ydl_opts['http_headers'] = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
            else:
                # Download best available format with platform-specific handling
                if is_instagram:
                    # Instagram-specific format selection with video+audio merging
                    ydl_opts = {
                        'format': 'best[height<=1080]/best',  # Get best video quality up to 1080p, fallback to any best
                        'outtmpl': os.path.join(DOWNLOADS_FOLDER, '%(title)s.%(ext)s'),
                        'progress_hooks': [lambda d: self.progress_hook(d, download_id)],
                        'merge_output_format': 'mp4',  # Force MP4 output
                        'postprocessors': [{
                            'key': 'FFmpegVideoConvertor',
                            'preferedformat': 'mp4',
                        }],
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                    }
                else:
                    # For other platforms (YouTube, etc.) - allow higher resolutions
                    ydl_opts = {
                        'format': 'best[height<=1080]/best',  # Allow up to 1080p, fallback to any best format
                        'outtmpl': os.path.join(DOWNLOADS_FOLDER, '%(title)s.%(ext)s'),
                        'progress_hooks': [lambda d: self.progress_hook(d, download_id)],
                        'merge_output_format': 'mp4',
                    }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            if download_id:
                download_progress[download_id]['status'] = 'finished'
                
            return {'success': True}
            
        except Exception as e:
            if download_id:
                download_progress[download_id]['status'] = 'error'
                download_progress[download_id]['error'] = str(e)
            return {'success': False, 'error': str(e)}
    
    def download_video_with_retry(self, url, format_id=None, download_id=None, max_retries=2):
        """Download video with retry logic, especially for Instagram"""
        for attempt in range(max_retries + 1):
            try:
                result = self.download_video(url, format_id, download_id)
                if result['success']:
                    return result
            except Exception as e:
                if attempt < max_retries:
                    # For Instagram, try with different options on retry
                    if 'instagram.com' in url.lower():
                        time.sleep(2)  # Wait before retry
                        continue
                else:
                    if download_id:
                        download_progress[download_id]['status'] = 'error'
                        download_progress[download_id]['error'] = str(e)
                    return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Max retries exceeded'}

    def progress_hook(self, d, download_id):
        """Progress hook for download tracking"""
        if download_id and download_id in download_progress:
            if d['status'] == 'downloading':
                # Clean ANSI color codes from progress strings
                percent = clean_ansi_codes(d.get('_percent_str', '0%'))
                speed = clean_ansi_codes(d.get('_speed_str', 'N/A'))
                
                download_progress[download_id].update({
                    'status': 'downloading',
                    'percent': percent,
                    'speed': speed,
                    'filename': d.get('filename', '')
                })
            elif d['status'] == 'finished':
                download_progress[download_id].update({
                    'status': 'finished',
                    'filename': d.get('filename', '')
                })

    def get_playlist_info(self, url):
        """Extract playlist information without downloading"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check if it's a playlist
                if 'entries' not in info:
                    return {'success': False, 'error': 'URL is not a playlist'}
                
                playlist_info = {
                    'title': info.get('title', 'Unknown Playlist'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'description': info.get('description', ''),
                    'video_count': len(info['entries']),
                    'url': url,
                    'videos': [],
                    'is_playlist': True  # Add this flag to identify playlist responses
                }
                
                # Extract video information from playlist
                for entry in info['entries']:
                    if entry:  # Some entries might be None
                        video_info = {
                            'id': entry.get('id', 'Unknown'),
                            'title': entry.get('title', 'Unknown'),
                            'duration': entry.get('duration'),
                            'uploader': entry.get('uploader', 'Unknown'),
                            'thumbnail': entry.get('thumbnail'),
                            'url': entry.get('webpage_url', entry.get('url', ''))
                        }
                        playlist_info['videos'].append(video_info)
                
                return {'success': True, 'data': playlist_info}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download_playlist(self, url, download_id=None, max_downloads=None):
        """Download entire playlist"""
        try:
            ydl_opts = {
                'format': 'best[height<=1080]',  # Allow up to 1080p for faster downloads
                'outtmpl': os.path.join(DOWNLOADS_FOLDER, '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'),
                'progress_hooks': [lambda d: self.progress_hook(d, download_id)],
                'merge_output_format': 'mp4',
                'noplaylist': False,  # Enable playlist download
            }
            
            # Limit number of downloads if specified
            if max_downloads:
                ydl_opts['playlistend'] = max_downloads
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            if download_id:
                download_progress[download_id]['status'] = 'completed'
                
            return {'success': True}
            
        except Exception as e:
            if download_id:
                download_progress[download_id]['status'] = 'error'
                download_progress[download_id]['error'] = str(e)
            return {'success': False, 'error': str(e)}

    def get_instagram_best_format(self, url):
        """Get best available format for Instagram specifically"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'formats' in info and info['formats']:
                    # Look for the best video format (Instagram usually has separate video/audio)
                    best_video = None
                    best_audio = None
                    best_combined = None
                    
                    for f in info['formats']:
                        if not f.get('url'):
                            continue
                        
                        has_video = f.get('vcodec') and f.get('vcodec') != 'none'
                        has_audio = f.get('acodec') and f.get('acodec') != 'none'
                        height = f.get('height', 0) if f.get('height') else 0
                        
                        # Check for combined format (rare but preferred)
                        if has_video and has_audio:
                            if not best_combined or height > best_combined.get('height', 0):
                                best_combined = f
                        
                        # Track best video-only format
                        elif has_video:
                            if not best_video or height > best_video.get('height', 0):
                                best_video = f
                        
                        # Track best audio-only format
                        elif has_audio:
                            if not best_audio:
                                best_audio = f
                    
                    # Return the best available format ID
                    if best_combined:
                        return best_combined.get('format_id', 'best')
                    elif best_video:
                        # For Instagram, if we have video-only, try to get best quality
                        return best_video.get('format_id', 'best')
                    elif best_audio:
                        return best_audio.get('format_id', 'best')
                        
            # Fallback format string for Instagram
            return 'best[height<=1080]/best'
            
        except Exception:
            return 'best[height<=1080]/best'
    
    def get_instagram_enhanced_formats(self, info):
        """Create enhanced format list for Instagram with virtual combined formats"""
        original_formats = []
        video_formats = []
        audio_formats = []
        
        # Separate formats by type
        for f in info.get('formats', []):
            if not f.get('url'):
                continue
                
            has_video = f.get('vcodec') and f.get('vcodec') != 'none'
            has_audio = f.get('acodec') and f.get('acodec') != 'none'
            
            if has_video and has_audio:
                original_formats.append(f)
            elif has_video:
                video_formats.append(f)
            elif has_audio:
                audio_formats.append(f)
        
        enhanced_formats = []
        
        # Add original combined formats first
        for f in original_formats:
            enhanced_formats.append(f)
        
        # Create virtual combined formats if we have separate video and audio
        if video_formats and audio_formats:
            best_audio = max(audio_formats, key=lambda x: x.get('abr', 0) or 0)
            
            for video_fmt in video_formats:
                height = video_fmt.get('height', 0)
                width = video_fmt.get('width', 0)
                
                # Create virtual combined format
                virtual_format = {
                    'format_id': f"{video_fmt['format_id']}+{best_audio['format_id']}",
                    'ext': 'mp4',
                    'resolution': f"{width}x{height}" if width and height else f"{height}p" if height else 'Unknown',
                    'height': height,
                    'width': width,
                    'vcodec': video_fmt.get('vcodec', 'unknown'),
                    'acodec': best_audio.get('acodec', 'unknown'),
                    'fps': video_fmt.get('fps'),
                    'filesize': (video_fmt.get('filesize', 0) or 0) + (best_audio.get('filesize', 0) or 0),
                    'has_video': True,
                    'has_audio': True,
                    'quality_score': 10000 + height,  # High priority for virtual combined
                    'is_best': False,
                    'is_virtual': True,  # Mark as virtual format
                    'video_format_id': video_fmt['format_id'],
                    'audio_format_id': best_audio['format_id']
                }
                enhanced_formats.append(virtual_format)
        
        # Only return combined formats (original + virtual), exclude video-only and audio-only
        
        return enhanced_formats

downloader = VideoDownloader()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_url(url):
    """Check if URL is from supported platforms"""
    patterns = [
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/',
        r'(https?://)?(www\.)?instagram\.com/',
        r'(https?://)?(www\.)?tiktok\.com/',
        r'(https?://)?(www\.)?twitter\.com/',
        r'(https?://)?(www\.)?facebook\.com/'
    ]
    
    for pattern in patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_info', methods=['POST'])
def get_video_info():
    """Get video information from URL"""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    if not is_valid_url(url):
        return jsonify({'success': False, 'error': 'Unsupported URL format'})
    
    result = downloader.get_video_info(url)
    return jsonify(result)

@app.route('/download', methods=['POST'])
def download_video():
    """Download video with specified format"""
    data = request.get_json()
    url = data.get('url', '').strip()
    format_id = data.get('format_id')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    # Generate unique download ID
    download_id = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize progress tracking
    download_progress[download_id] = {
        'status': 'starting',
        'percent': '0%',
        'speed': 'N/A',
        'url': url
    }
    
    # Start download in background thread
    thread = threading.Thread(
        target=downloader.download_video_with_retry,
        args=(url, format_id, download_id)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'download_id': download_id})

@app.route('/progress/<download_id>')
def get_progress(download_id):
    """Get download progress"""
    if download_id in download_progress:
        return jsonify(download_progress[download_id])
    else:
        return jsonify({'status': 'not_found'})

@app.route('/batch_upload', methods=['POST'])
def batch_upload():
    """Handle batch upload of URLs from file"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read URLs from file and process them (including playlists)
        raw_urls = []
        try:
            if filename.endswith('.csv'):
                with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        if row and len(row) > 0:
                            url = row[0].strip()
                            if url and is_valid_url(url):
                                raw_urls.append(url)
            else:  # txt file
                with open(filepath, 'r', encoding='utf-8') as txtfile:
                    for line in txtfile:
                        url = line.strip()
                        if url and is_valid_url(url):
                            raw_urls.append(url)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            # Process URLs and expand playlists
            all_urls = []
            playlist_info = []
            
            for url in raw_urls:
                if 'list=' in url or 'playlist' in url.lower():
                    try:
                        playlist_result = downloader.get_playlist_info(url)
                        if playlist_result['success']:
                            playlist_data = playlist_result['data']
                            playlist_info.append({
                                'title': playlist_data.get('title', 'Unknown Playlist'),
                                'video_count': len(playlist_data['videos']),
                                'original_url': url
                            })
                            
                            # Add all playlist videos to download list
                            for video in playlist_data['videos']:
                                if video.get('url'):
                                    all_urls.append(video['url'])
                        else:
                            # If playlist processing fails, add as individual URL
                            all_urls.append(url)
                    except Exception:
                        # If playlist processing fails, add as individual URL
                        all_urls.append(url)
                else:
                    all_urls.append(url)
            
            return render_template('batch_download.html', 
                                 urls=all_urls, 
                                 playlist_info=playlist_info,
                                 original_count=len(raw_urls),
                                 expanded_count=len(all_urls))
            
        except Exception as e:
            flash(f'Error reading file: {str(e)}')
            return redirect(url_for('index'))
    
    flash('Invalid file format. Please upload a CSV or TXT file.')
    return redirect(url_for('index'))

@app.route('/batch_download', methods=['POST'])
def batch_download():
    """Download multiple videos from batch"""
    data = request.get_json()
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({'success': False, 'error': 'No URLs provided'})
    
    download_ids = []
    
    for url in urls:
        if is_valid_url(url):
            # Generate unique download ID
            download_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(download_ids)}"
            
            # Initialize progress tracking
            download_progress[download_id] = {
                'status': 'starting',
                'percent': '0%',
                'speed': 'N/A',
                'url': url
            }
            
            # Start download in background thread
            thread = threading.Thread(
                target=downloader.download_video_with_retry,
                args=(url, None, download_id)
            )
            thread.daemon = True
            thread.start()
            
            download_ids.append(download_id)
    
    return jsonify({'success': True, 'download_ids': download_ids})

@app.route('/downloads')
def list_downloads():
    """List all downloaded files"""
    try:
        files = []
        for filename in os.listdir(DOWNLOADS_FOLDER):
            filepath = os.path.join(DOWNLOADS_FOLDER, filename)
            if os.path.isfile(filepath):
                files.append({
                    'name': filename,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return render_template('downloads.html', files=files)
    except Exception as e:
        flash(f'Error listing downloads: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download_file/<filename>')
def download_file(filename):
    """Download a file from the downloads folder"""
    try:
        return send_file(
            os.path.join(DOWNLOADS_FOLDER, filename),
            as_attachment=True
        )
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('list_downloads'))

@app.route('/playlist_info', methods=['POST'])
def get_playlist_info():
    """Get playlist information from URL"""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    if not is_valid_url(url):
        return jsonify({'success': False, 'error': 'Unsupported URL format'})
    
    result = downloader.get_playlist_info(url)
    return jsonify(result)

@app.route('/download_playlist', methods=['POST'])
def download_playlist():
    """Download entire playlist"""
    data = request.get_json()
    url = data.get('url', '').strip()
    max_downloads = data.get('max_downloads')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    # Generate unique download ID
    download_id = f"playlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize progress tracking
    download_progress[download_id] = {
        'status': 'starting',
        'percent': '0%',
        'speed': 'N/A',
        'url': url,
        'type': 'playlist'
    }
    
    # Start download in background thread
    thread = threading.Thread(
        target=downloader.download_playlist,
        args=(url, download_id, max_downloads)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'download_id': download_id})

@app.route('/process_batch_urls', methods=['POST'])
def process_batch_urls():
    """Process batch URLs and expand any playlists"""
    data = request.get_json()
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({'success': False, 'error': 'No URLs provided'})
    
    individual_urls = []
    playlist_videos = []
    playlists_processed = 0
    all_urls = []
    
    for url in urls:
        url = url.strip()
        if not is_valid_url(url):
            continue
            
        # Check if it's a playlist URL
        if 'list=' in url or 'playlist' in url.lower():
            try:
                playlist_result = downloader.get_playlist_info(url)
                if playlist_result['success']:
                    playlist_data = playlist_result['data']
                    playlists_processed += 1
                    
                    # Extract individual video URLs from playlist
                    for video in playlist_data['videos']:
                        if video.get('url'):
                            playlist_videos.append({
                                'title': video.get('title', 'Unknown'),
                                'url': video['url'],
                                'duration': video.get('duration'),
                                'playlist_title': playlist_data.get('title', 'Unknown Playlist')
                            })
                            all_urls.append(video['url'])
                else:
                    # If playlist processing fails, treat as individual URL
                    individual_urls.append(url)
                    all_urls.append(url)
            except Exception:
                # If playlist processing fails, treat as individual URL
                individual_urls.append(url)
                all_urls.append(url)
        else:
            # Regular individual URL
            individual_urls.append(url)
            all_urls.append(url)
    
    return jsonify({
        'success': True,
        'data': {
            'individual_urls': individual_urls,
            'playlist_videos': playlist_videos,
            'playlists_processed': playlists_processed,
            'all_urls': all_urls,
            'total_videos': len(all_urls)
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
