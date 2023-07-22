import motor.motor_asyncio
from config import Config
from datetime import datetime
import certifi

ca = certifi.where()

class manage_db():
    def __init__(self):
        try:
            self.db = motor.motor_asyncio.AsyncIOMotorClient(Config.DB_URL, tlsCAFile=ca)["JVAmazonDl"]
            self.user = self.db.users
            self.col = self.db.members
        except Exception as e:
            self.user = None
            
    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users
  
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count
        
    async def set_user(self, user_id, expiry=0, balance=0):
        start_date = datetime.now()
        try:
            await self.user.insert_one({"_id": user_id, "expiry": expiry, "balance": balance, "start": start_date})
        except:
            userkey = await self.user.find_one({'_id': user_id})
            await self.user.update_one({"_id": user_id},
                                      {'$set':
                                             {'expiry': userkey["expiry"] + expiry,
                                              'balance': userkey["balance"] + balance}})
    
    async def get_user(self, user_id):
        userkey = await self.user.find_one({'_id': user_id})
        if userkey:
            return userkey
        else:
            return False
    
    async def delete_user(self, user_id):
        await self.user.delete_one({"_id": user_id})
