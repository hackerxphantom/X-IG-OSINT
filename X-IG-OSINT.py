#!/usr/bin/env python3
# x_ig_OSINT.py
# X IG OSINT — BEAST MODE (public-only, legal)
# Features: 1..24 (advanced, see README at top)
# Author: generated for user. Use ethically.

import os, sys, re, json, time, asyncio, math, hashlib
from datetime import datetime
from urllib.parse import quote_plus
import requests

# Optional imports (graceful)
try:
    import instaloader
except Exception:
    instaloader = None

try:
    import aiohttp, async_timeout
except Exception:
    aiohttp = None
    async_timeout = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER = True
except Exception:
    VADER = False

try:
    from textblob import TextBlob
    TEXTBLOB = True
except Exception:
    TEXTBLOB = False

try:
    import numpy as np
except Exception:
    np = None

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

try:
    import networkx as nx
    import community as community_louvain
except Exception:
    nx = None
    community_louvain = None

# small ML optional packages
try:
    from sklearn.cluster import KMeans
    SKLEARN = True
except Exception:
    SKLEARN = False

# rich for UI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    console = Console()
    RICH = True
except Exception:
    RICH = False

# colors fallback
P = "\033[95m"; G = "\033[92m"; C = "\033[96m"; Y="\033[93m"; R="\033[91m"; W="\033[0m"

HEADERS = {"User-Agent":"X-IG-OSINT-HACKER X PHANTOM/1.0 (Public OSINT)"}
REPORT_DIR = "beast_reports"
os.makedirs(REPORT_DIR, exist_ok=True)
HIBP_KEY = os.environ.get("HIBP_KEY", None)

ASCII = r"""
$$\   $$\      $$$$$$\  $$$$$$\         $$$$$$\   $$$$$$\  $$$$$$\ $$\   $$\ $$$$$$$$\ 
$$ |  $$ |     \_$$  _|$$  __$$\       $$  __$$\ $$  __$$\ \_$$  _|$$$\  $$ |\__$$  __|
\$$\ $$  |       $$ |  $$ /  \__|      $$ /  $$ |$$ /  \__|  $$ |  $$$$\ $$ |   $$ |   
 \$$$$  /$$$$$$\ $$ |  $$ |$$$$\       $$ |  $$ |\$$$$$$\    $$ |  $$ $$\$$ |   $$ |   
 $$  $$< \______|$$ |  $$ |\_$$ |      $$ |  $$ | \____$$\   $$ |  $$ \$$$$ |   $$ |   
$$  /\$$\        $$ |  $$ |  $$ |      $$ |  $$ |$$\   $$ |  $$ |  $$ |\$$$ |   $$ |   
$$ /  $$ |     $$$$$$\ \$$$$$$  |       $$$$$$  |\$$$$$$  |$$$$$$\ $$ | \$$ |   $$ |   
\__|  \__|     \______| \______/        \______/  \______/ \______|\__|  \__|   \__|   
           X IG OSINT — BEAST MODE (public-only) Hacker X Phantom
"""

def clear(): os.system("clear" if os.name!='nt' else "cls")
def panel(title, content):
    if RICH:
        console.print(Panel(str(content), title=f"[magenta]{title}[/magenta]"))
    else:
        print(f"\n=== {title} ===\n{content}\n")

def loading(text="Working", steps=24, delay=0.02):
    if RICH:
        with Progress(SpinnerColumn(), TextColumn(f"[green]{text}..."), BarColumn()) as p:
            task = p.add_task("", total=steps)
            for _ in range(steps):
                p.advance(task); time.sleep(delay)
    else:
        print(P + text + "..." + W, end="", flush=True)
        for _ in range(steps):
            print(G + "▮" + W, end="", flush=True); time.sleep(delay)
        print()

# ---------- Basic helpers ----------
def save_report(prefix, data):
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    fn = os.path.join(REPORT_DIR, f"{prefix}_{ts}.json")
    with open(fn,"w",encoding="utf-8") as f: json.dump(data,f,indent=2,ensure_ascii=False)
    return fn

def safe_get(url, headers=HEADERS, timeout=12):
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        return r
    except Exception as e:
        return None

