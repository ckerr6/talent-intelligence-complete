"""
Recruiter Workflow API Router
Provides endpoints for candidate lists, notes, tags, and saved searches
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from psycopg2.extras import RealDictCursor
import json

from api.dependencies import get_db

router = APIRouter(prefix="/api/workflow", tags=["recruiter_workflow"])


# Pydantic models
class CreateListRequest(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: Optional[str] = None


class UpdateListRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AddToListRequest(BaseModel):
    person_id: str
    notes: Optional[str] = None


class CreateNoteRequest(BaseModel):
    person_id: str
    note_text: str
    user_id: Optional[str] = None
    note_type: str = 'general'  # 'general', 'call', 'meeting', 'screen', 'email', 'timing', 'reference', 'ai_generated'
    note_category: Optional[str] = 'general'
    priority: str = 'normal'  # 'low', 'normal', 'high', 'urgent'
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class AddTagRequest(BaseModel):
    person_id: str
    tag: str
    tag_type: str = 'manual'


class SaveSearchRequest(BaseModel):
    name: str
    filters: Dict[str, Any]
    user_id: Optional[str] = None


# ===== CANDIDATE LISTS =====

@router.post("/lists")
async def create_list(
    request: CreateListRequest,
    db=Depends(get_db)
):
    """
    Create a new candidate list
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            INSERT INTO candidate_lists (name, description, user_id, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            RETURNING list_id, name, description, created_at, updated_at
        """, (request.name, request.description, request.user_id))
        
        list_data = dict(cursor.fetchone())
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'list': list_data
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating list: {str(e)}")


@router.get("/lists")
async def get_lists(
    user_id: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Get all candidate lists for a user
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                cl.*,
                COUNT(clm.person_id) as member_count
            FROM candidate_lists cl
            LEFT JOIN candidate_list_members clm ON cl.list_id = clm.list_id
        """
        
        if user_id:
            query += " WHERE cl.user_id = %s"
            cursor.execute(query + " GROUP BY cl.list_id ORDER BY cl.updated_at DESC", (user_id,))
        else:
            cursor.execute(query + " GROUP BY cl.list_id ORDER BY cl.updated_at DESC")
        
        lists = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        return {
            'success': True,
            'count': len(lists),
            'lists': lists
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching lists: {str(e)}")


@router.get("/lists/{list_id}")
async def get_list(
    list_id: str,
    db=Depends(get_db)
):
    """
    Get a specific list with all members
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Get list details
        cursor.execute("""
            SELECT * FROM candidate_lists WHERE list_id = %s
        """, (list_id,))
        
        list_data = cursor.fetchone()
        
        if not list_data:
            raise HTTPException(status_code=404, detail="List not found")
        
        list_data = dict(list_data)
        
        # Get members
        cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                p.headline,
                p.location,
                p.linkedin_url,
                clm.added_at,
                clm.notes
            FROM candidate_list_members clm
            JOIN person p ON clm.person_id = p.person_id
            WHERE clm.list_id = %s
            ORDER BY clm.added_at DESC
        """, (list_id,))
        
        members = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        return {
            'success': True,
            'list': {
                **list_data,
                'members': members,
                'member_count': len(members)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching list: {str(e)}")


@router.put("/lists/{list_id}")
async def update_list(
    list_id: str,
    request: UpdateListRequest,
    db=Depends(get_db)
):
    """
    Update list name or description
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        updates = []
        params = []
        
        if request.name:
            updates.append("name = %s")
            params.append(request.name)
        
        if request.description is not None:
            updates.append("description = %s")
            params.append(request.description)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = NOW()")
        params.append(list_id)
        
        query = f"UPDATE candidate_lists SET {', '.join(updates)} WHERE list_id = %s RETURNING *"
        
        cursor.execute(query, params)
        updated_list = dict(cursor.fetchone())
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'list': updated_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating list: {str(e)}")


@router.delete("/lists/{list_id}")
async def delete_list(
    list_id: str,
    db=Depends(get_db)
):
    """
    Delete a candidate list (cascade deletes members)
    """
    
    try:
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM candidate_lists WHERE list_id = %s", (list_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="List not found")
        
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'message': 'List deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting list: {str(e)}")


@router.post("/lists/{list_id}/members")
async def add_to_list(
    list_id: str,
    request: AddToListRequest,
    db=Depends(get_db)
):
    """
    Add a person to a candidate list
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Update list updated_at timestamp
        cursor.execute("UPDATE candidate_lists SET updated_at = NOW() WHERE list_id = %s", (list_id,))
        
        cursor.execute("""
            INSERT INTO candidate_list_members (list_id, person_id, notes, added_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (list_id, person_id) DO UPDATE
            SET notes = EXCLUDED.notes
            RETURNING *
        """, (list_id, request.person_id, request.notes))
        
        member = dict(cursor.fetchone())
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'member': member
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding to list: {str(e)}")


@router.delete("/lists/{list_id}/members/{person_id}")
async def remove_from_list(
    list_id: str,
    person_id: str,
    db=Depends(get_db)
):
    """
    Remove a person from a candidate list
    """
    
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            DELETE FROM candidate_list_members 
            WHERE list_id = %s AND person_id = %s
        """, (list_id, person_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Person not in list")
        
        # Update list updated_at timestamp
        cursor.execute("UPDATE candidate_lists SET updated_at = NOW() WHERE list_id = %s", (list_id,))
        
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'message': 'Person removed from list'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing from list: {str(e)}")


# ===== NOTES =====

@router.post("/notes")
async def create_note(
    request: CreateNoteRequest,
    db=Depends(get_db)
):
    """
    Add an enhanced note to a person with type, priority, tags, and metadata
    Uses add_person_note() database function
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Use the database function to add note with all enhanced fields
        cursor.execute("""
            SELECT add_person_note(
                %s::uuid,
                %s::uuid,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s::jsonb
            ) as note_id
        """, (
            request.person_id,
            request.user_id,
            request.note_text,
            request.note_type,
            request.note_category,
            request.priority,
            request.tags or [],
            json.dumps(request.metadata or {})
        ))
        
        result = cursor.fetchone()
        note_id = str(result['note_id'])
        
        # Fetch the complete note to return
        cursor.execute("""
            SELECT * FROM person_notes WHERE note_id = %s
        """, (note_id,))
        
        note = dict(cursor.fetchone())
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'note_id': note_id,
            'note': note
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating note: {str(e)}")


@router.get("/notes/{person_id}")
async def get_notes(
    person_id: str,
    db=Depends(get_db)
):
    """
    Get all notes for a person
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM person_notes 
            WHERE person_id = %s 
            ORDER BY created_at DESC
        """, (person_id,))
        
        notes = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        return {
            'success': True,
            'person_id': person_id,
            'count': len(notes),
            'notes': notes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notes: {str(e)}")


@router.put("/notes/{note_id}")
async def update_note(
    note_id: str,
    note_text: str = Body(..., embed=True),
    db=Depends(get_db)
):
    """
    Update a note
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            UPDATE person_notes 
            SET note_text = %s, updated_at = NOW()
            WHERE note_id = %s
            RETURNING *
        """, (note_text, note_id))
        
        note = cursor.fetchone()
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        note = dict(note)
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'note': note
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating note: {str(e)}")


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    db=Depends(get_db)
):
    """
    Delete a note
    """
    
    try:
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM person_notes WHERE note_id = %s", (note_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Note not found")
        
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'message': 'Note deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting note: {str(e)}")


