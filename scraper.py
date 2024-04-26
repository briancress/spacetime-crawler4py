import re
from urllib.parse import urlparse, urljoin
from urllib import robotparser
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
import hashlib
previous_hashes = set()

# Set of unique pages
unique_pages = set()
# List containing url at index 0, count at index 1
longest_page_words = ['page_url', 0]
# Dictionary containing [word] = # of occurrences
word_frequency = {}
# Dictionary containing [subdomain] = # of occurrences
subdomains = {}
# Set of all visited urls
visited_urls = set()
# Used to index the previous few links to detect traps
previous_links = []

count = 0

def calculate_hash(content):
    # Calculate hash value
    content_hash = hashlib.sha256(content).hexdigest()
    return content_hash

def record_data():
    # Log all data to it's files

    # Record number of unique pages
    num_unique_pages = len(unique_pages)
    with open("UniquePages.txt", "a") as file:
        file.write("Number of Unique Pages: " + str(num_unique_pages) + "\n")

    # Record longest page in terms of words
    longest_page = longest_page_words[0]
    longest_page_count = longest_page_words[1]
    with open("Longestpage.txt", "a") as file:
        file.write("Longest Page: " + str(longest_page) + "\n")
        file.write("Number of words: " + str(longest_page_count) + "\n")

    # Record most common 50 words
    sorted_word_frequency = dict(sorted(word_frequency.items(), key=lambda item: (-item[1], item[0])))
    with open("TopWords.txt", "w") as file:
        # Iterate over dictionary
        timeCounter = 0
        for word, frequency in sorted_word_frequency.items():
            file.write(f"{word}: {frequency}\n")
            # Break the loop when 50 items are written
            if timeCounter >= 50:
                break
            timeCounter += 1

    # Record all subdomains under ics.uci.edu
    sorted_subdomains = dict(sorted(subdomains.items()))
    with open("Subdomains.txt", "w") as file:
        # Iterate over dictionary
        for sub, frequency in sorted_subdomains.items():
            file.write(f"{sub}: {frequency}\n")

    return

def scraper(url, resp):
    # DO WE USE URL OR RESP.URL IN SCRAPER?
    # we already used resp.url in extract_next_links so idk ????????????????????????????????????????????????????????????????????????
    global unique_pages
    global longest_page_words
    global word_frequency
    global subdomains
    global visited_urls
    global count
    global previous_links
    global previous_hashes

    url = resp.url
    url = url.split("#")[0]

    try:
        # Use a try in case it gives 200 but page doesn't exist
        links = extract_next_links(url, resp)
    except Exception as e:
        print('Exception: Error extracting next link')
        return []

    # Return empty links and don't count if bad status
    if links == []:
        return []
    
    #print(f'Checking trap: {url}')
    if is_Trap(url):
        print(f'Is a trap: {url}')
        return []

    current_hash = calculate_hash(resp.raw_response.content)
    if current_hash in previous_hashes:
        print('Not browsing, exact page has been seen')
        return []
    else:
        previous_hashes.add(current_hash)

    # Add url to visited
    # visited_urls contains all visited urls, the entire url (not used for counting unique urls, only for not re-visiting)
    visited_urls.add(url)
    #visited_urls.add(resp.url)

    previous_links.append(url)

    if len(previous_links) > 500:
        previous_links = []

    count += 1
    print('Current count:' + str(count))

    if count >= 300 and count % 300 == 0:
        # call recording function
        record_data()
        pass

    # Uniqueness is only established by URL, not fragment
    # Get rid of fragment after '#' and add to unique pages
    no_fragment_url = url.split("#")[0]
    unique_pages.add(no_fragment_url)

    # Update longest page word count
    update_longest_word_page(url, resp.raw_response.content)

    # Update word frequency for current URL page
    update_word_frequency(resp.raw_response.content)

    # Total subdomains in the ics.uci.edu domain
    update_subdomain(url)

    print(f"Visiting url : '{url}'")

    #return [link for link in links if is_valid(link)]
    f = [link for link in links if is_valid(link)]
    #for link in links:
     #   visited_urls.add(link)
      #  previous_links.append(url)

    return f

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # Filter for an unsuccessful status code
    if resp.status != 200:
        return []

    # Parse HTML with beautiful soup
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

    # Extract links from the html
    links = []
    # Find all links in the html
    for link in soup.find_all('a'):
        # Get href from each link
        href = link.get('href')
        # Join the original url with the new href and append
        if href:
            # Check if href is a full URL
            if href.startswith('http://') or href.startswith('https://'):
                full_url = href
            else:
                # Join relative URL with the original URL (resp.url)
                #base_url = urlparse(resp.url).scheme + '://' + urlparse(resp.url).netloc
                #full_url = urljoin(base_url, href)
                full_url = urljoin(url, href)
               # if has_repeating_component(full_url):
                   # base_url = urlparse(resp.url).scheme + '://' + urlparse(resp.url).netloc
                    #full_url = urljoin(base_url, href)
            # Remove fragment from the full URL
            full_url = full_url.split('#')[0]
            links.append(full_url)

    return links