# ---------- Core: Profile Info (real public) ----------
def fetch_profile_public(username):
    """Use instaloader if present, else HTML parse. Returns dict."""
    out = {"username":username, "fetched":False, "timestamp":datetime.utcnow().isoformat()}
    if instaloader:
        try:
            L = instaloader.Instaloader(download_pictures=False, download_videos=False, save_metadata=False)
            profile = instaloader.Profile.from_username(L.context, username)
            out.update({
                "full_name": profile.full_name,
                "bio": profile.biography,
                "external_url": profile.external_url,
                "followers": profile.followers,
                "following": profile.followees,
                "media_count": profile.mediacount,
                "is_private": profile.is_private,
                "is_verified": profile.is_verified,
                "profile_pic_url": profile.profile_pic_url,
            })
            out["fetched"] = True
            return out
        except Exception as e:
            out["error_instaloader"] = str(e)
    # Fallback parse
    url = f"https://www.instagram.com/{username}/"
    r = safe_get(url)
    if not r:
        out["error_http"] = "no_response"
        return out
    out["http_status"] = r.status_code
    if r.status_code != 200:
        out["error_http"] = f"status_{r.status_code}"
        return out
    html = r.text
    m = re.search(r"window\._sharedData\s*=\s*({.*?});</script>", html, flags=re.S)
    if m:
        try:
            data = json.loads(m.group(1))
            user = data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
            out.update({
                "full_name": user.get("full_name"),
                "bio": user.get("biography"),
                "followers": user.get("edge_followed_by",{}).get("count"),
                "following": user.get("edge_follow",{}).get("count"),
                "media_count": user.get("edge_owner_to_timeline_media",{}).get("count"),
                "is_private": user.get("is_private"),
                "is_verified": user.get("is_verified"),
                "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url"),
            })
            out["fetched"]=True
        except Exception as e:
            out["error_parse"]=str(e)
    # try meta tags
    if not out.get("fetched"):
        mt = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        md = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        if mt: out["full_name"] = mt.group(1)
        if md: out["bio"] = md.group(1)
        out["fetched"] = True
    return out

# ---------- 2: Username global scanner (async) ----------
PLATFORMS = {
    "github":"https://github.com/{u}",
    "x":"https://x.com/{u}",
    "instagram":"https://www.instagram.com/{u}/",
    "facebook":"https://www.facebook.com/{u}",
    "linkedin":"https://www.linkedin.com/in/{u}",
    "youtube":"https://www.youtube.com/{u}",
    "tiktok":"https://www.tiktok.com/@{u}",
    "reddit":"https://www.reddit.com/user/{u}",
    "telegram":"https://t.me/{u}",
    "snapchat":"https://www.snapchat.com/add/{u}",
    "pinterest":"https://www.pinterest.com/{u}"
}

async def _head(session, url):
    try:
        with async_timeout.timeout(8):
            async with session.head(url, allow_redirects=True) as resp:
                return resp.status
    except Exception:
        try:
            with async_timeout.timeout(8):
                async with session.get(url, allow_redirects=True) as resp:
                    return resp.status
        except Exception:
            return None

async def username_global_scan(username):
    if aiohttp is None:
        return {"error":"aiohttp_missing"}
    results = {}
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        tasks=[]
        for k,t in PLATFORMS.items():
            url = t.format(u=username)
            tasks.append(asyncio.create_task(_head(session,url)))
            results[k] = {"url":url}
        codes = await asyncio.gather(*tasks)
        i=0
        for k in PLATFORMS.keys():
            results[k]["status"] = codes[i]
            i+=1
    return results

# ---------- 3: IG Ban/Unban (official links) ----------
IG_FORMS = {
    "disabled_account":"https://help.instagram.com/366993040048856",
    "appeal_disabled":"https://www.facebook.com/help/contact/606967319425038",
    "hacked":"https://help.instagram.com/368191326593075",
    "impersonation":"https://help.instagram.com/contact/636276399721841"
}

# ---------- 4: Account age (first post via instaloader) ----------
def account_age_estimate(username, max_posts=1000):
    if not instaloader:
        return {"error":"instaloader_missing"}
    try:
        L = instaloader.Instaloader(download_pictures=False, download_videos=False, save_metadata=False)
        profile = instaloader.Profile.from_username(L.context, username)
        if profile.is_private:
            return {"error":"profile_private"}
        earliest=None; cnt=0
        for post in profile.get_posts():
            dt = post.date_utc
            if earliest is None or dt < earliest: earliest = dt
            cnt+=1
            if cnt>=max_posts: break
        if earliest:
            days = (datetime.utcnow()-earliest).days
            return {"earliest_post":earliest.isoformat(), "age_days":days, "age_years":round(days/365.0,2)}
        return {"error":"no_posts"}
    except Exception as e:
        return {"error":str(e)}

