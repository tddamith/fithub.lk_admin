from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from bson import ObjectId
from app.db.database import mongo
from app.api.v1.schemas.sub_category_schema import SubCategoryBase,UpdateSubCategoryItem,UpdateSubcategory

router = APIRouter()

#create sub-category
@router.post("/create/new/sub-category")
async def create_sub_category(sub_category: SubCategoryBase):
    """Create a new sub-category."""
    try:
        sub_category_collection = await mongo.get_collection("sub_categories")
        category_collection = await mongo.get_collection("categories")
        

        existing_category = await category_collection.find_one({"category_id": sub_category.category_id})
        if not existing_category:
            raise HTTPException(status_code=400, detail="category does not exist.")

        # Check if sub-category with the same name already exists
        existing_sub_category = await sub_category_collection.find_one({"sub_category_name": sub_category.sub_category_name})
        if existing_sub_category:
            raise HTTPException(status_code=400, detail="Sub-category with this name already exists.")
        
        sub_category_data = {
            "sub_category_id": str(ObjectId()),
            "category_id": sub_category.category_id,
            "sub_category_name": sub_category.sub_category_name,
            "sub_category_items": [item.dict() for item in sub_category.sub_category_items] if sub_category.sub_category_items else [],
            "status": "new",
            "created_at": datetime.utcnow()
        }
        
        result = await sub_category_collection.insert_one(sub_category_data)
        
        return {"message": "Sub-category created successfully", "sub_category_id": str(result.inserted_id)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    
#get sub categories by category_id
@router.get("/get/sub-categories/by/{category_id}")
async def get_sub_categories(category_id: str):
    """Retrieve sub-categories by category ID."""
    try:
        sub_category_collection = await mongo.get_collection("sub_categories")
        
        sub_categories_cursor = sub_category_collection.find({"category_id": category_id})
        sub_categories = []
        async for sub_category in sub_categories_cursor:
            sub_category["_id"] = str(sub_category["_id"])  
            sub_categories.append(sub_category)
        
        return {"sub_categories": sub_categories}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    
#update sub-category
@router.put("/update/sub-category/by/{sub_category_id}")
async def update_sub_category(sub_category_id: str, sub_category: UpdateSubcategory):
    """Update a sub-category by its ID."""
    try:
        sub_category_collection = await mongo.get_collection("sub_categories")
        
        update_data = {
            "sub_category_name": sub_category.sub_category_name,
            "sub_category_items": [item.dict() for item in sub_category.sub_category_items] if sub_category.sub_category_items else [],
            "updated_at": datetime.utcnow()
        }
        
        result = await sub_category_collection.update_one(
            {"sub_category_id": sub_category_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Sub-category not found.")
        
        return {"message": "Sub-category updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

#delete sub-category
@router.delete("/delete/sub-category/by/{sub_category_id}")
async def delete_sub_category(sub_category_id: str):
    """Delete a sub-category by its ID."""
    try:
        sub_category_collection = await mongo.get_collection("sub_categories")
        
        result = await sub_category_collection.delete_one({"sub_category_id": sub_category_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Sub-category not found.")
        
        return {"message": "Sub-category deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    

#update sub-category items
@router.put("/update/sub-category/items/by/{sub_category_id}")  
async def update_sub_category_items(sub_category_id: str, sub_category: UpdateSubCategoryItem):
    """Update sub-category items by sub-category ID."""
    try:
        sub_category_collection = await mongo.get_collection("sub_categories")
        
        update_data = {
            "sub_category_items": [item.dict() for item in sub_category.sub_category_items] if sub_category.sub_category_items else [],
            "updated_at": datetime.utcnow()
        }
        
        result = await sub_category_collection.update_one(
            {"sub_category_id": sub_category_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Sub-category not found.")
        
        return {"message": "Sub-category items updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    
#delete sub-category item
@router.delete("/delete/sub-category/item/by/{sub_category_id}/{item_id}")
async def delete_sub_category_item(sub_category_id: str, item_id: str):
    """Delete a sub-category item by its ID."""
    try:
        sub_category_collection = await mongo.get_collection("sub_categories")

        result = await sub_category_collection.update_one(
            {"sub_category_id": sub_category_id},
            {"$pull": {"sub_category_items": {"id": item_id}}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Sub-category not found.")
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Item not found in sub-category.")

        return {"message": "Sub-category item deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

#Get Sub_category by SubCategory Id
@router.get("/get/sub-categories/{sub_category_id}")
async def get_sub_category_by_id(sub_category_id: str):
    """Retrieve a sub-category (or list) by its sub_category_id."""
    try:
        sub_category_collection = await mongo.get_collection("sub_categories")

        # Query by sub_category_id
        cursor = sub_category_collection.find({"sub_category_id": sub_category_id})
        results = []
        async for sub_category in cursor:
            sub_category["_id"] = str(sub_category["_id"])
            results.append(sub_category)

        # Handle empty results gracefully
        if not results:
            raise HTTPException(status_code=404, detail="Sub-category not found")

        return {"sub_categories": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
