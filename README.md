# Video Downloader Web Application

A modern, feature-rich web application for downloading videos from popular platforms like YouTube, Instagram, TikTok, and more.

## Features

- **Single Video Download**: Download individual videos by URL
- **Smart Batch Download**: Upload files or paste URLs (including YouTube playlists) for bulk downloads
- **Playlist Integration**: Automatically expands YouTube playlist URLs into individual videos
- **Format Selection**: Choose from available video quality and formats
- **Real-time Progress**: Live download progress tracking
- **File Management**: View and download completed files
- **Cross-platform Support**: Works on Windows, macOS, and Linux
- **Modern UI**: Beautiful, responsive web interface

## Supported Platforms

- YouTube
- Instagram
- TikTok
- Twitter/X
- Facebook
- And many more (thanks to yt-dlp)

## Installation

1. Clone or download this project
2. Install Python 3.7 or higher
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and go to `http://localhost:5000`

3. **Single Video Download**:
   - Enter a video URL
   - Click "Get Info" to see available formats
   - Select your preferred quality/format
   - Click "Download Video"

4. **Batch Download** (supports playlists):
   - **Method 1**: Paste URLs directly in the text area (supports individual URLs and playlists)
   - **Method 2**: Upload a CSV or TXT file with URLs (including playlist URLs)
   - System automatically expands playlist URLs into individual videos
   - Click "Process URLs" to see expanded video list
   - Click "Download All" to start batch download
   - Prepare a CSV or TXT file with one URL per line
   - Upload the file using the "Batch Upload" tab
   - Select which URLs to download
   - Start the batch download process

## File Formats

### For Batch Upload
- **CSV**: One URL per row in the first column
- **TXT**: One URL per line

Example CSV:
```
https://www.youtube.com/watch?v=VIDEO_ID1
https://www.instagram.com/p/POST_ID/
https://www.tiktok.com/@user/video/VIDEO_ID
```

Example TXT:
```
https://www.youtube.com/watch?v=VIDEO_ID1
https://www.instagram.com/p/POST_ID/
https://www.tiktok.com/@user/video/VIDEO_ID
```

## Configuration

- Downloaded files are saved to the `downloads/` directory
- Uploaded files are temporarily stored in `uploads/` directory
- You can modify the download location in `app.py`

## Deployment

### Local Development
```bash
python app.py
```

### Production Deployment

#### Using Gunicorn (Linux/macOS)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Using Waitress (Windows)
```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

### Environment Variables
You can set these environment variables for production:
- `FLASK_ENV=production`
- `SECRET_KEY=your_secret_key_here`

## Features in Detail

### Video Information Extraction
- Video title, duration, uploader
- Available formats and resolutions
- File sizes and codecs
- Thumbnail preview

### Playlist Support
- YouTube playlist information extraction
- Video count and playlist metadata
- Individual video details within playlists
- Option to limit number of downloads
- Organized folder structure (creates folders for playlists)

### Download Options
- Multiple quality options
- Video + Audio combined downloads
- Format selection (MP4, WebM, etc.)
- Audio-only downloads (when available)

### Progress Tracking
- Real-time download progress
- Speed monitoring
- Error handling and reporting
- Multiple concurrent downloads

### File Management
- List all downloaded files
- File size and modification date
- Direct download links
- Organized file structure

## Technical Details

### Dependencies
- **Flask**: Web framework
- **yt-dlp**: Video downloading engine
- **Werkzeug**: WSGI utilities
- **Bootstrap**: Frontend framework
- **Font Awesome**: Icons

### Architecture
- Backend: Python Flask application
- Frontend: HTML5, CSS3, JavaScript with Bootstrap
- Download Engine: yt-dlp with custom progress hooks
- File Storage: Local filesystem with organized structure

## Troubleshooting

### Common Issues
1. **"Unsupported URL"**: Check if the platform is supported by yt-dlp
2. **Download Fails**: Some videos may have restrictions or require authentication
3. **Slow Downloads**: Large files or slow internet connection
4. **Format Not Available**: Some platforms limit available formats

### Error Handling
- Comprehensive error messages
- Graceful fallback to best available format
- Progress tracking with error states
- Detailed logging for debugging

## Security Considerations

- Input validation for URLs
- File type restrictions for uploads
- Secure filename handling
- No execution of uploaded content

## License

This project is for educational purposes. Please respect the terms of service of the platforms you download from and ensure you have the right to download the content.

## Contributing

Feel free to submit issues and enhancement requests!
