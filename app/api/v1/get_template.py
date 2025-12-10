from fastapi import APIRouter, HTTPException
from app.db.database import mongo

router = APIRouter()

@router.get("/get/template/{page_count}/{page_no}")
async def get_templates(page_count: int, page_no: int):
    """
    Retrieve templates with pagination.
    - page_count: number of items per page
    - page_no: page number (starting from 1)
    """
    try:
        template_collection = await mongo.get_collection("templates")

        # Ensure valid page numbers
        if page_no < 1 or page_count < 1:
            raise HTTPException(status_code=400, detail="Invalid pagination parameters")

        pipeline = [
             {
                "$lookup": {
                    "from": "categories",
                    "let": {"category_id": "$category_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$category_id", "$$category_id"]}
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "category_id": 1,
                                "category_name": 1,
                                "icon_name": 1
                            }
                        },
                    ],
                    "as": "category_info"
                }
            },
            {
                "$lookup": {
                    "from": "sub_categories",
                    "let": {"sub_category_id": "$sub_category_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$sub_category_id", "$$sub_category_id"]}
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "sub_category_id": 1,
                                "sub_category_name": 1
                            }
                        },
                    ],
                    "as": "sub_category_info"
                }
                
            },
             {
                "$addFields": {
                    "category_name": {
                        "$arrayElemAt": ["$category_info.category_name", 0]
                    },
                    "sub_category_name": {
                        "$arrayElemAt": ["$sub_category_info.sub_category_name", 0]
                    }
                }
            },
            {"$sort": {"created_at": -1}},
            {"$skip": page_count * (page_no - 1)},
            {"$limit": page_count}
        ]

        # Execute aggregation
        templates_cursor = template_collection.aggregate(pipeline)

        templates_list = []
        async for template in templates_cursor:
            template["_id"] = str(template["_id"])
            templates_list.append(template)

        total_count = await template_collection.count_documents({})

        return {
            "templates": templates_list,
            "total_count": total_count,
            "page_no": page_no,
            "page_count": page_count,
            "total_pages": (total_count + page_count - 1) // page_count  
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get/all/template/status")
async def get_templates_status():
    try:
        template_collection = await mongo.get_collection("templates")

        # Correct use of projection
        status_cursor = template_collection.find(
            {},  # filter (empty for all documents)
            {
                "_id": 0,
                "template_id": 0,
                "template_name": 0,
                "category_id": 0,
                "sub_category_id": 0,
                "cover_image": 0,
                "type": 0,
                "latest_version": 0,
                "created_at": 0,
               
            }
        )

        status = []
        async for template in status_cursor:
            template["status"] = str(template["status"])
            status.append(template)

        return {
            "status": True,
            "message": "Success",
            "data": status,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