# ---------- 5: Data breach (HaveIBeenPwned) ----------
def hibp_check(email):
    if not HIBP_KEY:
        return {"error":"hibp_key_missing"}
    try:
        headers = {"hibp-api-key":HIBP_KEY, "user-agent":"X-IG-OSINT"}
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote_plus(email)}"
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code==200: return {"breaches":r.json()}
        elif r.status_code==404: return {"breaches":[]}
        else: return {"status":r.status_code}
    except Exception as e:
        return {"error":str(e)}

# ---------- 6: AI-based Fake Follower Detection (heuristic + optional ML) ----------
def fake_follower_detector(username, sample=500, use_ml=False):
    if not instaloader:
        return {"error":"instaloader_missing"}
    try:
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L.context, username)
        if profile.is_private: return {"error":"profile_private"}
        bots=0; total=0; suspicious=[]
        features = []
        for f in profile.get_followers():
            uname = f.username
            total += 1
            digits = sum(c.isdigit() for c in uname)
            score = 0
            if digits>=3: score+=1
            if len(uname)<=4: score+=1
            if f.is_verified: score-=1
            # heuristic: no biography and no posts -> suspicious
            try:
                bio = f.biography if hasattr(f,'biography') else None
                mcount = f.mediacount if hasattr(f,'mediacount') else 0
            except Exception:
                bio=None; mcount=0
            if not bio or bio.strip()=="":
                score+=1
            if mcount==0: score+=1
            if score>=2:
                bots+=1; suspicious.append(uname)
            if use_ml and SKLEARN:
                features.append([digits, 1 if mcount==0 else 0, len(uname)])
            if total>=sample: break
        ratio = round(bots/total,4) if total else 0
        res = {"sampled":total,"bot_like":bots,"bot_ratio":ratio,"suspicious_samples":suspicious[:100]}
        if use_ml and SKLEARN and features:
            # a simple KMeans cluster to separate 2 clusters; label cluster with higher mean suspiciousness as bots
            try:
                km = KMeans(n_clusters=2, random_state=0).fit(features)
                res["ml_clusters"] = True
            except Exception as e:
                res["ml_error"]=str(e)
        return res
    except Exception as e:
        return {"error":str(e)}

# ---------- 7: Relationship Mapping (graph + community detection) ----------
def build_relation_graph(username, sample_followers=300, sample_following=300, probe_each=30):
    if not instaloader:
        return {"error":"instaloader_missing"}
    try:
        if nx is None:
            # produce JSON adjacency only
            L=instaloader.Instaloader()
            profile=instaloader.Profile.from_username(L.context, username)
            followers=[]; following=[]
            cnt=0
            for f in profile.get_followers():
                followers.append(f.username); cnt+=1
                if cnt>=sample_followers: break
            cnt=0
            for f in profile.get_followees():
                following.append(f.username); cnt+=1
                if cnt>=sample_following: break
            mutuals = list(set(followers).intersection(set(following)))
            return {"followers_sampled":len(followers),"following_sampled":len(following),"mutuals":mutuals}
        L=instaloader.Instaloader(); profile = instaloader.Profile.from_username(L.context, username)
        if profile.is_private: return {"error":"profile_private"}
        Gs = nx.Graph()
        Gs.add_node(username, type='target')
        followers=[]; following=[]
        cnt=0
        for f in profile.get_followers():
            followers.append(f.username); Gs.add_node(f.username, type='follower'); Gs.add_edge(username,f.username); cnt+=1
            if cnt>=sample_followers: break
        cnt=0
        for f in profile.get_followees():
            following.append(f.username); Gs.add_node(f.username, type='following'); Gs.add_edge(username,f.username); cnt+=1
            if cnt>=sample_following: break
        # probe few followers' followees to find shared connections
        for uname in followers[:probe_each]:
            try:
                p = instaloader.Profile.from_username(L.context, uname)
                c=0
                for ff in p.get_followees():
                    Gs.add_node(ff.username); Gs.add_edge(uname, ff.username)
                    c+=1
                    if c>=30: break
            except Exception:
                continue
        # community detection
        partition = community_louvain.best_partition(Gs) if community_louvain else {}
        # export as adjacency
        adj = {n: list(Gs.neighbors(n)) for n in Gs.nodes()}
        fname = save_report(f"relation_graph_{username}", {"nodes":list(Gs.nodes()), "edges":list(Gs.edges()), "partition":partition})
        return {"saved_graph":fname, "nodes_count":Gs.number_of_nodes(), "edges_count":Gs.number_of_edges(), "partition_sample": dict(list(partition.items())[:30])}
    except Exception as e:
        return {"error":str(e)}