@router.get("/notes/search")
async def search_notes(
    q: str,
    person_id: Optional[str] = None,
    note_type: Optional[str] = None,
    note_category: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 100,
    db=Depends(get_db)
):
    """
    Search notes using full-text search
    Uses search_person_notes() database function
    
    Params:
    - q: Search query text
    - person_id: Filter by specific person (optional)
    - note_type: Filter by note type (optional)
    - note_category: Filter by category (optional)
    - priority: Filter by priority (optional)
    - tags: Comma-separated tags to filter by (optional)
    - limit: Max results (default 100)
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Convert string filters to arrays for database function
        note_types = [note_type] if note_type else None
        note_categories = [note_category] if note_category else None
        priorities = [priority] if priority else None
        search_tags = tags.split(',') if tags else None
        
        cursor.execute("""
            SELECT * FROM search_person_notes(
                %s,
                %s::uuid,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (q, person_id, note_types, note_categories, priorities, search_tags, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        return {
            'success': True,
            'query': q,
            'count': len(results),
            'results': results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching notes: {str(e)}")


# ===== TAGS =====

@router.post("/tags")
async def add_tag(
    request: AddTagRequest,
    db=Depends(get_db)
):
    """
    Add a tag to a person
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            INSERT INTO person_tags (person_id, tag, tag_type, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (person_id, tag) DO NOTHING
            RETURNING *
        """, (request.person_id, request.tag.lower(), request.tag_type))
        
        result = cursor.fetchone()
        db.commit()
        
        if result:
            tag = dict(result)
            cursor.close()
            return {
                'success': True,
                'tag': tag
            }
        else:
            cursor.close()
            return {
                'success': True,
                'message': 'Tag already exists'
            }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding tag: {str(e)}")


@router.get("/tags/{person_id}")
async def get_tags(
    person_id: str,
    db=Depends(get_db)
):
    """
    Get all tags for a person
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM person_tags 
            WHERE person_id = %s 
            ORDER BY tag_type, tag
        """, (person_id,))
        
        tags = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        return {
            'success': True,
            'person_id': person_id,
            'count': len(tags),
            'tags': tags
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tags: {str(e)}")


@router.delete("/tags/{person_id}/{tag}")
async def remove_tag(
    person_id: str,
    tag: str,
    db=Depends(get_db)
):
    """
    Remove a tag from a person
    """
    
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            DELETE FROM person_tags 
            WHERE person_id = %s AND tag = %s
        """, (person_id, tag.lower()))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'message': 'Tag removed successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing tag: {str(e)}")


# ===== SAVED SEARCHES =====

@router.post("/searches")
async def save_search(
    request: SaveSearchRequest,
    db=Depends(get_db)
):
    """
    Save a search with filters
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            INSERT INTO saved_searches (name, filters, user_id, created_at, last_used)
            VALUES (%s, %s, %s, NOW(), NOW())
            RETURNING *
        """, (request.name, json.dumps(request.filters), request.user_id))
        
        search = dict(cursor.fetchone())
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'search': search
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving search: {str(e)}")


@router.get("/searches")
async def get_saved_searches(
    user_id: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Get all saved searches for a user
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        if user_id:
            cursor.execute("""
                SELECT * FROM saved_searches 
                WHERE user_id = %s 
                ORDER BY last_used DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT * FROM saved_searches 
                ORDER BY last_used DESC
            """)
        
        searches = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        return {
            'success': True,
            'count': len(searches),
            'searches': searches
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching searches: {str(e)}")


@router.put("/searches/{search_id}/use")
async def mark_search_used(
    search_id: str,
    db=Depends(get_db)
):
    """
    Update last_used timestamp for a search
    """
    
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE saved_searches 
            SET last_used = NOW()
            WHERE search_id = %s
        """, (search_id,))
        
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'message': 'Search usage updated'
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating search: {str(e)}")


@router.delete("/searches/{search_id}")
async def delete_search(
    search_id: str,
    db=Depends(get_db)
):
    """
    Delete a saved search
    """
    
    try:
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM saved_searches WHERE search_id = %s", (search_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Search not found")
        
        db.commit()
        cursor.close()
        
        return {
            'success': True,
            'message': 'Search deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting search: {str(e)}")

