# 🚀 Video Info Extractor - Vercel Edition

A serverless video information extractor that works with YouTube and Instagram URLs. Deployed on Vercel for fast, global access.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ASHWINASH-8/VID-DOWNLOADER)

## ✨ Features

- 🎥 **YouTube Video Info** - Extract title, duration, formats, views
- 📱 **Instagram Reel Info** - Get Instagram reel information  
- 🎵 **Playlist Support** - List videos in YouTube playlists
- ⚡ **Serverless** - Fast response times with Vercel
- 🌐 **Global CDN** - Available worldwide
- 📱 **Mobile Friendly** - Responsive design

## 🚀 Quick Deploy to Vercel

### Option 1: One-Click Deploy
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ASHWINASH-8/VID-DOWNLOADER)

### Option 2: Manual Deploy
1. Fork this repository
2. Go to [vercel.com](https://vercel.com)
3. Import your forked repository
4. Deploy automatically

### Option 3: Vercel CLI
```bash
npm i -g vercel
git clone https://github.com/ASHWINASH-8/VID-DOWNLOADER.git
cd VID-DOWNLOADER
vercel
```

## 🛠️ Local Development

```bash
# Clone the repository
git clone https://github.com/ASHWINASH-8/VID-DOWNLOADER.git
cd VID-DOWNLOADER

# Install dependencies
pip install -r requirements.txt

# Run locally
python api/app.py
```

## 📡 API Endpoints

### Get Video Information
```http
POST /video_info
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

### Health Check
```http
GET /health
```

## 📱 Supported URLs

- ✅ YouTube videos: `youtube.com/watch?v=...`
- ✅ YouTube shorts: `youtu.be/...`
- ✅ YouTube playlists: `youtube.com/playlist?list=...`
- ✅ Instagram reels: `instagram.com/reel/...`
- ✅ Instagram posts: `instagram.com/p/...`

## 💡 Usage Examples

### Extract YouTube Video Info
1. Paste: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
2. Get: Title, duration, available formats, view count

### Extract Playlist Info
1. Paste: `https://www.youtube.com/playlist?list=PLxxxxxx`
2. Get: Playlist title, video count, individual video info

### Extract Instagram Reel Info
1. Paste: `https://www.instagram.com/reel/xxxxxxxxx/`
2. Get: Title, uploader, duration, thumbnail

## ⚠️ Important Notes

- **Information Only**: This tool extracts video information, not downloads
- **Vercel Limits**: 60-second execution limit for serverless functions
- **No File Storage**: Downloads not supported on Vercel's serverless platform
- **Use External Tools**: Use yt-dlp, youtube-dl, or similar for actual downloads

## 🔧 Environment Variables

Set in Vercel dashboard:
- `SECRET_KEY`: Random string for session security

## 📊 Why Vercel?

- ⚡ **Fast**: Global edge network
- 🆓 **Free Tier**: Generous limits for personal use
- 🔄 **Auto Deploy**: Git push = auto deployment
- 📈 **Scalable**: Handles traffic spikes automatically
- 🌍 **Global**: Available worldwide instantly

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

MIT License - feel free to use and modify

---

⭐ **Star this repo if it helps you!**
