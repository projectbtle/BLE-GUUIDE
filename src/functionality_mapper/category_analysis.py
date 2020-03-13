import json
import requests
import html2text
import nltk
import re
from nltk.wsd import lesk
from nltk import word_tokenize, regexp_tokenize
from nltk.corpus import wordnet as wn
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer("english")


class CategoryAnalyser:
    """
    This file can be imported to deal with text related tasks, including getting meaning out of them.
    """

    def __init__(self, basepath):
        super().__init__()
        path_to_categories = os.path.join(
            basepath,
            'resources/common/functional_categories_database.json'
        )
        with open(path_to_categories) as json_data:
            self.category_keywords = json.load(json_data)
        self.html_converter = html2text.HTML2Text()   
        self.html_converter.ignore_links = True    
    
    def get_all_children(self,cat,sub_cat,word):
        if cat not in self.category_keywords:
            return []
        if sub_cat not in self.category_keywords[cat]:
            return []
        if word not in self.category_keywords[cat][sub_cat]:
            return []
        result = []
        if 'children' in self.category_keywords[cat][sub_cat][word] and len(self.category_keywords[cat][sub_cat][word]['children']) > 0:
            for s_word in self.category_keywords[cat][sub_cat][word]['children']:
                if 'children' in self.category_keywords[cat][sub_cat][word]['children'][s_word] and len(self.category_keywords[cat][sub_cat][word]['children'][s_word]['children']) > 0:
                    for t_word in self.category_keywords[cat][sub_cat][word]['children'][s_word]['children']:
                        result.append([word, s_word, t_word])    
                else:
                    result.append([word, s_word])
        return result

    def match_text(self,text,match_meanings=False,single_word=False):
        """Matches a text with the functionality categories.
        
        Keyword arguments:
        text -- The text to match
        Return: return_description
        """
        text = text.lower()
        
        # Output object.
        matches = {}
        matches['category']= []
        matches['sub-category']= []
        matches['category_subcategory']= []
        matches['words']= []
        
        # If text is to be considered a string (not a word).
        if single_word == False:
            word_tokens = word_tokenize(text)
            try:
                # Split on underscore
                split_tokens = [split_token for split_token in (word_token.split('_') for word_token in word_tokens)]
                flat_tokens = [item for sublist in split_tokens for item in sublist]
                # Split on .
                second_split_tokens = [split_token for split_token in (word_token.split('.') for word_token in flat_tokens)]
                tokens = [item for sublist in second_split_tokens for item in sublist]
            except Exception as e:
                print(e)
            stemmed_tokens = [stemmer.stem(element) for element in tokens]
            # If the text is too short we just do a simple keyword search
            if len(tokens) < 10:
                match_meanings = False

        # Actual test.
        for category in self.category_keywords:
            for sub_category in self.category_keywords[category]:
                for index,word in enumerate(self.category_keywords[category][sub_category]):
                    # If word is nowhere in input text, no use in continuing?                 
                    if word not in text:
                        continue
                        
                    # Get children words.
                    word_children = self.get_all_children(category,sub_category,word)
                    
                    # Get blacklist.
                    black_list = self.category_keywords[category][sub_category][word]['blacklist']
                    
                    # Handle API/fields.
                    if (single_word == True):
                        if len(word_children)>0:
                            for next_word in word_children:
                                direct_joined_w = ''.join(next_word)
                                hyphen_joined_w = '-'.join(next_word)
                                uscore_joined_w = '_'.join(next_word)
                                for joined_w in [direct_joined_w, hyphen_joined_w, uscore_joined_w]:
                                    if joined_w in text:
                                        matches['category'].append(category)
                                        matches['sub-category'].append(sub_category)
                                        matches['category_subcategory'].append(category+':'+sub_category)
                                        matches['words'].append(joined_w)
                        else:
                            # check blacklist
                            no_blacklist = True
                            if len(black_list) > 0:
                                for blacklist_word in black_list:
                                    if blacklist_word in text:
                                        no_blacklist = False
                                        continue
                            if no_blacklist == True:
                                matches['category'].append(category)
                                matches['sub-category'].append(sub_category)
                                matches['category_subcategory'].append(category+':'+sub_category)
                                matches['words'].append(word) 
                    # Handle strings.
                    else:
                        # See if the words have children.
                        if len(word_children)>0:
                            for next_word in word_children:
                                direct_joined_w = ''.join(next_word)
                                space_joined_w = ' '.join(next_word)
                                hyphen_joined_w = '-'.join(next_word)
                                uscore_joined_w = '_'.join(next_word)
                                for joined_w in [direct_joined_w, space_joined_w, hyphen_joined_w, uscore_joined_w]:
                                    if joined_w in text:
                                        matches['category'].append(category)
                                        matches['sub-category'].append(sub_category)
                                        matches['category_subcategory'].append(category+':'+sub_category)
                                        matches['words'].append(joined_w)
                        else:
                            # Find the location(s) of the word within text.
                            all_indices = self.findall(text, word)
                            
                            if len(black_list) > 0:
                                for single_index in all_indices:
                                    for blacklist_word in black_list:
                                        len_word = len(word)
                                        len_blacklist_word = len(blacklist_word)
                                        lower_boundary = single_index - len_blacklist_word
                                        if lower_boundary < 0:
                                            lower_boundary = 0
                                        upper_boundary = single_index + len_word + len_blacklist_word
                                        if upper_boundary > (len(text)-1):
                                            upper_boundary = len(text) - 1
                                        text_of_interest = text[lower_boundary: upper_boundary]
                                        if blacklist_word in text_of_interest:
                                            try:
                                                all_indices.remove(single_index)
                                            except:
                                                break
                                                
                            if len(all_indices) == 0:
                                continue

                            if match_meanings == True:
                                meanings = self.category_keywords[category][sub_category][word]['meaning']
                                if len(meanings)>0:
                                    for token_index in token_indices:
                                        boundary = min([20,token_index,len(tokens)-token_index])
                                        meaning = lesk(tokens[token_index-boundary:token_index+boundary], word)            
                                        if meaning is not None and meaning.name() in meanings:
                                            matches['category'].append(category)
                                            matches['sub-category'].append(sub_category)
                                            matches['category_subcategory'].append(category+':'+sub_category)   
                                            matches['words'].append(word)
                                else:
                                    matches['category'].append(category)
                                    matches['sub-category'].append(sub_category)
                                    matches['category_subcategory'].append(category+':'+sub_category)   
                                    matches['words'].append(word) 
                            else:
                                matches['category'].append(category)
                                matches['sub-category'].append(sub_category)  
                                matches['category_subcategory'].append(category+':'+sub_category)                            
                                matches['words'].append(word)
        return matches

    def findall(self, string, substring):
        all_indices = []
        i = string.find(substring)
        while i != -1:
            all_indices.append(i)
            i = string.find(substring, i+1)
        return all_indices
        
    def contained_in(self,word,word_list):
        for element in word_list:
            if word in element:
                return True
        return False
    
    def match_short_call(self,text):
        """Matches a text with the functionality categories.
        
        Keyword arguments:
        text -- The text to match
        size_limit -- it won't count words with less than those characters for the matchings (useful to avoid matches with 'car', etc.)
        Return: return_description
        """
        matches = {}
        matches['category']= []
        matches['sub-category']= []
        matches['category_subcategory'] = []
        result = re.search(r"<(.*): [\w|\d|\$|\.|\[\]]* (.*)\(",text)
        text = '{0} {1}'.format(result.group(1),result.group(2))
        text = text.lower()
        for category in self.category_keywords:
            for sub_category in self.category_keywords[category]:
                for word in self.category_keywords[category][sub_category]:
                    if word in text:
                        matches['category'].append(category)
                        matches['sub-category'].append(sub_category)
                        matches['category_subcategory'].append(category+':'+sub_category)   
                    elif text.endswith(word):
                        matches['category'].append(category)
                        matches['sub-category'].append(sub_category)
                        matches['category_subcategory'].append(category+':'+sub_category)   
        return matches

    def match_call(self,text,size_limit=3):
        """Matches a text with the functionality categories.
        
        Keyword arguments:
        text -- The text to match
        size_limit -- it won't count words with less than those characters for the matchings (useful to avoid matches with 'car', etc.)
        Return: return_description
        """
        matches = {}
        matches['category']= []
        matches['sub-category']= []
        matches['category_subcategory'] = []
        text = text.lower()
        for category in self.category_keywords:
            for sub_category in self.category_keywords[category]:
                for word in self.category_keywords[category][sub_category]:
                    if word in text and len(word)>size_limit:
                        matches['category'].append(category)
                        matches['sub-category'].append(sub_category)
                        matches['category_subcategory'].append(category+':'+sub_category)   
                    elif text.endswith(word):
                        matches['category'].append(category)
                        matches['sub-category'].append(sub_category)
                        matches['category_subcategory'].append(category+':'+sub_category)   
        return matches

    def check_website(self,url):
        headers = {"Accept-Language": "en-US,en;q=0.5"}
        r = requests.get(url, headers=headers)
        filtered_text = self.html_converter.handle((r.text)).replace('\n','')
        return self.match_text(filtered_text)
