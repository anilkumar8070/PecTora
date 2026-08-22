import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database.models import Memory, MemoryTypeEnum

logger = logging.getLogger(__name__)

class MemoryEngine:
    """
    Handles storage and structured retrieval of personal memories without a Vector DB.
    Implements relevance scoring and contradiction resolution.
    """
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_memory(self, user_id: int, content: str, type: MemoryTypeEnum, source: str, confidence: float = 1.0) -> Memory:
        mem = Memory(
            user_id=user_id,
            content=content,
            type=type,
            source=source,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(mem)
        self.db.commit()
        return mem

    def retrieve_relevant(self, user_id: int, query: str, top_k: int = 5) -> List[Memory]:
        """
        Retrieves memories relevant to the query.
        Applies keyword scoring, source prioritization, and contradiction filtering.
        """
        import re
        
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        if not query_words:
            return []
            
        all_memories = self.db.query(Memory).filter(Memory.user_id == user_id).all()
        
        scored_memories = []
        for mem in all_memories:
            content_lower = mem.content.lower()
            content_words = set(re.findall(r'\b\w+\b', content_lower))
            
            # 1. Relevance: Intersection of words
            overlap = len(query_words.intersection(content_words))
            if overlap == 0:
                continue
                
            base_score = float(overlap)
            
            # 2. Source & Type Weighting
            weight = 1.0
            if mem.source == "EXPLICIT_USER_STATEMENT":
                weight = 2.0
            elif mem.type == MemoryTypeEnum.INFERENCE:
                weight = 0.5
                
            final_score = base_score * weight * mem.confidence
            scored_memories.append({
                "score": final_score,
                "memory": mem,
                "content_words": content_words
            })
            
        # 3. Sort by score DESC, then timestamp DESC
        scored_memories.sort(key=lambda x: (x["score"], x["memory"].timestamp), reverse=True)
        
        # 4. Contradiction Resolution
        final_memories = []
        
        for item in scored_memories:
            mem = item["memory"]
            mem_words = item["content_words"]
            is_contradicted = False
            
            for approved_item in final_memories:
                approved_mem = approved_item["memory"]
                approved_words = approved_item["content_words"]
                
                # Check if they share a relevant keyword from the query
                shared_query_keywords = query_words.intersection(mem_words).intersection(approved_words)
                
                if shared_query_keywords:
                    # Rule 1: Explicit > Inference
                    if approved_mem.source == "EXPLICIT_USER_STATEMENT" and mem.source != "EXPLICIT_USER_STATEMENT":
                        is_contradicted = True
                        break
                        
                    # Rule 2: Newer > Older
                    if approved_mem.source == mem.source:
                        if approved_mem.timestamp > mem.timestamp:
                            is_contradicted = True
                            break
                            
            if not is_contradicted:
                final_memories.append(item)
                
            if len(final_memories) >= top_k:
                break
                
        return [item["memory"] for item in final_memories]
