import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class Database:
    """
    Database manager for conversation history and query templates.
    """
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
    
    def get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.database_url)
    
    # Conversation History Methods
    
    def save_research_result(
        self, 
        query: str, 
        answer: str, 
        tasks_completed: List[Dict], 
        stats: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> int:
        """Save a research result to conversation history."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO conversation_history 
                    (query, answer, tasks_completed, stats, session_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        query,
                        answer,
                        json.dumps(tasks_completed),
                        json.dumps(stats),
                        session_id or str(uuid.uuid4())
                    )
                )
                result_id = cur.fetchone()[0]
                conn.commit()
                return result_id
    
    def get_conversation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, query, answer, tasks_completed, stats, created_at, session_id
                    FROM conversation_history
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,)
                )
                results = cur.fetchall()
                # Convert to regular dicts and parse JSON fields
                return [
                    {
                        **dict(row),
                        'tasks_completed': json.loads(row['tasks_completed']) if row['tasks_completed'] else [],
                        'stats': json.loads(row['stats']) if row['stats'] else {}
                    }
                    for row in results
                ]
    
    def get_research_by_id(self, research_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific research result by ID."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, query, answer, tasks_completed, stats, created_at, session_id
                    FROM conversation_history
                    WHERE id = %s
                    """,
                    (research_id,)
                )
                row = cur.fetchone()
                if row:
                    return {
                        **dict(row),
                        'tasks_completed': json.loads(row['tasks_completed']) if row['tasks_completed'] else [],
                        'stats': json.loads(row['stats']) if row['stats'] else {}
                    }
                return None
    
    def search_conversation_history(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search conversation history by query text."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, query, answer, tasks_completed, stats, created_at, session_id
                    FROM conversation_history
                    WHERE query ILIKE %s OR answer ILIKE %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (f'%{search_term}%', f'%{search_term}%', limit)
                )
                results = cur.fetchall()
                return [
                    {
                        **dict(row),
                        'tasks_completed': json.loads(row['tasks_completed']) if row['tasks_completed'] else [],
                        'stats': json.loads(row['stats']) if row['stats'] else {}
                    }
                    for row in results
                ]
    
    # Query Templates Methods
    
    def save_template(
        self, 
        name: str, 
        query_text: str, 
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> int:
        """Save a new query template."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO query_templates 
                    (name, query_text, category, description)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (name, query_text, category, description)
                )
                template_id = cur.fetchone()[0]
                conn.commit()
                return template_id
    
    def get_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get query templates, optionally filtered by category."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if category:
                    cur.execute(
                        """
                        SELECT id, name, query_text, category, description, created_at
                        FROM query_templates
                        WHERE category = %s
                        ORDER BY name
                        """,
                        (category,)
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, name, query_text, category, description, created_at
                        FROM query_templates
                        ORDER BY category, name
                        """
                    )
                return [dict(row) for row in cur.fetchall()]
    
    def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, name, query_text, category, description, created_at
                    FROM query_templates
                    WHERE id = %s
                    """,
                    (template_id,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
    
    def update_template(
        self, 
        template_id: int, 
        name: Optional[str] = None,
        query_text: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """Update an existing template."""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if query_text is not None:
            updates.append("query_text = %s")
            params.append(query_text)
        if category is not None:
            updates.append("category = %s")
            params.append(category)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(template_id)
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE query_templates
                    SET {', '.join(updates)}
                    WHERE id = %s
                    """,
                    params
                )
                conn.commit()
                return cur.rowcount > 0
    
    def delete_template(self, template_id: int) -> bool:
        """Delete a template."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM query_templates WHERE id = %s",
                    (template_id,)
                )
                conn.commit()
                return cur.rowcount > 0
    
    def get_template_categories(self) -> List[str]:
        """Get all unique template categories."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT category 
                    FROM query_templates 
                    WHERE category IS NOT NULL
                    ORDER BY category
                    """
                )
                return [row[0] for row in cur.fetchall()]
