#!/usr/bin/env python3
"""
Test script for Instagram format detection
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import VideoDownloader

def test_instagram_formats():
    downloader = VideoDownloader()
    
    # Test Instagram URL (replace with the one from your screenshot)
    test_url = "https://www.instagram.com/reels/DL9QHdUyZQ4/"
    
    print(f"Testing Instagram URL: {test_url}")
    print("-" * 50)
    
    try:
        result = downloader.get_video_info(test_url)
        
        if result['success']:
            info = result['data']
            print(f"Title: {info['title']}")
            print(f"Uploader: {info['uploader']}")
            print(f"Best format ID: {info.get('best_format_id', 'None')}")
            print("\nFormats:")
            print("-" * 30)
            
            for i, fmt in enumerate(info['formats']):
                marker = " [BEST]" if fmt.get('is_best') else ""
                audio_status = "✓ Audio" if fmt.get('has_audio') else "✗ No Audio"
                video_status = "✓ Video" if fmt.get('has_video') else "✗ No Video"
                
                print(f"{i+1:2d}. {fmt['format_id']:15s} | {fmt['resolution']:15s} | {audio_status:10s} | {video_status:10s} | Score: {fmt.get('quality_score', 0):4d}{marker}")
                
        else:
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_instagram_formats()