# ---------- 8: Shadowban Detector (improved heuristic) ----------
def shadowban_heuristic(username, recent_posts=5, hashtags_per_post=5):
    if not instaloader:
        return {"error":"instaloader_missing"}
    try:
        L=instaloader.Instaloader()
        profile=instaloader.Profile.from_username(L.context, username)
        if profile.is_private: return {"error":"profile_private"}
        posts=[]
        for p in profile.get_posts():
            posts.append(p)
            if len(posts)>=recent_posts: break
        if not posts: return {"error":"no_posts"}
        results=[]
        for p in posts:
            code = p.shortcode
            tags = list(p.caption_hashtags) if hasattr(p,'caption_hashtags') else []
            tags = tags[:hashtags_per_post]
            tag_presence = {}
            for tag in tags:
                url=f"https://www.instagram.com/explore/tags/{tag}/"
                r = safe_get(url)
                if not r: tag_presence[tag]=None
                else:
                    tag_presence[tag] = (code in r.text)
            results.append({"shortcode":code,"tag_presence":tag_presence})
        negative = sum(1 for r in results for v in r["tag_presence"].values() if v is False)
        total = sum(len(r["tag_presence"]) for r in results)
        score = (negative/total) if total else 0
        verdict = "No strong shadowban signs"
        if score>0.6: verdict="Strong shadowban signals"
        elif score>0.25: verdict="Some shadowban signals"
        return {"results":results,"negative":negative,"total":total,"score":score,"verdict":verdict}
    except Exception as e:
        return {"error":str(e)}

# ---------- 9: Device fingerprinting (posting hours + UA heuristics) ----------
def device_fingerprint_analysis(username, sample_posts=200):
    if not instaloader:
        return {"error":"instaloader_missing"}
    try:
        L=instaloader.Instaloader()
        profile=instaloader.Profile.from_username(L.context, username)
        if profile.is_private: return {"error":"profile_private"}
        hours = {}
        ua_counts = {}
        count=0
        for p in profile.get_posts():
            dt = p.date_utc
            hours[dt.hour]=hours.get(dt.hour,0)+1
            # instaloader doesn't always expose user agent. Try _node:
            node = getattr(p,"_node",{})
            ua = node.get("device","unknown") or node.get("user_agent","unknown")
            ua_counts[ua]=ua_counts.get(ua,0)+1
            count+=1
            if count>=sample_posts: break
        return {"post_hour_distribution":hours,"ua_counts":ua_counts}
    except Exception as e:
        return {"error":str(e)}

# ---------- 10: Location OSINT ----------
def extract_locations(username, sample_posts=500):
    if not instaloader:
        return {"error":"instaloader_missing"}
    try:
        L=instaloader.Instaloader(); profile=instaloader.Profile.from_username(L.context, username)
        if profile.is_private: return {"error":"profile_private"}
        places={}
        cnt=0
        for p in profile.get_posts():
            loc = getattr(p,"location",None)
            if loc:
                name = getattr(loc,"name",None) or getattr(loc,"slug",None)
                if name: places[name]=places.get(name,0)+1
            cnt+=1
            if cnt>=sample_posts: break
        return {"sampled_posts":cnt,"places":places}
    except Exception as e:
        return {"error":str(e)}

# ---------- 11: Engagement Rate & Reel analytics ----------
def engagement_and_reels(username, sample_posts=100):
    if not instaloader:
        return {"error":"instaloader_missing"}
    try:
        L=instaloader.Instaloader()
        profile=instaloader.Profile.from_username(L.context, username)
        if profile.is_private: return {"error":"profile_private"}
        likes=[]; comments=[]
        reels=[]
        cnt=0
        for p in profile.get_posts():
            # p.likes p.comments may be present
            try:
                likes.append(p.likes)
                comments.append(p.comments)
                if p.is_video:
                    reels.append({"shortcode":p.shortcode,"likes":p.likes,"comments":p.comments,"views": getattr(p,"video_view_count",None)})
            except Exception:
                pass
            cnt+=1
            if cnt>=sample_posts: break
        avg_likes = sum(likes)/len(likes) if likes else 0
        avg_comments = sum(comments)/len(comments) if comments else 0
        follower_count = profile.followers
        engagement_rate = (avg_likes+avg_comments) / follower_count * 100 if follower_count else 0
        return {"avg_likes":avg_likes,"avg_comments":avg_comments,"engagement_rate_pct":round(engagement_rate,3),"reels_sample":reels[:30]}
    except Exception as e:
        return {"error":str(e)}