def has_repeating_component(url):
    # Split the URL by slashes
    components = url.split('/')

    # Count occurrences of each component
    component_count = {}
    for component in components:
        if component in component_count:
            component_count[component] += 1
        else:
            component_count[component] = 1
    # Check if any component repeats
    for count in component_count.values():
        if count >= 2:
            return True

    return False

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global visited_urls

    try:
        parsed = urlparse(url)
        if "filter" in url:
            return False
        if is_Trap(url):
            return False
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not re.match(r"(www\.)?(ics|cs|informatics|stat)\.uci\.edu", parsed.netloc):
            return False
        if not re.match(r"/\w+", parsed.path):
            return False
        if url in visited_urls:
            return False
        if not robots_valid_search(url):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r" |png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def is_Trap(url):
    global visited_urls
    global previous_links

    if len(url) > 300:
        # with open("TestTrap.txt", "a") as file:
        #     file.write("It's a 300 trap " + url + "\n")
        return True

    if len(previous_links) > 150:

        # Loop through previous 20 URLs
        for i in range(-1, -140, -1):
            past_url = previous_links[i]

            url_length = len(url)
            num_differences = 0

            if url_length != len(past_url):
                return False
            
            # Loop through each past URL and compare to current
            for j in range(url_length):

                if url[j] != past_url[j]:
                    num_differences += 1

            if num_differences > 3:
                # Not in trap if URLs differ by more than 3 characters
                return False
            else:
                # Reset for next URL
                num_differences = 0
        # If it loops through all 20 URLs and their differences arent high enough, you are in a trap
        with open("TestTrap.txt", "a") as file:
            file.write("It's a trap " + url + "\n")
        return True

    else:
        # False (Not in trap) if haven't even visited 50 urls yet
        return False


def update_longest_word_page(url, page_content):
    global longest_page_words

    # Parse the page content with beautiful soup
    soup = BeautifulSoup(page_content, 'html.parser')
    # Get the actual text content fromt he created soup
    text_content = soup.get_text(separator = ' ')
    # extract all the words using regex
    extracted_words = re.findall(r'\b[A-Za-z]+\b', text_content)

    word_count = len(extracted_words)

    if (word_count > longest_page_words[1]):
        longest_page_words[0] = url
        longest_page_words[1] = word_count


def update_word_frequency(page_content):
    global word_frequency

    english_stopwords = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 
    'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 
    'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', 
    "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 
    'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 
    'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', 
    "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 
    'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', '', '', '', 'ourselves', 'out', 
    'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 
    'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 
    'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 
    'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 
    'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', 
    "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves'}

    # Parse the page content with beautiful soup
    soup = BeautifulSoup(page_content, 'html.parser')
    # Get the actual text content fromt he created soup
    text_content = soup.get_text(separator = ' ')
    # extract all the words using regex
    extracted_words = re.findall(r'\b[A-Za-z]+\b', text_content)

    # Update frequency for each word
    for word in extracted_words:
        word = word.lower()

        if word not in word_frequency and word not in english_stopwords:
            word_frequency[word] = 1
        elif word in word_frequency and word not in english_stopwords:
            word_frequency[word] += 1
        else:
            pass

def highContent(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    # Get the actual text content fromt he created soup
    text_content = soup.get_text(separator = ' ')
    # extract all the words using regex
    extracted_words = word_tokenize(text_content)

    if len(extracted_words) > 1800:
        return True
    else:
        return False

def update_subdomain(url):
    global subdomains

    # Only count subdomains in the ics.uci.edu domain
    parsed_url = urlparse(url)
    # Get subdomain by splitting once at the first period
    # subdomain = [vision].ics.uci.edu
    subdomain = parsed_url.netloc.split('.', 1)[0]
    #Get domain
    # domain = [vision.ics.uci.edu]
    domain = parsed_url.netloc

    # Check if the domain ends with ics.uci.edu
    if domain.endswith('ics.uci.edu'):
        # Increment the subdomain's count
        if domain not in subdomains:
            subdomains[domain] = 1
        else:
            subdomains[domain] += 1

def robots_valid_search(url):
    try:
        # gets site portion of url
        site = urlparse(url).netloc
        # gets robots txt of that site
        robots_txt_url = f"http://{site}/robots.txt"
        robotUrl = requests.get(robots_txt_url)

        # if robots site can successfully be reached
        if robotUrl.status_code == 200:
            txt = robotUrl.text # the content of robots
            # goes through every line of the content and determines which are disallowed
            for line in txt.split('\n'):
                if line.strip().startswith('Disallow:'):
                    disallowed_path = line.split(': ')[1].strip()
                    if url.endswith(disallowed_path):
                        return False
            return True 
        else:
            return True
    # throws exception
    except Exception as e:
        return True
