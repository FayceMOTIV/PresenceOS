"""
Tests for Ilyas Intelligence Module (Sprint 3).
Tests all 5 intelligence modules + tool dispatch + tools definition.
Uses mocks — no real API calls.
"""
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# ── Google Trends ──


def test_google_trends_init():
    """GoogleTrendsIntel initializes with lazy pytrends client."""
    from app.services.ilyas.intelligence.google_trends import GoogleTrendsIntel
    intel = GoogleTrendsIntel()
    assert intel._pytrends is None


@pytest.mark.asyncio
async def test_google_trends_get_food_trends():
    """get_food_trends returns rising and top queries."""
    from app.services.ilyas.intelligence.google_trends import GoogleTrendsIntel
    intel = GoogleTrendsIntel()

    import pandas as pd
    mock_rising = pd.DataFrame({"query": ["brunch paris", "burger gourmet"], "value": [150, 120]})
    mock_top = pd.DataFrame({"query": ["restaurant", "pizza"], "value": [100, 90]})

    mock_pt = MagicMock()
    mock_pt.build_payload = MagicMock()
    mock_pt.related_queries.return_value = {
        "restaurant": {"rising": mock_rising, "top": mock_top}
    }
    intel._pytrends = mock_pt

    result = await intel.get_food_trends("restaurant")
    assert result["keyword"] == "restaurant"
    assert len(result["rising"]) > 0
    assert len(result["top"]) > 0


@pytest.mark.asyncio
async def test_google_trends_compare_keywords():
    """compare_keywords returns trend data for each keyword."""
    from app.services.ilyas.intelligence.google_trends import GoogleTrendsIntel
    intel = GoogleTrendsIntel()

    import pandas as pd
    mock_df = pd.DataFrame({
        "burger": [50, 55, 60, 65, 70],
        "pizza": [80, 78, 75, 72, 70],
        "isPartial": [False] * 5,
    })
    mock_pt = MagicMock()
    mock_pt.build_payload = MagicMock()
    mock_pt.interest_over_time.return_value = mock_df
    intel._pytrends = mock_pt

    result = await intel.compare_keywords(["burger", "pizza"])
    assert result["keywords"] == ["burger", "pizza"]
    assert len(result["data"]) == 2
    assert result["data"][0]["keyword"] == "burger"
    assert result["data"][0]["trend"] == "up"


@pytest.mark.asyncio
async def test_google_trends_error_handling():
    """get_food_trends handles errors gracefully."""
    from app.services.ilyas.intelligence.google_trends import GoogleTrendsIntel
    intel = GoogleTrendsIntel()

    mock_pt = MagicMock()
    mock_pt.build_payload.side_effect = Exception("rate limited")
    intel._pytrends = mock_pt

    result = await intel.get_food_trends("test")
    assert "error" in result
    assert result["rising"] == []


# ── Instagram ──


def test_instagram_init():
    """InstagramIntel initializes with lazy loader."""
    from app.services.ilyas.intelligence.instagram_intel import InstagramIntel
    intel = InstagramIntel()
    assert intel._loader is None


@pytest.mark.asyncio
async def test_instagram_analyze_competitor():
    """analyze_competitor returns profile info and recent posts."""
    from app.services.ilyas.intelligence.instagram_intel import InstagramIntel
    intel = InstagramIntel()
    intel._loader = MagicMock()

    mock_post = MagicMock()
    mock_post.date_utc.isoformat.return_value = "2026-01-15T12:00:00"
    mock_post.likes = 150
    mock_post.comments = 10
    mock_post.caption = "Plat du jour #restaurant"
    mock_post.is_video = False
    mock_post.caption_hashtags = ["restaurant"]

    mock_profile = MagicMock()
    mock_profile.full_name = "Le Family's"
    mock_profile.followers = 5000
    mock_profile.followees = 200
    mock_profile.mediacount = 300
    mock_profile.biography = "Restaurant familial"
    mock_profile.is_verified = False
    mock_profile.get_posts.return_value = iter([mock_post])

    # Inject a mock instaloader module into sys.modules
    mock_insta_mod = MagicMock()
    mock_insta_mod.Profile.from_username.return_value = mock_profile
    with patch.dict(sys.modules, {"instaloader": mock_insta_mod}):
        result = await intel.analyze_competitor("lefamilys")

    assert result["username"] == "lefamilys"
    assert result["followers"] == 5000
    assert len(result["recent_posts"]) == 1
    assert "engagement_rate" in result