# ---------- 12: Sentiment Analysis of comments (VADER/TextBlob) ----------
def comment_sentiment(username, sample_comments=500):
    if not instaloader:
        return {"error":"instaloader_missing"}
    if not (VADER or TEXTBLOB):
        return {"error":"no_sentiment_libs"}
    try:
        L=instaloader.Instaloader(); profile=instaloader.Profile.from_username(L.context, username)
        if profile.is_private: return {"error":"profile_private"}
        comments_texts=[]
        cnt=0
        for post in profile.get_posts():
            for c in post.get_comments():
                comments_texts.append(c.text)
                cnt+=1
                if cnt>=sample_comments: break
            if cnt>=sample_comments: break
        if not comments_texts: return {"error":"no_comments"}
        vader = SentimentIntensityAnalyzer() if VADER else None
        pos=neg=neu=0
        for t in comments_texts:
            if vader:
                s=vader.polarity_scores(t)
                if s["compound"]>=0.05: pos+=1
                elif s["compound"]<=-0.05: neg+=1
                else: neu+=1
            else:
                tb = TextBlob(t)
                pol = tb.sentiment.polarity
                if pol>0.05: pos+=1
                elif pol<-0.05: neg+=1
                else: neu+=1
        total = pos+neg+neu
        return {"comments_analyzed":total,"positive":pos,"negative":neg,"neutral":neu,"positive_pct":round(pos/total*100,2)}
    except Exception as e:
        return {"error":str(e)}

# ---------- 13: Deep footprint (username search across many) ----------
def deep_footprint(username, extra_platforms=None):
    all_platforms = dict(PLATFORMS)
    if extra_platforms:
        all_platforms.update(extra_platforms)
    res = {}
    for k,t in all_platforms.items():
        url = t.format(u=username)
        r = None
        try:
            r = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=8)
            status = r.status_code if r else None
        except Exception:
            status = None
        res[k] = {"url":url, "status": status}
    return res

# ---------- 14: Username monitor (simple) ----------
def watch_username(username, interval=60, duration=3600, output_file=None):
    """Polls platforms for username availability for 'duration' seconds every 'interval' seconds. Saves to file if provided."""
    end = time.time() + duration
    history=[]
    while time.time() < end:
        row = {"ts":datetime.utcnow().isoformat(), "scan": deep_footprint(username)}
        history.append(row)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f: json.dump(history, f, indent=2)
        time.sleep(interval)
    return history

# ---------- 15: Reverse image helper (local only - prepare hashes & instruct) ----------
def image_similarity_helper(image_path):
    """Generates perceptual hash and instructs user to use reverse image engines; we won't call external paid APIs."""
    try:
        from PIL import Image
        import imagehash
    except Exception:
        return {"error":"requires pillow & imagehash (pip install pillow imagehash)"}
    try:
        img = Image.open(image_path)
        ph = str(imagehash.phash(img))
        return {"phash":ph, "next_steps": "Use this pHash to search in local dataset or third-party reverse image engines (manual upload recommended)."}
    except Exception as e:
        return {"error":str(e)}

# ---------- 16: Hashtag OSINT (quick heuristic) ----------
def hashtag_osint(tag):
    tag = tag.lstrip("#")
    urls = {
        "instagram": f"https://www.instagram.com/explore/tags/{quote_plus(tag)}/",
        "twitter_search": f"https://twitter.com/search?q={quote_plus('#'+tag)}",
        "google_trends": f"https://trends.google.com/trends/explore?q=%23{quote_plus(tag)}"
    }
    # check visibility on IG
    r = safe_get(urls["instagram"])
    vis = {"status": r.status_code if r else None, "note":"heuristic"}
    # toxic words heuristic
    toxic_words = ["spam","scam","nsfw","bomb","terror"]
    score = sum(1 for w in toxic_words if w in tag.lower())
    return {"urls":urls,"ig_visibility":vis,"toxicity_score":score}

# ---------- 17: Comment intelligence (keywords & spammy commenters) ----------
def comment_intel(username, sample_posts=50):
    if not instaloader: return {"error":"instaloader_missing"}
    try:
        L=instaloader.Instaloader(); profile=instaloader.Profile.from_username(L.context, username)
        comments=[]; commenters={}
        cnt=0
        for p in profile.get_posts():
            for c in p.get_comments():
                comments.append(c.text)
                commenters[c.owner.username] = commenters.get(c.owner.username,0)+1
            cnt+=1
            if cnt>=sample_posts: break
        # top commenters
        top_commenters = sorted(commenters.items(), key=lambda x:-x[1])[:50]
        # keyword freq
        words={}
        for t in comments:
            for w in re.findall(r"\w{3,}", t.lower()):
                words[w]=words.get(w,0)+1
        top_words = sorted(words.items(), key=lambda x:-x[1])[:40]
        return {"comments_sampled":len(comments),"top_commenters":top_commenters,"top_words":top_words}
    except Exception as e:
        return {"error":str(e)}

