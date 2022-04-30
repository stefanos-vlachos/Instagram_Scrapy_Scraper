from pymongo import MongoClient

class DocumentsFinder:

    myclient = MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
    db = myclient["greek-socialmedia-businesses"]
    collection = db["instagram-businesses-toscrape"]

    def exportDocuments(self,startIndex,limit):
        return self.collection.find({'tagged_users': { '$exists' : False }},{'_id':0,'personal_info.user_name':1}).sort("_id",-1).skip(startIndex).limit(limit)

    #Finds documents using filter, project, skip and limit
    def findDocumentsWithProjSkipLim(self, filter, project, skip_num, limit_num):
        return self.collection.find(filter, project).skip(skip_num).limit(limit_num)


    #Finds documents using filter, skip and limit
    def findDocumentsWithSkipLim(self, filter, skip_num, limit_num):
        return self.collection.find(filter).skip(skip_num).limit(limit_num)


    #Finds documents using filter, project and skip
    def findDocumentsWithProjSkip(self, filter, project, skip_num):
        return self.collection.find(filter, project).skip(skip_num)


    #Finds documents using filter and skip
    def findDocumentsWithSkip(self, filter, skip_num):
        return self.collection.find(filter).skip(skip_num)


    #Finds documents using filter, project and limit
    def findDocumentsWithProjLim(self, filter, project, limit_num):
        return self.collection.find(filter, project).limit(limit_num)


    #Finds documents using filter and limit
    def findDocumentsWithLim(self, filter, limit_num):
        return self.collection.find(filter).limit(limit_num)


    #Finds documents using filter
    def findDocuments(self, filter):
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