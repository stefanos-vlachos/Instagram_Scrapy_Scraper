import scrapy
import json
import re
from urllib.parse import urlencode
from ..tools.resources_importer import ResourcesImporter
from ..items import PersonalInfo
from ..items import SlideShow
from ..items import SlidePost
from ..items import UserData
from ..items import RegularPost


class InstagramSpider(scrapy.Spider):

    name = 'InstagramSpider'
    allowed_domains = ['instagram.com']
    users_to_scrape = []
    scraped_users = []
    followers_limit = 0
    request_header = {
        "Host": "www.instagram.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
        "Accept": "*/*",
        "Accept-Language": "el-GR,el;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "X-IG-App-ID": "936619743392459",
        "X-ASBD-ID": "198387",
        "X-IG-WWW-Claim": "hmac.AR2-lW03gv1H6igo5IypPWLMYh1xVy2QBggkVd3xQlSHKxU6",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
        "Referer": "https://www.instagram.com/",
        "Cookie": "mid=YlrWKQALAAF0cS9nU2Bz1ppeAAig; ig_did=C56C0448-6E9A-4A91-83BA-CB69F1AD1FAA; sessionid=46324385601%3AMiFZhiRCmHwbxE%3A15; ds_user_id=46324385601; csrftoken=KN05ho23O3yTx5EoABXA78M5fTh0YmSg; shbid=\"10587\\05446324385601\\0541682858390:01f79460fd4fea8cd66935f32578d4b596bb56293a2e1071411b12d6747b9e5c5cdd502f\"; shbts=\"1651322390\\05446324385601\\0541682858390:01f737ee1f7d5c16c2553259ec34381ec9dff4eb1e32bce8dd650cb36b039dcfddb87344\"; rur=\"ODN\\05446324385601\\0541682858401:01f7245d913a18d7b5be0e52fba64e55e306b3e19e923b3d7b4b9312c9234cbe33c2015a\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "ec-Fetch-Site": "same-origin",
        "TE": "trailers"
    }
    scrape_from_date = 1577836800
    scrape_until_date = 1609459199

    #Populate users_to_scrape from file
    #users_to_scrape = ResourcesImporter.importProfilesFromJSON(ResourcesImporter)
    #Populate users_to_scrape from database
    users_to_scrape = ResourcesImporter.importProfilesFromDatabase(ResourcesImporter)


    #Sends request for each profile
    def start_requests(self):

        for user in self.users_to_scrape:
            requested_url = "https://www.instagram.com/"+user["id"]+"/?hl=el"
            yield scrapy.Request(requested_url, callback=self.parse, headers=self.request_header)


    #Receives response for each profile
    #Handles the first 12 posts of each profile
    def parse(self, response):

        response_script = response.xpath("//script[starts-with(.,'window._sharedData')]/text()").extract_first()
        if response_script and response_script.__contains__("ProfilePage") :

            #Extracts the profile data from the html page
            embedded_json = response_script.strip().split('sharedData = ')[1][:-1]
            profile_data = json.loads(embedded_json)['entry_data']['ProfilePage'][0]['graphql']['user']

            is_private = profile_data['is_private']
            if not is_private:
                if profile_data['edge_followed_by']['count'] > self.followers_limit:

                    #Instantiates user's data structures
                    user_data = UserData(tagged_users=[], user_posts=[], hashtags=[])
                    personal_info = PersonalInfo(followers=0, following=0, posts=0, videos=0, avg_erpost=0, avg_erview=0,
                                                    avg_likes=0, avg_comments=0, avg_engagement=0, avg_days_between_posts=0)

                    personal_info['user_name'] = profile_data['username']
                    personal_info['user_id'] = profile_data['id']
                    personal_info['followers'] = profile_data['edge_followed_by']['count']
                    personal_info['following'] = profile_data['edge_follow']['count']

                    biography = profile_data['biography']
                    biography_tags = re.findall('@(.+?)[^0-9a-zA-Z._]', biography)
                    if biography_tags:
                        self.extract_tags_from_list(biography_tags,user_data['tagged_users'], "tags")

                    account_type = profile_data['business_category_name']
                    if  account_type and account_type is not None:
                        personal_info['account_type'] = profile_data['business_category_name']    
                    else:
                        personal_info['account_type'] = "General Purpose"

                    account_category = profile_data['category_enum']
                    if account_category and account_category is not None:     
                        personal_info['account_category'] = profile_data['category_enum']
                    else:
                        personal_info['account_category'] = "General Purpose"

                    #Turns True when posts exceed the threshold date
                    found_older_posts = False
                    #Holds the date of the last scraped post
                    last_post_date = 0

                    profile_posts = profile_data['edge_owner_to_timeline_media']['edges']
                    for edge in profile_posts:

                        post_date = int(edge['node']['taken_at_timestamp'])
                        if(post_date < self.scrape_until_date):
                            if(post_date > self.scrape_from_date) :

                                personal_info['posts'] += 1

                                #Checks if post is Slideshow or Regular post
                                post_type = edge['node']['__typename']
                                if post_type == "GraphSidecar":

                                    #Instantiates SlideShow
                                    post = SlideShow(likes=0, comments=0, er_post=0, er_comments_post=0, slidePosts=[], post_tagged_users=[], post_hashtags=[])
                                    post['post_type'] = "slideshow"

                                    slideshow_erview = 0
                                    slideshow_videos = 0

                                    #Accesses slides of the SlideShow
                                    slides = edge['node']['edge_sidecar_to_children']['edges']
                                    for slide in slides:
                                        #Instantiates Slide
                                        slidepost = SlidePost()
                                        slidepost['slide_id'] = slide['node']['id'] 

                                        #Handles tagged users in the Slide
                                        if slide['node']['edge_media_to_tagged_user']:
                                            self.extract_tags_from_edges(slide['node']['edge_media_to_tagged_user']['edges'], user_data['tagged_users'])
                                            self.extract_tags_from_edges(slide['node']['edge_media_to_tagged_user']['edges'], post['post_tagged_users'])

                                        if slide['node']['is_video']:
                                            slidepost['slide_type'] = "video"
                                            slidepost['slide_views'] = float(slide['node']['video_view_count'])

                                            slideshow_videos += 1
                                            personal_info['videos'] += 1

                                            #slidepost_erview = slideshow_likes / slide_views
                                            slidepost['er_view'] = 0
                                            if slidepost['slide_views'] != 0:
                                                slidepost['er_view'] = post['likes'] / slidepost['slide_views'] * 100
                                                slideshow_erview += slidepost['er_view']

                                            #avg_erview = total_erview / number_of_videos
                                            personal_info['avg_erview'] += slidepost['er_view']
                                        else:
                                            slidepost['slide_type'] = "Photo"

                                        post['slidePosts'].append(dict(slidepost))

                                    #slideshow_erview = total_slidshow_erview / number_of_slideshow_videos
                                    if slideshow_videos != 0:
                                        post['slideshow_erview'] = round(float(slideshow_erview / slideshow_videos), 2)
                                else:

                                    #Instantiates Regular Post
                                    post = RegularPost(likes=0, comments=0, er_post=0, er_comments_post=0, post_tagged_users=[], post_hashtags=[])

                                    if edge['node']['is_video']:
                                        post['post_type'] = "video"
                                        post['views'] = float(edge['node']['video_view_count'])

                                        personal_info['videos'] += 1
                                        
                                        #post_erview = post_likes / post_views
                                        post['er_view'] = 0
                                        if post['views'] != 0:
                                            post['er_view'] = post['likes'] / post['views'] * 100

                                        personal_info['avg_erview'] += post['er_view']
                                    else:
                                        post['post_type'] = "photo"

                                post['post_id'] = edge['node']['id']
                                post['post_date_timestamp'] = post_date
                                post['likes'] = float(edge['node']['edge_liked_by']['count'])
                                post['comments'] = edge['node']['edge_media_to_comment']['count']

                                #er_comments_post = (post_likes + post_comments) / profile_followers
                                post['er_comments_post'] = float((post['likes'] + post['comments'])/personal_info['followers']) * 100
                                #er_post = post_likes / profile_followrers
                                post['er_post'] = post['likes'] / personal_info['followers'] * 100
                                #avg_likes = total_likes / number_of_posts
                                personal_info['avg_likes'] += post['likes']
                                #avg_comments = total_comments / number_of_posts
                                personal_info['avg_comments'] += post['comments']
                                #avg_engagement = total_er_comments_post / number_of_posts
                                personal_info['avg_engagement'] += post['er_comments_post']
                                #avg_erpost = total_er_post / number_of_posts
                                personal_info['avg_erpost'] += post['er_post']

                                #avg_days_between_posts=the average number of days between the user's sequential uploads
                                if personal_info['posts'] > 1:
                                    personal_info['avg_days_between_posts'] += ((last_post_date - edge['node']['taken_at_timestamp']) / (60*60*24))
                                last_post_date = edge['node']['taken_at_timestamp']

                                #Handles the post caption
                                if edge['node']['edge_media_to_caption']:
                                    post_captions = edge['node']['edge_media_to_caption']
                                    captions = ""
                                    for i in post_captions['edges']:
                                        captions += i['node']['text'] + "\n"
                                    captions_tags = re.findall('@(.+?)[^0-9a-zA-Z._]', captions)
                                    #Exctracts mentioned users from caption
                                    self.extract_tags_from_list(captions_tags, user_data['tagged_users'], "tags")
                                    self.extract_tags_from_list(captions_tags, post['post_tagged_users'], "tags")
                                    #Exctracts hashtags from caption
                                    captions_hashtags = re.findall(r"#(\w+)", captions)
                                    self.extract_tags_from_list(captions_hashtags, user_data['hashtags'], "hashtags")
                                    self.extract_tags_from_list(captions_hashtags, post['post_hashtags'], "hashtags")

                                #Handles the tagged users in the post
                                if edge['node']['edge_media_to_tagged_user']:
                                    inpost_tagged_users = edge['node']['edge_media_to_tagged_user']
                                    if inpost_tagged_users:
                                        self.extract_tags_from_edges(inpost_tagged_users['edges'], user_data['tagged_users'])
                                        self.extract_tags_from_edges(inpost_tagged_users['edges'], post['post_tagged_users'])
        
                                user_data['user_posts'].append(dict(post))
                            else:
                                found_older_posts = True
                                break

                    #Checks if profile has more posts in the acceptable time period
                    has_next_page = profile_data['edge_owner_to_timeline_media']['page_info']['has_next_page']
                    if has_next_page and not found_older_posts:

                        user_data['personal_info'] = personal_info

                        #Pointer to next dozen of posts  
                        cursor = profile_data['edge_owner_to_timeline_media']['page_info']['end_cursor']

                        #Construction of request
                        request_di={'id': personal_info['user_id'], 'first': 12, 'after': cursor, 'username': personal_info['user_name']}
                        params = {'query_hash': 'e769aa130647d2354c40ea6a439bfc08', 'variables': json.dumps(request_di)}
                        url = 'https://www.instagram.com/graphql/query/?' + urlencode(params)
                        metadata = {'user_data': dict(user_data)}

                        yield scrapy.Request(url, callback=self.parse_pages, headers=self.request_header, meta={'metadata': metadata})

                    else:
                        #Final calculation of the average post metrics
                        if personal_info['posts'] != 0:
                            personal_info['avg_erpost'] = round(float(personal_info['avg_erpost'] / personal_info['posts']), 2)
                            personal_info['avg_likes'] = int(personal_info['avg_likes'] / personal_info['posts'])
                            personal_info['avg_comments'] = int(personal_info['avg_comments'] / personal_info['posts'])
                            personal_info['avg_engagement'] = round(float(personal_info['avg_engagement'] / personal_info['posts']), 2)
                        if personal_info['posts'] > 1:
                            personal_info['avg_days_between_posts'] = int(personal_info['avg_days_between_posts'] / (personal_info['posts'] - 1))
                        if personal_info['videos'] > 0:
                            personal_info['avg_erview'] = round(float(personal_info['avg_erview'] / personal_info['videos']), 2)
                        else:
                            personal_info['avg_erview'] = 0

                        user_data['personal_info'] = personal_info

                        print("Scraped:" + personal_info['user_name'])
                        yield dict(user_data)

            else:
                print("Private profile.")
        else:
            print("Error Response.")


    #Handles the following dozens of posts of each profile
    def parse_pages(self, response):

        data = json.loads(response.text)
        metadata = response.meta['metadata']
        user_data = metadata['user_data']

        found_older_posts = False 
        if(user_data['user_posts']):
            last_post_date = int(user_data['user_posts'][-1]['post_date_timestamp'])
        else:
            last_post_date=0

        profile_posts = data['data']['user']['edge_owner_to_timeline_media']['edges']
        
        for edge in profile_posts:
            post_date = int(edge['node']['taken_at_timestamp'])

            if(post_date < 1609459199):
                if(post_date > 1577836800) :

                    user_data['personal_info']['posts'] += 1

                    if edge['node']['__typename']=="GraphSidecar":
                        post = SlideShow(likes=0, comments=0, er_post=0, er_comments_post=0, slidePosts=[], post_tagged_users=[], post_hashtags=[])
                    else:
                        post = RegularPost(likes=0, comments=0, er_post=0, er_comments_post=0, post_tagged_users=[], post_hashtags=[])

                    post['post_id'] = edge['node']['id']
                    post['post_date_timestamp'] = post_date
                    post['likes'] = float(edge['node']['edge_media_preview_like']['count']) 
                    post['comments'] = float(edge['node']['edge_media_to_comment']['count'])
                    post['er_post'] = post['likes'] / float(user_data['personal_info']['followers']) * 100
                    post['er_comments_post'] = float((post['likes']+post['comments']) / user_data['personal_info']['followers']) * 100 

                    user_data['personal_info']['avg_likes'] += post['likes']
                    user_data['personal_info']['avg_comments'] += post['comments']
                    user_data['personal_info']['avg_engagement'] += post['er_comments_post']
                    user_data['personal_info']['avg_erpost'] += post['er_post']

                    if user_data['personal_info']['posts'] > 1:
                        user_data['personal_info']['avg_days_between_posts'] += ((last_post_date - edge['node']['taken_at_timestamp']) / (60*60*24))
                    last_post_date = edge['node']['taken_at_timestamp']
                    
                    if edge['node']['edge_media_to_caption']:
                        post_captions = edge['node']['edge_media_to_caption']
                        captions = ""
                        for i in post_captions['edges']:
                            captions += i['node']['text'] + "\n"
                        captions_tags = re.findall('@(.+?)[^0-9a-zA-Z._]', captions)  
                        self.extract_tags_from_list(captions_tags,user_data['tagged_users'], "tags")
                        self.extract_tags_from_list(captions_tags, post['post_tagged_users'], "tags")

                        captions_hashtags = re.findall(r"#(\w+)", captions) 
                        self.extract_tags_from_list(captions_hashtags, user_data['hashtags'], "hashtags")
                        self.extract_tags_from_list(captions_hashtags, post['post_hashtags'], "hashtags")     

                    if edge['node']['edge_media_to_tagged_user']:
                        self.extract_tags_from_edges(edge['node']['edge_media_to_tagged_user']['edges'], user_data['tagged_users'])
                        self.extract_tags_from_edges(edge['node']['edge_media_to_tagged_user']['edges'], post['post_tagged_users'])

                    post_type = edge['node']['__typename']

                    if post_type == "GraphSidecar":
                        post['post_type'] = "slideshow"
                        slides = edge['node']['edge_sidecar_to_children']['edges']

                        slideshow_erview = 0
                        slideshow_videos = 0

                        for slide in slides:
                            slidepost = SlidePost()
                            slidepost['slide_id'] = slide['node']['id']

                            if slide['node']['edge_media_to_tagged_user']:
                                self.extract_tags_from_edges(slide['node']['edge_media_to_tagged_user']['edges'], user_data['tagged_users'])
                                self.extract_tags_from_edges(slide['node']['edge_media_to_tagged_user']['edges'], post['post_tagged_users'])

                            if slide['node']['is_video']:
                                slideshow_videos += 1
                                user_data['personal_info']['videos'] += 1
                                slidepost['slide_type'] = "video"
                                slidepost['slide_views'] = float(slide['node']['video_view_count'])
                                slidepost['er_view'] = 0
                                if slidepost['slide_views'] != 0:
                                    slidepost['er_view'] = post['likes'] / slidepost['slide_views'] * 100
                                    slideshow_erview += slidepost['er_view']
                                user_data['personal_info']['avg_erview'] += slidepost['er_view']
                            else:
                                slidepost['slide_type'] = "Photo"

                            post['slidePosts'].append(dict(slidepost))

                        if slideshow_videos != 0:
                            post['slideshow_erview'] = round(float(slideshow_erview / slideshow_videos),2)

                        user_data['user_posts'].append(dict(post))
                    else:
                        if edge['node']['is_video']:
                            user_data['personal_info']['videos'] += 1
                            post['post_type'] = "video"
                            post['views'] = float(edge['node']['video_view_count'])
                            post['er_view'] = 0
                            if post['views'] != 0:
                                post['er_view'] = post['likes'] / post['views'] * 100
                            user_data['personal_info']['avg_erview'] += post['er_view']
                        else:
                            post['post_type'] = "photo"

                        user_data['user_posts'].append(dict(post))      
                else:
                    found_older_posts = True
                    break

        has_next_page = data['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
        if has_next_page and not found_older_posts:
            cursor = data['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
            request_di={'id': user_data['personal_info']['user_id'], 'first': 12, 'after': cursor, 'username': user_data['personal_info']['user_name']}
            params = {'query_hash': 'e769aa130647d2354c40ea6a439bfc08', 'variables': json.dumps(request_di)}
            url = 'https://www.instagram.com/graphql/query/?' + urlencode(params)
            metadata = {'user_data': dict(user_data)}
            yield scrapy.Request(url, callback=self.parse_pages, headers=self.request_header, meta={'metadata': metadata})
        else :

            if user_data['personal_info']['avg_erpost'] != 0:
                user_data['personal_info']['avg_erpost'] = round(float(user_data['personal_info']['avg_erpost']/user_data['personal_info']['posts']),2)
                user_data['personal_info']['avg_likes'] = int(user_data['personal_info']['avg_likes']/user_data['personal_info']['posts'])
                user_data['personal_info']['avg_comments'] = int(user_data['personal_info']['avg_comments']/user_data['personal_info']['posts'])
                user_data['personal_info']['avg_engagement'] = round(float(user_data['personal_info']['avg_engagement']/user_data['personal_info']['posts']),2)
                user_data['personal_info']['avg_days_between_posts'] = int(user_data['personal_info']['avg_days_between_posts']/(user_data['personal_info']['posts']-1))
            if not user_data['personal_info']['videos'] == 0:
                user_data['personal_info']['avg_erview'] = round(float(user_data['personal_info']['avg_erview']/user_data['personal_info']['videos']),2)
            else:
                user_data['personal_info']['avg_erview'] = 0

            print("Scraped:" + user_data['personal_info']['user_name'])
            yield dict(user_data)


    def extract_tags_from_list(self, extraction_list, insertion_list, type):

        for tag in extraction_list:
            if tag.endswith('.'):
                tag = tag[:-1]
                
            if not tag in insertion_list: 
                insertion_list.append(tag)


    def extract_tags_from_edges(self, extraction_list, insertion_list):

        for edge in extraction_list:
            tag=edge['node']['user']['username']

            if tag.endswith('.'):
                tag = tag[:-1]
                
            if not tag in insertion_list:
                insertion_list.append(tag)
