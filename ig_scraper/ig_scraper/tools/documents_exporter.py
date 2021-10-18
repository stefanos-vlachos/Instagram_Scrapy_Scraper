from pymongo import MongoClient

class DocumentsExporter:

    myclient = MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
    db = myclient["Thesis"]
    collection = db["InstagramAccounts"]

    def exportDocuments(self,startIndex,limit):
        return self.collection.find({'tagged_users': { '$exists' : False }},{'_id':0,'personal_info.user_name':1}).sort("_id",-1).skip(startIndex).limit(limit)

    def findDocuments(self, filter, project, skip_num, limit_num):
        if skip_num != None:
            if limit_num != None:
                if project != None:
                    return self.collection.find(filter, project).skip(skip_num).limit(limit_num)
                return self.collection.find(filter).skip(skip_num).limit(limit_num)
            else:
                if project != None:
                    return self.collection.find(filter, project).skip(skip_num)
                return self.collection.find(filter).skip(skip_num)
        else:
            if limit_num != None:
                if project != None:
                    return self.collection.find(filter, project).limit(limit_num)
                return self.collection.find(filter).limit(limit_num)
            return self.collection.find(filter)

    def findNoTagsPosts(self,skipnum,limitnum):
        aggregation=[
            {
                '$match': {
                    "user_posts":{"$elemMatch":{"post_hashtags":{"$exists":False}}},
                    "scraped":{"$exists":False}
                }
            }, {
                '$skip': skipnum
            }, {
                '$limit': limitnum
            }, {
                '$unwind': {
                    'path': '$user_posts'
                }
            }, {
                '$project': {
                    'personal_info.user_name': 1, 
                    'personal_info.user_id': 1, 
                    'user_posts.post_date_timestamp': 1
                }
            }, {
                '$sort': {
                    'user_posts.post_date_timestamp': 1
                }
            }, {
                '$group': {
                    '_id': {
                        'user_name': '$personal_info.user_name', 
                        'user_id': '$personal_info.user_id'
                    }, 
                    'last_post_date': {
                        '$max': '$user_posts.post_date_timestamp'
                    }
                }
            }
        ]
        return self.collection.aggregate(aggregation)