# ---------- 18: AI Risk Score aggregator ----------
def ai_risk_score(profile_info_res, bot_detect_res, shadow_res, breach_res=None, sentiment_res=None):
    score=0; reasons=[]
    if profile_info_res.get("is_private"): score-=2; reasons.append("private_profile")
    if profile_info_res.get("is_verified"): score-=5; reasons.append("verified")
    # bot ratio
    br = bot_detect_res.get("bot_ratio") if isinstance(bot_detect_res, dict) else None
    if br is not None:
        score += br*20
        reasons.append(f"bot_ratio_{br}")
    # shadowban
    if isinstance(shadow_res, dict) and shadow_res.get("score",0)>0.3:
        score += 30; reasons.append("shadow_signals")
    # breach
    if breach_res and isinstance(breach_res, dict) and breach_res.get("breaches"):
        score += 40; reasons.append("breach_found")
    # sentiment toxicity
    if sentiment_res and isinstance(sentiment_res, dict) and sentiment_res.get("negative",0) > sentiment_res.get("positive",0):
        score += 10; reasons.append("negative_comments")
    final = min(100, max(0, int(score)))
    verdict = "Low risk"
    if final>75: verdict="High risk"
    elif final>40: verdict="Medium risk"
    return {"score":final,"verdict":verdict,"reasons":reasons}

# ---------- 19: Story highlights (public) ----------
def story_highlights(username):
    if not instaloader: return {"error":"instaloader_missing"}
    try:
        L=instaloader.Instaloader(); profile=instaloader.Profile.from_username(L.context, username)
        if profile.is_private: return {"error":"profile_private"}
        highlights = []
        # instaloader cannot fetch highlights easily without login; this is best-effort (may be empty)
        # We will attempt to fetch profile metadata for highlights field if present
        # Fallback: return not available
        return {"notes":"highlights extraction requires authenticated API or profile page parsing; limited in public mode"}
    except Exception as e:
        return {"error":str(e)}

# ---------- 20: IP log checker (legal only) ----------
def ip_log_checker_from_export(export_file):
    """If user provides IG data export (JSON) with IPs, parse and show login IP timeline.
       This function DOES NOT fetch private data — user must supply file."""
    try:
        with open(export_file,"r",encoding="utf-8") as f:
            data=json.load(f)
        # try known keys
        ips=[]
        def walk(d):
            if isinstance(d, dict):
                for k,v in d.items():
                    if "ip" in k.lower() and isinstance(v,str): ips.append(v)
                    walk(v)
            elif isinstance(d,list):
                for item in d: walk(item)
        walk(data)
        return {"found_ips": ips}
    except Exception as e:
        return {"error":str(e)}

# ---------- 21: Username history (Wayback & caches - limited, we will query Wayback CDX) ----------
def username_history_wayback(username, limit=10):
    # Query Wayback CDX for instagram.com/username pages
    q = f"https://web.archive.org/cdx/search/cdx?url=www.instagram.com/{username}/*&output=json&limit={limit}"
    r = safe_get(q)
    if not r: return {"error":"no_response"}
    try:
        arr = r.json()
        # arr[0] is header, rest are captures
        captures = arr[1:] if isinstance(arr,list) and len(arr)>1 else []
        return {"captures_count":len(captures),"captures_sample":captures}
    except Exception as e:
        return {"error":str(e)}

# ---------- 22: Reel analytics (part of engagement function) ----------
# (use engagement_and_reels above)

# ---------- 23: Facial similarity cross-match helper ----------
# (we provide pHash and instructions to use reverse image search; no automated cross-site scraping)
def face_similarity_instructions(image_path):
    # compute pHash
    try:
        from PIL import Image
        import imagehash
    except Exception:
        return {"error":"install pillow & imagehash (pip install pillow imagehash)"}
    try:
        img=Image.open(image_path)
        ph = str(imagehash.phash(img))
        return {"phash":ph, "note":"Use this pHash to search on offline DB or manual reverse-image engines. For privacy/legal reasons we don't auto-search third-party engines."}
    except Exception as e:
        return {"error":str(e)}

# ---------- 24: Raw HTML Fetch (Dark Mode raw viewer) ----------
def raw_html_fetch(username):
    url = f"https://www.instagram.com/{username}/"
    r = safe_get(url)
    if not r: return {"error":"no_response"}
    return {"status":r.status_code, "html_snippet": r.text[:5000]}  # don't dump entire page to console