@pytest.mark.asyncio
async def test_instagram_analyze_hashtag():
    """analyze_hashtag returns top posts for a hashtag."""
    from app.services.ilyas.intelligence.instagram_intel import InstagramIntel
    intel = InstagramIntel()
    intel._loader = MagicMock()

    mock_post = MagicMock()
    mock_post.owner_username = "foodie_paris"
    mock_post.likes = 500
    mock_post.comments = 25
    mock_post.caption = "Best burger in town"
    mock_post.date_utc.isoformat.return_value = "2026-02-01T10:00:00"

    mock_hashtag = MagicMock()
    mock_hashtag.mediacount = 50000
    mock_hashtag.get_top_posts.return_value = iter([mock_post])

    mock_insta_mod = MagicMock()
    mock_insta_mod.Hashtag.from_name.return_value = mock_hashtag
    with patch.dict(sys.modules, {"instaloader": mock_insta_mod}):
        result = await intel.analyze_hashtag("restaurantparis")

    assert result["hashtag"] == "restaurantparis"
    assert result["post_count"] == 50000
    assert len(result["top_posts"]) == 1


@pytest.mark.asyncio
async def test_instagram_error_handling():
    """analyze_competitor handles errors gracefully."""
    from app.services.ilyas.intelligence.instagram_intel import InstagramIntel
    intel = InstagramIntel()
    intel._loader = MagicMock()

    mock_insta_mod = MagicMock()
    mock_insta_mod.Profile.from_username.side_effect = Exception("private profile")
    with patch.dict(sys.modules, {"instaloader": mock_insta_mod}):
        result = await intel.analyze_competitor("private_user")

    assert "error" in result


# ── TikTok ──


def test_tiktok_init():
    """TikTokIntel initializes with no session."""
    from app.services.ilyas.intelligence.tiktok_intel import TikTokIntel
    intel = TikTokIntel()
    assert intel._api is None


@pytest.mark.asyncio
async def test_tiktok_get_video_info():
    """get_video_info extracts metadata via yt-dlp."""
    from app.services.ilyas.intelligence.tiktok_intel import TikTokIntel
    intel = TikTokIntel()

    mock_info = {
        "title": "Best restaurant in Paris",
        "description": "Check out this amazing food",
        "uploader": "foodie_fr",
        "view_count": 100000,
        "like_count": 5000,
        "comment_count": 200,
        "duration": 30,
        "upload_date": "20260201",
        "tags": ["food", "paris", "restaurant"],
    }

    mock_ydl = MagicMock()
    mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.return_value = mock_info

    mock_ytdlp_mod = MagicMock()
    mock_ytdlp_mod.YoutubeDL.return_value = mock_ydl
    with patch.dict(sys.modules, {"yt_dlp": mock_ytdlp_mod}):
        result = await intel.get_video_info("https://tiktok.com/@user/video/123")

    assert result["title"] == "Best restaurant in Paris"
    assert result["view_count"] == 100000


@pytest.mark.asyncio
async def test_tiktok_search_no_api():
    """search_videos returns empty when API not available."""
    from app.services.ilyas.intelligence.tiktok_intel import TikTokIntel
    intel = TikTokIntel()
    # _api stays None → should return error
    result = await intel.search_videos("burger")
    assert "error" in result or result.get("videos") == []


# ── Reddit ──


def test_reddit_init():
    """RedditIntel initializes with lazy PRAW client."""
    from app.services.ilyas.intelligence.reddit_intel import RedditIntel
    intel = RedditIntel()
    assert intel._reddit is None


@pytest.mark.asyncio
async def test_reddit_search_no_credentials():
    """search_food_discussions returns error when credentials missing."""
    from app.services.ilyas.intelligence.reddit_intel import RedditIntel
    intel = RedditIntel()

    with patch("app.services.ilyas.intelligence.reddit_intel.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            reddit_client_id="",
            reddit_client_secret="",
            reddit_user_agent="test",
        )
        # Force re-init
        intel._reddit = None

        result = await intel.search_food_discussions("burger")
        assert "error" in result or result["posts"] == []


