"""
Memory Integration for WaddleAI
Provides conversation memory using mem0 and ChromaDB
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
import numpy as np
from sentence_transformers import SentenceTransformer

# Optional mem0 import (if available)
try:
    import mem0
    HAS_MEM0 = True
except ImportError:
    mem0 = None
    HAS_MEM0 = False

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Memory entry structure"""
    id: str
    user_id: int
    organization_id: int
    session_id: Optional[str]
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]]
    created_at: datetime
    relevance_score: float = 0.0


@dataclass
class ConversationContext:
    """Conversation context with memory"""
    user_id: int
    organization_id: int
    session_id: Optional[str]
    recent_messages: List[Dict[str, str]]
    relevant_memories: List[MemoryEntry]
    conversation_summary: Optional[str] = None


class ChromaDBMemoryStore:
    """ChromaDB-based memory storage"""
    
    def __init__(self, persist_directory: str = "./chroma_data", collection_name: str = "waddleai_memory"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.encoder = None
        
        # Initialize embedding model
        self._init_encoder()
    
    def _init_encoder(self):
        """Initialize sentence transformer for embeddings"""
        try:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Initialized SentenceTransformer encoder")
        except Exception as e:
            logger.error(f"Failed to initialize encoder: {e}")
            self.encoder = None
    
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing memory collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "WaddleAI conversation memory"}
                )
                logger.info(f"Created new memory collection: {self.collection_name}")
            
            logger.info("ChromaDB memory store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self.encoder:
            return None
        
        try:
            embedding = self.encoder.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def store_memory(self, entry: MemoryEntry) -> bool:
        """Store memory entry"""
        try:
            if not self.collection:
                await self.initialize()
            
            # Generate embedding if not provided
            if entry.embedding is None:
                entry.embedding = self._generate_embedding(entry.content)
            
            # Prepare metadata
            metadata = {
                **entry.metadata,
                "user_id": entry.user_id,
                "organization_id": entry.organization_id,
                "session_id": entry.session_id or "",
                "created_at": entry.created_at.isoformat(),
                "content_length": len(entry.content)
            }
            
            # Store in ChromaDB
            self.collection.add(
                ids=[entry.id],
                documents=[entry.content],
                metadatas=[metadata],
                embeddings=[entry.embedding] if entry.embedding else None
            )
            
            logger.debug(f"Stored memory entry: {entry.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False
    
    async def search_memories(
        self,
        query: str,
        user_id: int,
        organization_id: int,
        session_id: Optional[str] = None,
        limit: int = 10,
        min_relevance: float = 0.7
    ) -> List[MemoryEntry]:
        """Search for relevant memories"""
        try:
            if not self.collection:
                await self.initialize()
            
            # Build where clause
            where_clause = {
                "user_id": user_id,
                "organization_id": organization_id
            }
            
            if session_id:
                where_clause["session_id"] = session_id
            
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Search in ChromaDB
            if query_embedding:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    where=where_clause,
                    n_results=limit,
                    include=["documents", "metadatas", "distances"]
                )
            else:
                # Fallback to text search if no embedding
                results = self.collection.query(
                    query_texts=[query],
                    where=where_clause,
                    n_results=limit,
                    include=["documents", "metadatas", "distances"]
                )
            
            # Convert results to MemoryEntry objects
            memories = []
            if results and results['documents']:
                for i in range(len(results['documents'][0])):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if results.get('distances') else 0.0
                    relevance_score = 1.0 - distance  # Convert distance to relevance
                    
                    if relevance_score >= min_relevance:
                        memory = MemoryEntry(
                            id=results['ids'][0][i],
                            user_id=metadata['user_id'],
                            organization_id=metadata['organization_id'],
                            session_id=metadata.get('session_id'),
                            content=results['documents'][0][i],
                            metadata={k: v for k, v in metadata.items() 
                                    if k not in ['user_id', 'organization_id', 'session_id', 'created_at']},
                            embedding=None,
                            created_at=datetime.fromisoformat(metadata['created_at']),
                            relevance_score=relevance_score
                        )
                        memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def get_recent_memories(
        self,
        user_id: int,
        organization_id: int,
        session_id: Optional[str] = None,
        hours: int = 24,
        limit: int = 20
    ) -> List[MemoryEntry]:
        """Get recent memories"""
        try:
            if not self.collection:
                await self.initialize()
            
            # Calculate cutoff time
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            # Build where clause
            where_clause = {
                "user_id": user_id,
                "organization_id": organization_id
            }
            
            if session_id:
                where_clause["session_id"] = session_id
            
            # Query recent memories
            results = self.collection.get(
                where=where_clause,
                include=["documents", "metadatas"],
                limit=limit
            )
            
            # Convert and filter by time
            memories = []
            if results and results['documents']:
                for i in range(len(results['documents'])):
                    metadata = results['metadatas'][i]
                    created_at = datetime.fromisoformat(metadata['created_at'])
                    
                    if created_at >= cutoff:
                        memory = MemoryEntry(
                            id=results['ids'][i],
                            user_id=metadata['user_id'],
                            organization_id=metadata['organization_id'],
                            session_id=metadata.get('session_id'),
                            content=results['documents'][i],
                            metadata={k: v for k, v in metadata.items() 
                                    if k not in ['user_id', 'organization_id', 'session_id', 'created_at']},
                            embedding=None,
                            created_at=created_at
                        )
                        memories.append(memory)
            
            # Sort by created_at descending
            memories.sort(key=lambda m: m.created_at, reverse=True)
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get recent memories: {e}")
            return []
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory"""
        try:
            if not self.collection:
                await self.initialize()
            
            self.collection.delete(ids=[memory_id])
            logger.debug(f"Deleted memory: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    async def cleanup_old_memories(self, days: int = 90) -> int:
        """Cleanup memories older than specified days"""
        try:
            if not self.collection:
                await self.initialize()
            
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Get all memories to check dates
            all_results = self.collection.get(include=["metadatas"])
            
            old_ids = []
            if all_results and all_results['ids']:
                for i, metadata in enumerate(all_results['metadatas']):
                    created_at = datetime.fromisoformat(metadata['created_at'])
                    if created_at < cutoff:
                        old_ids.append(all_results['ids'][i])
            
            # Delete old memories
            if old_ids:
                self.collection.delete(ids=old_ids)
                logger.info(f"Cleaned up {len(old_ids)} old memories")
            
            return len(old_ids)
            
        except Exception as e:
            logger.error(f"Failed to cleanup memories: {e}")
            return 0


class WaddleAIMemoryManager:
    """Main memory management system for WaddleAI"""
    
    def __init__(self, db, memory_store: ChromaDBMemoryStore):
        self.db = db
        self.memory_store = memory_store
        self.mem0_client = None
        
        # Initialize mem0 if available
        if HAS_MEM0:
            try:
                self.mem0_client = mem0.MemoryClient()
                logger.info("Initialized mem0 client")
            except Exception as e:
                logger.warning(f"Failed to initialize mem0: {e}")
    
    async def initialize(self):
        """Initialize memory manager"""
        await self.memory_store.initialize()
        logger.info("Memory manager initialized")
    
    async def add_conversation_turn(
        self,
        user_id: int,
        organization_id: int,
        messages: List[Dict[str, str]],
        response: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a conversation turn to memory"""
        try:
            # Combine user message and assistant response
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            last_user_message = user_messages[-1]['content'] if user_messages else ""
            
            # Create conversation context
            conversation_text = f"User: {last_user_message}\nAssistant: {response}"
            
            # Generate memory ID
            memory_id = f"conv_{user_id}_{int(datetime.utcnow().timestamp() * 1000)}"
            
            # Prepare metadata
            memory_metadata = {
                "type": "conversation",
                "message_count": len(messages),
                "response_length": len(response),
                **(metadata or {})
            }
            
            # Create memory entry
            entry = MemoryEntry(
                id=memory_id,
                user_id=user_id,
                organization_id=organization_id,
                session_id=session_id,
                content=conversation_text,
                metadata=memory_metadata,
                embedding=None,
                created_at=datetime.utcnow()
            )
            
            # Store in memory store
            success = await self.memory_store.store_memory(entry)
            
            # Also try to store in mem0 if available
            if self.mem0_client and success:
                try:
                    self.mem0_client.add(
                        conversation_text,
                        user_id=str(user_id),
                        metadata={
                            "organization_id": organization_id,
                            "session_id": session_id or "",
                            **memory_metadata
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to store in mem0: {e}")
            
            if success:
                logger.debug(f"Added conversation turn to memory for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add conversation turn: {e}")
            return False
    
    async def get_conversation_context(
        self,
        user_id: int,
        organization_id: int,
        current_messages: List[Dict[str, str]],
        session_id: Optional[str] = None,
        context_limit: int = 5
    ) -> ConversationContext:
        """Get conversation context with relevant memories"""
        try:
            # Extract query from current messages
            user_messages = [msg['content'] for msg in current_messages if msg.get('role') == 'user']
            query = " ".join(user_messages[-2:])  # Use last 2 user messages as query
            
            # Search for relevant memories
            relevant_memories = await self.memory_store.search_memories(
                query=query,
                user_id=user_id,
                organization_id=organization_id,
                session_id=session_id,
                limit=context_limit
            )
            
            # Get recent memories for additional context
            recent_memories = await self.memory_store.get_recent_memories(
                user_id=user_id,
                organization_id=organization_id,
                session_id=session_id,
                hours=24,
                limit=3
            )
            
            # Combine and deduplicate memories
            all_memories = {m.id: m for m in relevant_memories + recent_memories}
            combined_memories = list(all_memories.values())
            
            # Sort by relevance and recency
            combined_memories.sort(
                key=lambda m: (m.relevance_score, m.created_at.timestamp()),
                reverse=True
            )
            
            # Generate conversation summary if we have memories
            conversation_summary = None
            if combined_memories:
                conversation_summary = await self._generate_conversation_summary(combined_memories)
            
            return ConversationContext(
                user_id=user_id,
                organization_id=organization_id,
                session_id=session_id,
                recent_messages=current_messages,
                relevant_memories=combined_memories[:context_limit],
                conversation_summary=conversation_summary
            )
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return ConversationContext(
                user_id=user_id,
                organization_id=organization_id,
                session_id=session_id,
                recent_messages=current_messages,
                relevant_memories=[],
                conversation_summary=None
            )
    
    async def _generate_conversation_summary(self, memories: List[MemoryEntry]) -> str:
        """Generate a summary of relevant conversation memories"""
        if not memories:
            return ""
        
        # Simple summary based on most relevant memories
        summary_parts = []
        for memory in memories[:3]:  # Use top 3 memories
            # Extract key information
            content = memory.content
            if len(content) > 200:
                content = content[:200] + "..."
            summary_parts.append(content)
        
        return " | ".join(summary_parts)
    
    async def enhance_messages_with_context(
        self,
        messages: List[Dict[str, str]],
        context: ConversationContext
    ) -> List[Dict[str, str]]:
        """Enhance messages with memory context"""
        try:
            if not context.relevant_memories and not context.conversation_summary:
                return messages
            
            # Build context information
            context_parts = []
            
            if context.conversation_summary:
                context_parts.append(f"Previous conversation context: {context.conversation_summary}")
            
            if context.relevant_memories:
                memory_summaries = []
                for memory in context.relevant_memories:
                    # Format memory for context
                    timestamp = memory.created_at.strftime("%Y-%m-%d %H:%M")
                    content = memory.content
                    if len(content) > 300:
                        content = content[:300] + "..."
                    memory_summaries.append(f"[{timestamp}] {content}")
                
                context_parts.append("Relevant conversation history:\n" + "\n".join(memory_summaries))
            
            # Add context to system message or create new system message
            context_text = "\n\n".join(context_parts)
            
            enhanced_messages = []
            has_system_message = False
            
            for msg in messages:
                if msg.get('role') == 'system':
                    # Enhance existing system message
                    enhanced_content = msg['content'] + f"\n\n{context_text}"
                    enhanced_messages.append({
                        'role': 'system',
                        'content': enhanced_content
                    })
                    has_system_message = True
                else:
                    enhanced_messages.append(msg)
            
            # If no system message, add context as new system message
            if not has_system_message:
                enhanced_messages.insert(0, {
                    'role': 'system',
                    'content': f"Context from previous conversations:\n{context_text}"
                })
            
            return enhanced_messages
            
        except Exception as e:
            logger.error(f"Failed to enhance messages with context: {e}")
            return messages
    
    async def cleanup_old_memories(self, days: int = 90) -> int:
        """Cleanup old memories"""
        return await self.memory_store.cleanup_old_memories(days)
    
    async def get_memory_stats(self, user_id: int, organization_id: int) -> Dict[str, Any]:
        """Get memory statistics for user/organization"""
        try:
            # Get recent memories to calculate stats
            recent_memories = await self.memory_store.get_recent_memories(
                user_id=user_id,
                organization_id=organization_id,
                hours=24 * 30,  # Last 30 days
                limit=1000
            )
            
            # Calculate statistics
            total_memories = len(recent_memories)
            avg_length = sum(len(m.content) for m in recent_memories) / max(total_memories, 1)
            
            # Group by day
            daily_counts = {}
            for memory in recent_memories:
                day = memory.created_at.date().isoformat()
                daily_counts[day] = daily_counts.get(day, 0) + 1
            
            return {
                "total_memories": total_memories,
                "average_content_length": round(avg_length, 2),
                "daily_counts": daily_counts,
                "oldest_memory": min(recent_memories, key=lambda m: m.created_at).created_at.isoformat() if recent_memories else None,
                "newest_memory": max(recent_memories, key=lambda m: m.created_at).created_at.isoformat() if recent_memories else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {
                "total_memories": 0,
                "average_content_length": 0,
                "daily_counts": {},
                "oldest_memory": None,
                "newest_memory": None
            }


def create_memory_manager(db, persist_directory: str = "./chroma_data") -> WaddleAIMemoryManager:
    """Factory function to create memory manager"""
    memory_store = ChromaDBMemoryStore(persist_directory=persist_directory)
    return WaddleAIMemoryManager(db, memory_store)