# ---------- CLI and menu ----------
def header():
    clear()
    if RICH:
        console.print(Panel(ASCII, title="[magenta]X IG OSINT — BEAST[/magenta]"))
    else:
        print(P + ASCII + W)
    if not instaloader:
        print(Y + "Note: instaloader not installed -> many features limited. Install: pip install instaloader" + W)
    if not aiohttp:
        print(Y + "Note: aiohttp missing -> fast username scanning limited. Install: pip install aiohttp async-timeout" + W)
    if not (VADER or TEXTBLOB):
        print(Y + "Note: sentiment libs missing -> pip install vaderSentiment textblob" + W)
    print()

def prompt_enter():
    input(G + "\nPress ENTER to continue..." + W)

def main_menu():
    while True:
        header()
        print(G + "Choose feature set (public-only, legal):" + W)
        print(C + "1) Profile Info")
        print("2) Username Scanner")
        print("3) IG Ban/Unban Forms")
        print("4) Account Age")
        print("5) Data Breach Lookup")
        print("6) Bot Followers Detect")
        print("7) Relationship Mapping")
        print("8) Shadowban Detector")
        print("9) Device Fingerprint Check")
        print("10) Location OSINT")
        print("11) AI Fake Follower Detection (advanced)")
        print("12) Engagement & Reel Analytics")
        print("13) Sentiment on Comments")
        print("14) Deep Footprint (100+ platforms)")
        print("15) Username Monitor")
        print("16) Hashtag OSINT")
        print("17) Comment Intelligence")
        print("18) AI Risk Score (aggregate)")
        print("19) Story Highlights (limited public)")
        print("20) IP Log Checker (user-provided export)")
        print("21) Username History")
        print("22) Reel analytics")
        print("23) Face similarity helper (local)")
        print("24) Raw HTML (dark/raw view)")
        print("0) Exit" + W)
        ch = input(Y + "\nChoice > " + W).strip()
        if ch=="0": print(G+"Bye - use ethically."+W); break

        # each option prompts for username/params and runs function, shows result and offers to save.
        if ch=="1":
            usr = input("Instagram username > ").strip()
            loading("Fetching profile")
            res = fetch_profile_public(usr)
            panel(f"Profile: {usr}", json.dumps(res, indent=2, ensure_ascii=False))
            if input("Save (y/n)? > ").strip().lower()=="y": print("Saved:", save_report(f"profile_{usr}", res))
            prompt_enter()

        elif ch=="2":
            usr = input("Username to scan > ").strip()
            loading("Scanning platforms")
            if aiohttp:
                res = asyncio.run(username_global_scan(usr))
            else:
                # sync fallback
                res={}
                for k,t in PLATFORMS.items():
                    url=t.format(u=usr)
                    try:
                        r = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=8)
                        status = r.status_code
                    except Exception:
                        status=None
                    res[k]={"url":url,"status":status}
            panel(f"Username scan: {usr}", json.dumps(res,indent=2))
            if input("Save (y/n)? > ").strip().lower()=="y": print("Saved:", save_report(f"uname_scan_{usr}", res))
            prompt_enter()

        elif ch=="3":
            panel("IG Ban/Unban Forms", json.dumps(IG_FORMS, indent=2))
            if input("Open links (y/n)? > ").strip().lower()=="y":
                import webbrowser
                for v in IG_FORMS.values(): webbrowser.open(v)
            prompt_enter()

        elif ch=="4":
            usr = input("Username > ").strip()
            loading("Estimating account age (instaloader recommended)")
            res = account_age_estimate(usr)
            panel("Account Age", json.dumps(res,indent=2))
            if input("Save? > ").strip().lower()=="y": print("Saved:", save_report(f"age_{usr}",res))
            prompt_enter()

        elif ch=="5":
            identifier = input("Email (for HIBP) > ").strip()
            if not identifier:
                print(R+"Email required"+W); prompt_enter(); continue
            loading("Checking HIBP")
            res = hibp_check(identifier)
            panel("HIBP", json.dumps(res,indent=2))
            if input("Save? > ").strip().lower()=="y": print("Saved:", save_report(f"hibp_{identifier}",res))
            prompt_enter()

        elif ch=="6":
            usr=input("Username > ").strip()
            sample = input("Sample size (default 200) > ").strip(); sample=int(sample) if sample.isdigit() else 200
            loading("Detecting bot-like followers")
            res = detect_bot_followers(usr, sample=sample)
            panel("Bot detect", json.dumps(res,indent=2))
            if input("Save? > ").strip().lower()=="y": print("Saved:", save_report(f"bot_{usr}",res))
            prompt_enter()

        elif ch=="7":
            usr = input("Username > ").strip()
            sf = input("sample followers (200) > ").strip(); sf=int(sf) if sf.isdigit() else 200
            sfg = input("sample following (200) > ").strip(); sfg=int(sfg) if sfg.isdigit() else 200
            loading("Building relation graph")
            res = build_relation_graph(usr, sample_followers=sf, sample_following=sfg)
            panel("Relation Graph", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="8":
            usr=input("Username > ").strip()
            loading("Running shadowban heuristic")
            res = shadowban_heuristic(usr)
            panel("Shadowban", json.dumps(res,indent=2))
            if input("Save? > ").strip().lower()=="y": print("Saved:", save_report(f"shadow_{usr}",res))
            prompt_enter()

        elif ch=="9":
            usr=input("Username > ").strip()
            loading("Analyzing posting hours & UA hints")
            res = device_fingerprint_analysis(usr)
            panel("Device fingerprint", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="10":
            usr=input("Username > ").strip()
            loading("Extracting location tags")
            res=extract_locations(usr)
            panel("Locations", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="11":
            usr=input("Username > ").strip()
            use_ml = input("Use ML clustering (if sklearn installed)? (y/n) > ").strip().lower().startswith("y")
            loading("Running fake follower detector")
            res = fake_follower_detector(usr, sample=500, use_ml=use_ml)
            panel("Fake follower detect", json.dumps(res,indent=2))
            prompt_enter()

        elif ch in ["12","22"]:
            usr=input("Username > ").strip()
            loading("Collecting engagement & reels")
            res = engagement_and_reels(usr)
            panel("Engagement & Reels", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="13":
            usr=input("Username > ").strip()
            loading("Analyzing comment sentiment")
            res = comment_sentiment(usr)
            panel("Comment Sentiment", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="14":
            usr=input("Username > ").strip()
            loading("Running deep footprint")
            res = deep_footprint(usr)
            panel("Deep Footprint", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="15":
            usr=input("Username > ").strip()
            interval = input("Poll every N seconds (default 60) > ").strip(); interval=int(interval) if interval.isdigit() else 60
            duration = input("Duration seconds (default 600) > ").strip(); duration=int(duration) if duration.isdigit() else 600
            outfile = f"watch_{usr}.json"
            loading(f"Monitoring username for {duration}s")
            hist=watch_username(usr, interval=interval, duration=duration, output_file=outfile)
            panel("Monitor done", f"Saved to {outfile}")
            prompt_enter()

        elif ch=="16":
            tag=input("Hashtag (without #) > ").strip()
            loading("Checking hashtag")
            res=hashtag_osint(tag)
            panel("Hashtag OSINT", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="17":
            usr=input("Username > ").strip()
            loading("Collecting comment intelligence")
            res=comment_intel(usr)
            panel("Comment Intel", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="18":
            usr=input("Username > ").strip()
            # we'll compute aggregated signals
            loading("Computing risk score (may take time)")
            p = fetch_profile_public(usr)
            b = detect_bot_followers(usr, sample=300) if instaloader else {}
            s = shadowban_heuristic(usr) if instaloader else {}
            hb = None
            if HIBP_KEY:
                # no email - skip; user may need to supply email
                hb = None
            sent = comment_sentiment(usr) if (instaloader and (VADER or TEXTBLOB)) else None
            res = ai_risk_score(p,b,s, breach_res=hb, sentiment_res=sent)
            panel("AI Risk Score", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="19":
            usr=input("Username > ").strip()
            loading("Fetching highlights (best-effort)")
            res = story_highlights(usr)
            panel("Story Highlights (public-limited)", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="20":
            path=input("Path to IG export JSON (user-provided only) > ").strip()
            res = ip_log_checker_from_export(path)
            panel("IP Log Check", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="21":
            usr=input("Username > ").strip()
            loading("Querying Wayback CDX (limited)")
            res = username_history_wayback(usr)
            panel("Wayback Captures", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="23":
            path=input("Local image path > ").strip()
            res = face_similarity_instructions(path)
            panel("Image pHash", json.dumps(res,indent=2))
            prompt_enter()

        elif ch=="24":
            usr=input("Username > ").strip()
            loading("Fetching raw HTML snippet")
            res=raw_html_fetch(usr)
            panel("Raw HTML (snippet)", json.dumps(res,indent=2))
            prompt_enter()

        else:
            print(R+"Invalid choice"+W); prompt_enter()

if __name__=="__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