@pytest.mark.asyncio
async def test_reddit_search_with_results():
    """search_food_discussions returns posts from subreddits."""
    from app.services.ilyas.intelligence.reddit_intel import RedditIntel
    intel = RedditIntel()

    mock_post = MagicMock()
    mock_post.title = "Meilleur burger à Paris ?"
    mock_post.score = 150
    mock_post.num_comments = 45
    mock_post.permalink = "/r/france/comments/abc123/meilleur_burger/"
    mock_post.selftext = "Je cherche le meilleur burger de Paris"
    mock_post.created_utc = 1709200000
    mock_post.upvote_ratio = 0.95

    mock_subreddit = MagicMock()
    mock_subreddit.search.return_value = [mock_post]

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value = mock_subreddit
    intel._reddit = mock_reddit

    result = await intel.search_food_discussions("burger", subreddits=["france"])
    assert result["query"] == "burger"
    assert len(result["posts"]) == 1
    assert result["posts"][0]["title"] == "Meilleur burger à Paris ?"
    assert result["posts"][0]["score"] == 150


@pytest.mark.asyncio
async def test_reddit_trending():
    """get_trending_discussions returns hot posts from subreddit."""
    from app.services.ilyas.intelligence.reddit_intel import RedditIntel
    intel = RedditIntel()

    mock_post = MagicMock()
    mock_post.stickied = False
    mock_post.title = "Post trending"
    mock_post.score = 200
    mock_post.num_comments = 80
    mock_post.permalink = "/r/france/comments/xyz/"
    mock_post.selftext = ""
    mock_post.upvote_ratio = 0.92

    mock_subreddit = MagicMock()
    mock_subreddit.hot.return_value = [mock_post]

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value = mock_subreddit
    intel._reddit = mock_reddit

    result = await intel.get_trending_discussions("france", limit=5)
    assert result["subreddit"] == "france"
    assert len(result["posts"]) == 1


# ── YouTube ──


def test_youtube_init():
    """YouTubeIntel initializes with lazy API service."""
    from app.services.ilyas.intelligence.youtube_intel import YouTubeIntel
    intel = YouTubeIntel()
    assert intel._service is None


