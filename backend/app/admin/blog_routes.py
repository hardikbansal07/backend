from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.admin.blog_models import BlogSchema, UpdateBlogSchema
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

@admin_router.get("", response_model=List[BlogSchema])
async def list_all_blogs_admin(
    current_user: User = Depends(get_current_active_user)
):
    """
    Fetch all blogs for the admin dashboard (includes content).
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    if current_user.role != "admin":
         raise HTTPException(status_code=403, detail="Not authorized")

    blogs = await mongo_db.db.blogs.find().sort("created_at", -1).to_list(1000)
    return blogs

@admin_router.put("/{id}", response_model=BlogSchema)
async def update_blog(
    id: str,
    blog_update: UpdateBlogSchema,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing blog.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    if current_user.role != "admin":
         raise HTTPException(status_code=403, detail="Not authorized")

    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Filter out None values
    update_data = {k: v for k, v in blog_update.model_dump(exclude_unset=True).items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided to update")

    update_data["updated_at"] = datetime.utcnow()

    result = await mongo_db.db.blogs.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Blog not found")

    updated_blog = await mongo_db.db.blogs.find_one({"_id": ObjectId(id)})
    return updated_blog

@admin_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a blog permanently.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    if current_user.role != "admin":
         raise HTTPException(status_code=403, detail="Not authorized")
         
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    result = await mongo_db.db.blogs.delete_one({"_id": ObjectId(id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    return None


# Public Router (Read Only)
public_router = APIRouter(prefix="/api/blogs", tags=["public-blogs"])

@public_router.get("", response_model=List[BlogSchema])
async def list_public_blogs():
    """
    Fetch all blogs for public display. Optimized to exclude heavy content.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Projection to exclude content
    blogs = await mongo_db.db.blogs.find({}, {"content": 0}).sort("created_at", -1).to_list(100)
    
    # We need to manually add dummy content or handle the schema validation if content is required in BlogSchema
    # Since BlogSchema marks content as required, we might need a separate schema or just populate it with empty string
    # for the purpose of validation, OR change BlogSchema. But user requirement mentioned avoiding heavy loading.
    # Let's populate with empty string for response validation if needed, or better, use a PublicBlogSchema.
    # For simplicity, we'll iterate and patch, or just trust Pydantic ignores missing required if not strictly validated on output?
    # Pydantic will error if required field is missing.
    # Better approach: Adjust the return list to inject empty content or use response_model_exclude.
    
    # Re-fetching for now to ensure list is valid Pydantic objects, but mongo projection excluded it.
    # Let's modify the query to include content for now to be safe with schema, 
    # OR better: creating a specific PublicBlogSchema is cleaner but I'll stick to 
    # injecting a dummy string to save bandwidth if I can modify the dicts.
    
    results = []
    for b in blogs:
        b["content"] = "" # Optimized
        results.append(b)
        
    return results

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
