from app.db.mongodb import MongoDB

# Initialize MongoDB and MySQL instances
mongo = MongoDB()


async def connect_all():
    # Establish both MongoDB and MySQL connections
    await mongo.connect()
   

async def close_all():
    # Close both MongoDB and MySQL connections
    mongo.close()
   