@pytest.mark.asyncio
async def test_youtube_search_no_api_key():
    """search_food_videos returns error when API key missing."""
    from app.services.ilyas.intelligence.youtube_intel import YouTubeIntel
    intel = YouTubeIntel()

    with patch("app.services.ilyas.intelligence.youtube_intel.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(youtube_api_key="")
        intel._service = None

        result = await intel.search_food_videos("restaurant paris")
        assert "error" in result


@pytest.mark.asyncio
async def test_youtube_search_with_results():
    """search_food_videos returns videos with stats."""
    from app.services.ilyas.intelligence.youtube_intel import YouTubeIntel
    intel = YouTubeIntel()

    mock_search_response = {
        "items": [{
            "id": {"videoId": "abc123"},
            "snippet": {
                "title": "Top 10 restaurants Paris",
                "channelTitle": "FoodChannel",
                "description": "Découvrez les meilleurs restos",
                "publishedAt": "2026-01-15T10:00:00Z",
            },
        }]
    }
    mock_stats_response = {
        "items": [{
            "id": "abc123",
            "statistics": {
                "viewCount": "50000",
                "likeCount": "2000",
                "commentCount": "150",
            },
        }]
    }

    mock_search_req = MagicMock()
    mock_search_req.execute.return_value = mock_search_response
    mock_stats_req = MagicMock()
    mock_stats_req.execute.return_value = mock_stats_response

    mock_service = MagicMock()
    mock_service.search.return_value.list.return_value = mock_search_req
    mock_service.videos.return_value.list.return_value = mock_stats_req
    intel._service = mock_service

    result = await intel.search_food_videos("restaurant paris", max_results=5)
    assert result["query"] == "restaurant paris"
    assert len(result["videos"]) == 1
    assert result["videos"][0]["views"] == 50000
    assert result["videos"][0]["title"] == "Top 10 restaurants Paris"


@pytest.mark.asyncio
async def test_youtube_channel_analysis():
    """analyze_channel returns channel info with recent videos."""
    from app.services.ilyas.intelligence.youtube_intel import YouTubeIntel
    intel = YouTubeIntel()

    mock_ch_response = {
        "items": [{
            "snippet": {
                "title": "FoodChannel",
                "description": "Food reviews in France",
            },
            "statistics": {
                "subscriberCount": "100000",
                "viewCount": "5000000",
                "videoCount": "200",
            },
            "contentDetails": {
                "relatedPlaylists": {"uploads": "UUabc123"},
            },
        }]
    }
    mock_pl_response = {
        "items": [{
            "snippet": {
                "title": "New restaurant review",
                "publishedAt": "2026-02-20T10:00:00Z",
                "resourceId": {"videoId": "vid123"},
            },
        }]
    }

    mock_ch_req = MagicMock()
    mock_ch_req.execute.return_value = mock_ch_response
    mock_pl_req = MagicMock()
    mock_pl_req.execute.return_value = mock_pl_response

    mock_service = MagicMock()
    mock_service.channels.return_value.list.return_value = mock_ch_req
    mock_service.playlistItems.return_value.list.return_value = mock_pl_req
    intel._service = mock_service

    result = await intel.analyze_channel("UCabc123")
    assert result["title"] == "FoodChannel"
    assert result["subscribers"] == 100000
    assert len(result["recent_videos"]) == 1


# ── Tools definition ──


def test_tools_definition_count():
    """ILYAS_TOOLS contains all 12 tool definitions."""
    from app.services.ilyas.tools import ILYAS_TOOLS, ACTION_TOOLS, INTELLIGENCE_TOOLS
    assert len(ACTION_TOOLS) == 3
    assert len(INTELLIGENCE_TOOLS) == 9
    assert len(ILYAS_TOOLS) == 12


def test_tools_have_required_fields():
    """Each tool has name, description, and input_schema."""
    from app.services.ilyas.tools import ILYAS_TOOLS
    for tool in ILYAS_TOOLS:
        assert "name" in tool, f"Tool missing name: {tool}"
        assert "description" in tool, f"Tool {tool.get('name')} missing description"
        assert "input_schema" in tool, f"Tool {tool.get('name')} missing input_schema"
        assert tool["input_schema"]["type"] == "object"


def test_tools_unique_names():
    """All tool names are unique."""
    from app.services.ilyas.tools import ILYAS_TOOLS
    names = [t["name"] for t in ILYAS_TOOLS]
    assert len(names) == len(set(names)), f"Duplicate names: {names}"


# ── Tool dispatch (use private _xxx attributes to mock properties) ──


@pytest.mark.asyncio
async def test_dispatch_google_trends():
    """_dispatch_tool routes google_trends correctly."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    mock_gt = MagicMock()
    mock_gt.get_food_trends = AsyncMock(return_value={"keyword": "burger", "rising": []})
    agent._google_trends = mock_gt

    result_str = await agent._dispatch_tool("google_trends", {"category": "burger"})
    result = json.loads(result_str)
    assert result["keyword"] == "burger"
    mock_gt.get_food_trends.assert_called_once_with(category="burger")


@pytest.mark.asyncio
async def test_dispatch_compare_trends():
    """_dispatch_tool routes compare_trends correctly."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    mock_gt = MagicMock()
    mock_gt.compare_keywords = AsyncMock(return_value={"keywords": ["a", "b"], "data": []})
    agent._google_trends = mock_gt

    result_str = await agent._dispatch_tool("compare_trends", {"keywords": ["a", "b"]})
    result = json.loads(result_str)
    assert result["keywords"] == ["a", "b"]


@pytest.mark.asyncio
async def test_dispatch_instagram_competitor():
    """_dispatch_tool routes instagram_competitor correctly."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    mock_ig = MagicMock()
    mock_ig.analyze_competitor = AsyncMock(return_value={"username": "test", "followers": 1000})
    agent._instagram = mock_ig

    result_str = await agent._dispatch_tool("instagram_competitor", {"username": "test"})
    result = json.loads(result_str)
    assert result["username"] == "test"


@pytest.mark.asyncio
async def test_dispatch_instagram_hashtag():
    """_dispatch_tool routes instagram_hashtag correctly."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    mock_ig = MagicMock()
    mock_ig.analyze_hashtag = AsyncMock(return_value={"hashtag": "food", "post_count": 1000})
    agent._instagram = mock_ig

    result_str = await agent._dispatch_tool("instagram_hashtag", {"tag": "food"})
    result = json.loads(result_str)
    assert result["hashtag"] == "food"


@pytest.mark.asyncio
async def test_dispatch_tiktok_search():
    """_dispatch_tool routes tiktok_search correctly."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    mock_tt = MagicMock()
    mock_tt.search_videos = AsyncMock(return_value={"keyword": "brunch", "videos": []})
    agent._tiktok = mock_tt

    result_str = await agent._dispatch_tool("tiktok_search", {"keyword": "brunch"})
    result = json.loads(result_str)
    assert result["keyword"] == "brunch"


@pytest.mark.asyncio
async def test_dispatch_tiktok_video_info():
    """_dispatch_tool routes tiktok_video_info correctly."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    mock_tt = MagicMock()
    mock_tt.get_video_info = AsyncMock(return_value={"url": "https://tiktok.com/...", "title": "Video"})
    agent._tiktok = mock_tt

    result_str = await agent._dispatch_tool("tiktok_video_info", {"url": "https://tiktok.com/..."})
    result = json.loads(result_str)
    assert result["title"] == "Video"


@pytest.mark.asyncio
async def test_dispatch_reddit_search():
    """_dispatch_tool routes reddit_search correctly."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    mock_rd = MagicMock()
    mock_rd.search_food_discussions = AsyncMock(return_value={"query": "burger", "posts": []})
    agent._reddit = mock_rd

    result_str = await agent._dispatch_tool("reddit_search", {"query": "burger"})
    result = json.loads(result_str)
    assert result["query"] == "burger"


@pytest.mark.asyncio
async def test_dispatch_youtube_search():
    """_dispatch_tool routes youtube_search correctly."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    mock_yt = MagicMock()
    mock_yt.search_food_videos = AsyncMock(return_value={"query": "food", "videos": []})
    agent._youtube = mock_yt

    result_str = await agent._dispatch_tool("youtube_search", {"query": "food"})
    result = json.loads(result_str)
    assert result["query"] == "food"


@pytest.mark.asyncio
async def test_dispatch_youtube_channel():
    """_dispatch_tool routes youtube_channel correctly."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    mock_yt = MagicMock()
    mock_yt.analyze_channel = AsyncMock(return_value={"channel_id": "UC123", "title": "Test"})
    agent._youtube = mock_yt

    result_str = await agent._dispatch_tool("youtube_channel", {"channel_id": "UC123"})
    result = json.loads(result_str)
    assert result["channel_id"] == "UC123"


@pytest.mark.asyncio
async def test_dispatch_unknown_tool():
    """_dispatch_tool returns error for unknown tool."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    result_str = await agent._dispatch_tool("nonexistent_tool", {})
    result = json.loads(result_str)
    assert "error" in result


@pytest.mark.asyncio
async def test_dispatch_action_tool_placeholder():
    """_dispatch_tool returns not_implemented for action tools."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = AsyncMock()
    agent = IlyasAgent(mock_db)

    result_str = await agent._dispatch_tool("generate_post", {"platform": "instagram", "post_type": "post", "topic": "test"})
    result = json.loads(result_str)
    assert result["status"] == "not_implemented"


# ── Agent lazy init ──


def test_agent_lazy_intelligence_init():
    """Intelligence modules are lazily initialized."""
    from app.services.ilyas.agent import IlyasAgent

    mock_db = MagicMock()
    agent = IlyasAgent(mock_db)

    assert agent._google_trends is None
    assert agent._instagram is None
    assert agent._tiktok is None
    assert agent._reddit is None
    assert agent._youtube is None
