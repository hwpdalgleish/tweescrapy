# Henry Dalgleish (2022)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import numpy as np
import pandas as pd
import re
import time

def get_driver_options():
    options = Options()
    options.add_argument("--window-size=900,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument('--no-sandbox')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    return options

def init_driver(url,options,driver_path=[]):
    if isinstance(driver_path,str) & (len(driver_path)>0):
        print(driver_path)
        driver = webdriver.Chrome(driver_path,options=options)
    else:
        driver = webdriver.Chrome(options=options)
    driver.get(url)
    return driver

def make_js_scripts(elements,fcns=[]):
    if len(fcns)==0:
        fcns = ['textContent']*len(elements)
    scripts = [make_js_script(x,y) for x,y in zip(elements,fcns)]
    return scripts

def make_js_script(element,fcn='textContent'):
    # element = for classes, must have .CLASS
    # fcn = can have element.FUNCTION, return FCN, or simply FUNCTION
    beg = "return Array.from(document.querySelectorAll('"
    mid = "')).map(function(element) {"
    fcn_ret = "return "
    end = ";})"
    if 'return ' in fcn:
        script = beg + element + mid + fcn + "})"
    elif 'element.' in fcn:
        script = beg + element + mid + fcn_ret + fcn + end
    else:
        script = beg + element + mid + fcn_ret + "element." + fcn + end
    return script

def cat_js_scripts(scripts):
    beg = "return ["
    end = "];"
    scripts = [re.sub('\Areturn ','',x) for x in scripts]
    script = beg + (', '.join(scripts)) + end
    script.replace('return Array.from(document)','Array.from(document)')
    return script

def flatten_list(list_of_lists):
    # converts a list of lists to a single list
    ls = [item for sublist in list_of_lists for item in sublist]
    return ls

def format_classname(classname):
    formatted_classname = '.' + '.'.join(classname.split(' '))
    return formatted_classname

def parse_user_info(s):
    s = s.split('@')
    user = '@'.join(s[:-1])
    handle = '@'+s[-1].split('·')[0]
    return user, handle

def xpath_multiclass(string):
    string = string.split(' ')
    string = ' and '.join(['contains(@class,"' + x + '")' for x in string])
    return string

def scrape_visible_tweets(driver,**kwargs):
    tags = kwargs.get('tags',[])
    name = kwargs.get('name',[])
    embed_handle = kwargs.get('embed_handle',True)

    # HTML elements associated with bookmarked tweet user info, timestamp and content
    elements = ['css-1dbjc4n r-1awozwy r-18u37iz r-1wbh5a2 r-dnmrzs r-1ny4l3l',
               'css-4rbku5 css-18t94o4 css-901oao r-1bwzh9t r-1loqt21 r-xoduu5 r-1q142lx r-1w6e6rj r-37j5jr r-a023e6 r-16dba41 r-9aw3ui r-rjixqe r-bcqeeo r-3s2u2q r-qvutc0',
               'css-901oao r-1nao33i r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-bnwqim r-qvutc0']
    fcns = ['textContent',
            'element.children[0].getAttribute("datetime")',
            'textContent']

    # format user-inputted tags
    tags_str = '|'.join(tags)

    # make all JavaScript commands
    elements = [format_classname(x) for x in elements]
    info_script = make_js_scripts(elements,fcns)
    info_script = cat_js_scripts(info_script)
    user_script = make_js_script(format_classname('css-901oao css-16my406 css-1hf3ou5 r-1bwzh9t r-18u37iz r-poiln3 r-bcqeeo r-qvutc0'))

    # execute all JavaScript commands
    out = driver.execute_script(info_script)
    this_user = driver.execute_script(user_script)[0]

    # format raw output into dataframe
    user_info = flatten_list([list(parse_user_info(x)) for x in out[0]])
    data = {}
    data['author'] = user_info[0::2]
    data['handle'] = user_info[1::2]
    data['timestamp'] = out[1]
    data['content'] = out[2]
    if len(name)>0:
        data['bookmark_owner_name'] = name
    else:
        data['bookmark_owner_name'] = np.nan
    if embed_handle:
        data['bookmark_owner_handle'] = this_user
    else:
        data['bookmark_owner_handle'] = np.nan

    data['tags'] = tags_str 

    df_tweet = pd.DataFrame(data).drop_duplicates()
    return df_tweet

def scrape_all_tweets(driver,**kwargs):
    wait_time = kwargs.get('wait_time',0.5)
    scroll_amount = kwargs.get('scroll_amount',500)
    tags = kwargs.get('tags',[])
    name = kwargs.get('name',[])
    embed_handle = kwargs.get('embed_handle',True)

    tweet_df = scroll_scrape(driver,wait_time=wait_time,scroll_amount=scroll_amount)

    return tweet_df

def scroll_scrape(driver,**kwargs):
    wait_time = kwargs.get('wait_time',0.5)
    scroll_amount = kwargs.get('scroll_amount',500)
    content_type = kwargs.get('content_type','tweets')
    
    i = 0
    still_adding = True
    while still_adding:
        if i == 0:
            if content_type == 'tweets':
                tweet_df = scrape_visible_tweets(driver,
                                                embed_handle=embed_handle,
                                                name=name,
                                                tags=tags)
            elif content_type == 'thread':
                tweet_df = scrape_visible_thread(driver)
        else:
            if content_type == 'tweets':
                tmp = scrape_visible_tweets(driver,
                                            embed_handle=embed_handle,
                                            name=name,
                                            tags=tags)
            elif content_type == 'thread':
                tmp = scrape_visible_thread(driver)
            tweet_df = pd.concat((tweet_df,tmp),axis=0).drop_duplicates()
        driver.execute_script('window.scrollBy(0, %d)' % scroll_amount)
        i+=1
        still_adding = len(driver.find_elements_by_xpath('//div[' + xpath_multiclass('css-1dbjc4n r-o52ifk') + ']')) == 0
        time.sleep(wait_time)
        
    return tweet_df

def get_nested_children(children_idcs):
    nested_children = '.'.join(['children[%d]' % x for x in children_idcs])
    return nested_children

def make_tweet_js_scripts():
    tweet_class = 'css-1dbjc4n r-1loqt21 r-18u37iz r-1ny4l3l r-1udh08x r-1qhn6m8 r-i023vh r-o7ynqc r-6416eg'
    #content_children = [0,0,0,1,1,1,0,0]
    content_children = [[0,0,0,1,1,1,0],[0,0,0,1,1,1,1,]]
    name_children = [0,0,0,1,1,0,0,0,0,0,0,0]
    handle_children = [0,0,0,1,1,0,0,0,0,0,0,1,0,0]
    timestamp_children = [0,0,0,1,1,0,0,0,0,0,0,1,0,2,0,0]
    thread_children = [0,1]

    fcns = {}
    fcns['name'] = 'return element.' + get_nested_children(name_children) + '.textContent'
    fcns['handle'] = 'return element.' + get_nested_children(handle_children) + '.textContent'
    #fcns['content'] = 'return element.' + get_nested_children(content_children) + '.textContent'
    fcns['content'] = 'if (element.textContent.includes("Replying to @")) {return element.' \
                + get_nested_children(content_children[1]) + '.textContent;}' \
                + 'else '\
                + '{return element.' \
                + get_nested_children(content_children[0]) + '.textContent;}'
    fcns['timestamp'] = 'return element.' + get_nested_children(timestamp_children) + '.getAttribute("datetime")'
    fcns['thread'] = 'if (element.children[0].children.length==2) {return element.' \
                    + get_nested_children(thread_children) + '.getAttribute("href");}'
    fcns['reply'] = 'element.textContent.includes("Replying to @")'

    tweet_class = format_classname(tweet_class)
    js = cat_js_scripts([make_js_script(tweet_class,x) for x in fcns.values()])
    var_names = fcns.keys()
    return js,var_names

def return_tweet_df(tweet_js_script,var_names):
    o = driver.execute_script(tweet_js_script)
    output = {x:y for x,y in zip(var_names,o)}

    df_tweets = pd.DataFrame(output)
    df_tweets['timestamp'] = df_tweets['timestamp'].apply(pd.Timestamp) 
    df_tweets['thread'] = df_tweets['thread'].apply(lambda x: 'https://twitter.com' + x if (x != None) else x)
    
    return df_tweets

def tweet_scroll_scrape(**kwargs):
    content_type = kwargs.get('content_type','tweet')
    thread_id = kwargs.get('thread_id','')
    scroll_amount = kwargs.get('scroll_amount',500)
    wait_time = kwargs.get('scroll_wait_time',0.25)

    js,var_names = make_tweet_js_scripts()

    i = 0
    still_adding = True
    driver.execute_script('window.scrollTo(0,0)')
    time.sleep(wait_time)
    while still_adding:

        # pull tweets/thread
        if (i == 0):
            df_tweets = return_tweet_df(js,var_names).drop_duplicates()
        else:
            tmp = return_tweet_df(js,var_names)
            df_tweets = pd.concat((df_tweets,tmp),axis=0).drop_duplicates()

        # assess if end of tweets/thread
        if content_type == 'tweet':
            # if not reached the bottom, keep adding
            still_adding = len(driver.find_elements_by_xpath('//div[' + xpath_multiclass('css-1dbjc4n r-o52ifk') + ']')) == 0
        elif content_type == 'thread':
            # if not reached the last thread tweet and not reached the bottom, keep adding
            still_adding = (df_tweets.loc[min([len(df_tweets)-1,1]):,'reply'].any()==False) & (len(driver.find_elements_by_xpath('//div[' + xpath_multiclass('css-1dbjc4n r-o52ifk') + ']')) == 0)
            flag = df_tweets.loc[:,'reply']==False
            flag[0] = True
            df_tweets = df_tweets.loc[flag,:]
        
        # if still adding, scroll down a step
        if still_adding:
            driver.execute_script('window.scrollBy(0, %d)' % scroll_amount)
            time.sleep(wait_time)
        i+=1
            
    if content_type=='thread':
        df_tweets['thread'] = thread_id
    return df_tweets

def scrape_all_bookmarks(**kwargs):
    scroll_amount = kwargs.get('scroll_amount',500)
    scroll_wait_time = kwargs.get('scroll_wait_time',0.25)
    page_wait_time = kwargs.get('page_wait_time',2)
    importer_id = kwargs.get('importer_id',np.nan)
    importer_handle = kwargs.get('importer_handle',np.nan)
    importer_tags = kwargs.get('importer_tags',np.nan)
    
    # get all bookmarked tweets
    df_tweets = tweet_scroll_scrape(content_type='tweet',
                                    scroll_amount=scroll_amount,
                                    scroll_wait_time=scroll_wait_time)

    # get all threads from bookmarked tweets
    threads = [x for x in df_tweets['thread'].unique() if x!=None]

    # walk through each thread, pulling thread tweets
    url0 = driver.current_url
    for thread in threads:
        # navigate to thread url and wait
        driver.get(thread)
        time.sleep(page_wait_time)
        
        # pull all tweets
        tmp = tweet_scroll_scrape(content_type='thread',
                                  thread_id=thread,
                                  scroll_amount=scroll_amount,
                                  scroll_wait_time=scroll_wait_time)
        
        # add to existing dataframe
        df_tweets = pd.concat((df_tweets,tmp),axis=0)
    driver.get(url0)

    # consolidate the final dataframe
    df_tweets = df_tweets.drop_duplicates().sort_values(by=['thread','timestamp'])
    df_tweets = df_tweets.assign(thread_idx=df_tweets.groupby(['name']).cumcount()).drop(columns='reply')
    df_tweets = df_tweets.reset_index(drop=True) 
    
    # add metadata
    df_tweets = df_tweets.assign(importer_id=importer_id)
    df_tweets = df_tweets.assign(importer_handle=importer_handle)
    if isinstance(importer_tags,list):
        if (len(importer_tags)>0):
            importer_tags = '|'.join(importer_tags)
    df_tweets = df_tweets.assign(importer_tags=importer_tags)
   
    return df_tweets 
