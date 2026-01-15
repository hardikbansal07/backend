from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.admin.blog_models import BlogSchema, UpdateBlogSchema, PaginatedResponse
from mongo import mongo_db
from models import User
from auth import get_current_active_user
from bson import ObjectId

# Admin Router (Protected)
admin_router = APIRouter(prefix="/admin/blogs", tags=["admin-blogs"])

@admin_router.post("", response_model=BlogSchema, status_code=status.HTTP_201_CREATED)
async def create_blog(
    blog: BlogSchema,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new blog post. Requires admin privileges (assumed via get_current_active_user for now, 
    add proper role check if needed).
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Optional: Verify user role is admin
    if current_user.role != "admin":
         raise HTTPException(status_code=403, detail="Not authorized")

    blog_dict = blog.model_dump(by_alias=True, exclude=["id"])
    if blog_dict.get("_id") is None:
        blog_dict.pop("_id", None) # Ensure auto-gen

    new_blog = await mongo_db.db.blogs.insert_one(blog_dict)
    created_blog = await mongo_db.db.blogs.find_one({"_id": new_blog.inserted_id})
    return created_blog

@admin_router.get("", response_model=PaginatedResponse[BlogSchema])
async def list_all_blogs_admin(
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """
    Fetch all blogs for the admin dashboard (includes content) with pagination.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    if current_user.role != "admin":
         raise HTTPException(status_code=403, detail="Not authorized")

    skip = (page - 1) * limit
    total = await mongo_db.db.blogs.count_documents({})
    
    blogs = await mongo_db.db.blogs.find()\
        .sort("created_at", -1)\
        .skip(skip)\
        .limit(limit)\
        .to_list(limit)

    import math
    return {
        "items": blogs,
        "total": total,
        "page": page,
        "size": limit,
        "pages": math.ceil(total / limit)
    }

# ... (update/delete routes remain unchanged)

# Public Router (Read Only)
public_router = APIRouter(prefix="/api/blogs", tags=["public-blogs"])

@public_router.get("", response_model=PaginatedResponse[BlogSchema])
async def list_public_blogs(
    page: int = 1,
    limit: int = 10
):
    """
    Fetch all blogs for public display with pagination. Optimized to exclude heavy content.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    skip = (page - 1) * limit
    total = await mongo_db.db.blogs.count_documents({})

    # Projection to exclude content
    blogs = await mongo_db.db.blogs.find({}, {"content": 0})\
        .sort("created_at", -1)\
        .skip(skip)\
        .limit(limit)\
        .to_list(limit)
    
    results = []
    for b in blogs:
        b["content"] = "" # Optimized
        results.append(b)
        
    import math
    return {
        "items": results,
        "total": total,
        "page": page,
        "size": limit,
        "pages": math.ceil(total / limit)
    }

@public_router.get("/{id}", response_model=BlogSchema)
async def get_blog_detail(id: str):
    """
    Fetch a single blog with full details.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    blog = await mongo_db.db.blogs.find_one({"_id": ObjectId(id)})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    return blog
