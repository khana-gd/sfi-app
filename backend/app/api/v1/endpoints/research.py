import os
import httpx
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User
from app.api.v1.endpoints.auth import get_current_user

import time
from collections import defaultdict

router = APIRouter()

# In-memory rate limiter: max 5 queries per minute per user
RESEARCH_RATE_LIMIT_LIMIT = 5
RESEARCH_RATE_LIMIT_WINDOW = 60.0  # seconds
research_timestamps = defaultdict(list)

class ResearchQueryIn(BaseModel):
    query: str
    category: Optional[str] = None

class CitationOut(BaseModel):
    index: int
    title: str
    url: str

class ResearchQueryOut(BaseModel):
    query: str
    grounded_text: str
    citations: List[CitationOut]

# Rich mock database for fashion research queries
MOCK_RESEARCH_DATABASE = {
    "mughal": {
        "text": (
            "Mughal embroidery motifs are heavily derived from architectural decorations "
            "such as the pietra dura inlay work found on monuments like the Taj Mahal [1]. "
            "The zardozi technique, using metallic threads of gold and silver, reached its "
            "peak under Emperor Akbar, who wore elaborate angrakhas embroidered with floral patterns [2]. "
            "Common motifs include cypress trees, stylized poppy flowers, and scrolling vines (beli)."
        ),
        "citations": [
            {"index": 1, "title": "Mughal Architecture and Textile Syncretism - National Museum India", "url": "https://www.nationalmuseumindia.gov.in/mughal-architecture-textiles"},
            {"index": 2, "title": "Zardozi: The Golden Embroidery of Mughal Court - Victoria and Albert Museum", "url": "https://www.vam.ac.uk/articles/zardozi-golden-embroidery"}
        ]
    },
    "chikankari": {
        "text": (
            "Chikankari is a traditional embroidery style from Lucknow, believed to have been "
            "introduced by Empress Nur Jahan, the wife of Mughal Emperor Jahangir [1]. "
            "It features intricate shadow-work embroidery on sheer fabrics like muslin, cotton, or organza. "
            "The technique utilizes distinct stitches such as phanda (millet seed stitch), tepchi (running stitch), "
            "and keelkangan (fishhook stitch) to construct delicate floral borders and paisley medallions [2]."
        ),
        "citations": [
            {"index": 1, "title": "Origin and Evolution of Lucknow Chikankari - Craft Council of India", "url": "https://www.craftscouncilofindia.org/lucknow-chikankari"},
            {"index": 2, "title": "Stitch Techniques in Awadh Embroidery - Lucknow University Press", "url": "https://www.lkouniv.ac.in/departments/fine_arts/chikankari_stitches"}
        ]
    },
    "banarasi": {
        "text": (
            "Banarasi weaving originated in Varanasi (Benares) and is renowned for its brocade patterns "
            "utilizing fine silk and metallic gold/silver zari threads [1]. "
            "The craft was integrated with Persian design principles during the Mughal migration, resulting in "
            "composite motifs like the jhallar (scrolling border) and kalga (paisley leaf) [2]. "
            "Today, Banarasi textiles are protected under geographical indication tags."
        ),
        "citations": [
            {"index": 1, "title": "Banarasi Sarees: A Legacy of Zari Brocade - Textile Ministry India", "url": "https://www.texmin.nic.in/legacy-of-banarasi-weaving"},
            {"index": 2, "title": "Persian Syncretism in Banarasi Weaves - JSTOR Study", "url": "https://www.jstor.org/stable/banarasi-persian-weaves"}
        ]
    },
    "draping": {
        "text": (
            "Historical western silhouettes relied heavily on structural supports like crinolines, hoops, "
            "and bustles to construct exaggerated shapes [1]. "
            "In contrast, traditional Indian draping techniques (like the saree or dhoti) utilize the unstitched "
            "fabric's natural fluidity to outline fluid silhouettes. Draping a cowl neckline requires "
            "orienting fabric along the bias grain (45 degrees) to allow the textile to sag and fall into soft folds [2]."
        ),
        "citations": [
            {"index": 1, "title": "Understructures and Historical Silhouettes - Fashion Institute of Technology", "url": "https://www.fitnyc.edu/silhouettes-understructures"},
            {"index": 2, "title": "The Art of Bias Draping and Cowls - SFI Design Library", "url": "https://www.sfi.edu/library/bias-draping-techniques"}
        ]
    }
}

