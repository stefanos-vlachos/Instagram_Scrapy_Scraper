# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UserData(scrapy.Item):
    personal_info = scrapy.Field()
    tagged_users = scrapy.Field()
    hashtags = scrapy.Field()
    user_posts = scrapy.Field()

        
class PersonalInfo(scrapy.Item):
    user_name = scrapy.Field()
    user_id = scrapy.Field()
    account_type = scrapy.Field()
    account_category = scrapy.Field()
    owned_by = scrapy.Field()
    followers = scrapy.Field()
    following = scrapy.Field()
    posts = scrapy.Field()
    videos = scrapy.Field()
    avg_erpost = scrapy.Field()
    avg_erview = scrapy.Field()
    avg_likes = scrapy.Field()
    avg_comments = scrapy.Field()
    avg_engagement = scrapy.Field()
    avg_days_between_posts = scrapy.Field()

class RegularPost(scrapy.Item):
    post_id = scrapy.Field()
    post_type = scrapy.Field()
    post_date_timestamp = scrapy.Field()
    likes = scrapy.Field()
    comments = scrapy.Field()
    views = scrapy.Field()
    post_tagged_users = scrapy.Field()
    post_hashtags = scrapy.Field()
    er_view = scrapy.Field()
    er_post = scrapy.Field()
    er_comments_post = scrapy.Field()

class SlideShow(scrapy.Item):
    post_id = scrapy.Field()
    post_type = scrapy.Field()
    post_date_timestamp = scrapy.Field()
    likes = scrapy.Field()
    comments = scrapy.Field()
    post_tagged_users = scrapy.Field()
    post_hashtags = scrapy.Field()
    er_post = scrapy.Field()
    er_comments_post = scrapy.Field()
    slidePosts = scrapy.Field()
    slideshow_erview = scrapy.Field()

class SlidePost(scrapy.Item):
    slide_id = scrapy.Field()
    slide_type = scrapy.Field()
    slide_views = scrapy.Field()
    er_view = scrapy.Field()
