# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient

class DatabasePipeline:

    myclient = MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false") 
    db = myclient["Thesis"]
    collection = db["InstagramAccounts"]

    def process_item(self, item, spider):
        user_name = item['personal_info']['user_name']
        self.collection.replace_one(
            {'personal_info.user_name':user_name},
            item, upsert=True)   