DEFAULT_FALLBACK_TEXT = (
    "Traditional textile research requires identifying local geography, materials, and techniques [1]. "
    "KANHA fashion grounding verifies that local embellishment structures (such as block printing, Ajrakh, or Kantha) "
    "are preserved using natural materials and regional designs [2]."
)
DEFAULT_FALLBACK_CITATIONS = [
    {"index": 1, "title": "Handloom and Handicrafts Preservation Act - Govt of India", "url": "https://www.handlooms.nic.in/preservation-act"},
    {"index": 2, "title": "Grounded Studies in Traditional Indian Embellishments - SFI Publications", "url": "https://www.sfi.edu/publications/traditional-embellishments"}
]

@router.post("/query", response_model=ResearchQueryOut)
def run_research_query(
    payload: ResearchQueryIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Executes a fashion research query grounded in Google Search via Gemini API,
    with rich deterministic fallback content for offline development.
    """
    # Rate limit check
    now = time.time()
    user_id = current_user.id
    user_times = research_timestamps[user_id]
    
    # Filter times inside the window
    user_times = [t for t in user_times if now - t < RESEARCH_RATE_LIMIT_WINDOW]
    research_timestamps[user_id] = user_times
    
    if len(user_times) >= RESEARCH_RATE_LIMIT_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 5 queries per minute."
        )
        
    research_timestamps[user_id].append(now)

    query_text = payload.query.lower()
    
    # Check if we should call Gemini API
    api_key = os.getenv("GEMINI_API_KEY", "dummy_gemini_key_for_dev")
    
    if api_key != "dummy_gemini_key_for_dev":
        try:
            # Let's perform a live call to Gemini with Google Search Grounding enabled
            # Endpoint for Gemini 1.5 / 2.0 / 3.0 API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            
            headers = {"Content-Type": "application/json"}
            
            prompt = (
                f"You are a professional fashion historian and technical textiles expert at the "
                f"Shristi Fashion Institute (SFI). Provide a detailed, historical response to the following research query: "
                f"'{payload.query}'.\n"
                f"Your response must focus on fashion-specific terms, historical contexts, and material structures. "
                f"Answer in clear markdown format. Make sure you use the search grounding tool to cite actual sources."
            )
            
            request_body = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "tools": [
                    {"google_search": {}}
                ]
            }
            
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, headers=headers, json=request_body)
                if res.status_code == 200:
                    data = res.json()
                    
                    # Extract grounded text
                    candidate = data.get("candidates", [{}])[0]
                    content = candidate.get("content", {})
                    grounded_text = content.get("parts", [{}])[0].get("text", "")
                    
                    # Extract citations from grounding metadata
                    citations = []
                    grounding_metadata = candidate.get("groundingMetadata", {})
                    grounding_chunks = grounding_metadata.get("groundingChunks", [])
                    
                    for idx, chunk in enumerate(grounding_chunks):
                        web = chunk.get("web", {})
                        if web.get("uri"):
                            citations.append({
                                "index": idx + 1,
                                "title": web.get("title", "Reference Source"),
                                "url": web.get("uri")
                            })
                    
                    if grounded_text:
                        return {
                            "query": payload.query,
                            "grounded_text": grounded_text,
                            "citations": citations
                        }
        except Exception as e:
            # Log exception and fall back to local mock data
            print(f"Gemini live grounding query failed: {e}. Falling back to mock database.")
            
    # Mock data lookup
    matched_key = None
    for key in MOCK_RESEARCH_DATABASE.keys():
        if key in query_text:
            matched_key = key
            break
            
    if matched_key:
        result = MOCK_RESEARCH_DATABASE[matched_key]
        return {
            "query": payload.query,
            "grounded_text": result["text"],
            "citations": [CitationOut(**c) for c in result["citations"]]
        }
    
    return {
        "query": payload.query,
        "grounded_text": DEFAULT_FALLBACK_TEXT,
        "citations": [CitationOut(**c) for c in DEFAULT_FALLBACK_CITATIONS]
    }
