import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Sporty Tennis-Inspired Outfits for Confident Style",
        "Everyday Wellness Routine for a Healthy Glow",
        "Finding Strength in Little Wins: A Training Day",
        "Travel Diary: A City Escape with a Sporty Edge",
        "How to Build a Versatile Activewear Capsule",
        "Fresh Glow Makeup for an Active Lifestyle",
        "Photography Tips for Capturing Movement & Energy",
        "Wellness Rituals That Keep Me Feeling Strong",
        "Chic Airport Looks for the On-the-Go Traveler",
        "Personal Style Inspiration: Dressing with Confidence",
        "Cozy Off-Duty Looks for Rest Days",
        "Sporty Feminine Fashion I'm Loving Right Now",
        "A Energizing Morning Routine to Start Strong",
        "Travel Adventures: Exploring a New City in Motion",
        "Live Boldly: Small Habits for a Confident Life",
    ]

    fallback_descriptions = [
        "Fashion meets function on the court and beyond. These tennis-inspired looks are confident, fresh, and easy to wear every day. Save this for your next outfit plan! 🎾 #tennis #fashion #sportystyle #outfitinspo #livianakingsley",
        "Beauty starts with how you treat yourself. A simple routine, a little light, and you glow from within. Like if you love a natural look! 💄 #beauty #skincare #glow #selfcare #livianakingsley",
        "The little wins are where strength lives — a good session, fresh air, a slow moment to recover. Notice them today. Double tap if you agree! 💪 #wellness #lifestyle #everydaystrength #mindful #livianakingsley",
        "Travel feeds the soul. A new city, pretty streets, and outfits that match the energy — this escape was pure magic. Comment your dream destination! ✈️ #travel #traveldiary #adventure #style #livianakingsley",
        "A versatile wardrobe makes getting dressed fun. A few quality active pieces, mixed with love, go everywhere. Share this with a style friend! 🤍 #fashion #activewear #timeless #confidence #livianakingsley",
        "Fresh glow is my favorite kind of look — healthy skin, a sporty lip, and quiet confidence. Save this for your next active day! 🌞 #beauty #makeup #glow #activelifestyle #livianakingsley",
        "You don't need a fancy camera to capture energy — just light and attention. Try these simple tips today. Like if you love photography! 📸 #photography #movement #inspiration #livianakingsley",
        "Wellness is strength from the inside out. A walk, water, rest, and kind thoughts make all the difference. Drop a 🌿 if you're prioritizing you! #wellness #selfcare #lifestyle #strength #livianakingsley",
        "Travel in style starts at the airport. Comfy yet chic pieces keep you polished from takeoff to arrival. Save this travel look! ✈️ #travelstyle #airportlook #ootd #fashion #livianakingsley",
        "Dress for confidence, not just occasions. When your outfit makes you feel strong, the whole day feels lighter. Comment your favorite piece! 🎾 #personalstyle #fashion #styleinspo #livianakingsley",
        "Cozy off-duty looks are a love language. Soft textures, relaxed tones, gentle rest days — my kind of comfort. Double tap if you love rest days! 🧶 #cozy #fashion #restday #livianakingsley",
        "Sporty feminine fashion is forever in my wardrobe. It's confident, fresh, and effortlessly cool. Like if you're a sporty girl! 🎾 #sportyfashion #fashion #style #beauty #livianakingsley",
        "An energizing morning sets the tone for a strong day. Light, movement, a little skincare, and intention. Follow Liviana Kingsley for daily fashion, beauty, and lifestyle inspiration! ☀️ #morningroutine #lifestyle #wellness #livianakingsley",
        "New city, new stories. I love exploring in motion — pretty cafés, hidden corners, and outfits made for wandering. Share this with a travel buddy! 🗺️ #travel #explore #citybreak #style #livianakingsley",
        "Live boldly — not perfectly. Small, confident habits turn ordinary days into something special. Be boldly you. 🤍 #lifestyle #liveboldly #selflove #inspiration #livianakingsley",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "sporty and confident — make viewers want to embrace tennis-inspired, active style",
        "warm and personal — share real healthy everyday moments",
        "adventurous and travel-loving — emphasise escapes, movement, and discovery",
        "beauty-focused — celebrate skincare, fresh makeup, and self-care",
        "calm and mindful — emphasise rest, recovery, and the little wins",
        "photography-inspired — encourage capturing energy and movement",
        "uplifting — remind viewers to live boldly and be themselves",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Liviana Kingsley'. "
        f"A space dedicated to sporty fashion, tennis-inspired style, wellness, beauty, lifestyle, and confident everyday moments. Liviana shares active looks, fresh glow makeup, travel adventures, training, photography, and personal-style inspiration — live boldly, be confidently you. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if this inspired your style! Comment your favorite look below! Share this with a friend who loves fashion! Follow Liviana Kingsley for daily fashion, beauty, and lifestyle inspiration!"
        f"Include relevant hashtags in ALL LOWERCASE such as #tennis #fashion #beauty #lifestyle #sportystyle #wellness #activewear #confidence #livianakingsley. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["tennis", "fashion", "beauty", "lifestyle", "sportystyle", "wellness", "activewear", "confidence", "livianakingsley", "ootd", "skincare", "selfcare", "inspiration", "liveboldly"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
