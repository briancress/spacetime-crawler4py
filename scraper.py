import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

unique_pages = set()
longest_page_words = 0
word_frequency = {}
subdomains = {}

def scraper(url, resp):
    global unique_pages
    global longest_page_words
    global word_frequency
    global subdomains

    links = extract_next_links(url, resp)

    unique_pages.update(links)

    # Update longest page word count
    for link in links:
        words = link.split('/')
        word_count = len(words[-1].split('-')) if words[-1] else 0
        longest_page_words = max(longest_page_words, word_count)

    update_word_frequency(resp.raw_response.content)

    update_subdomain(url)

    return [link for link in links if is_valid(link)]

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

    # Parse the HTML content
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

    # Extract links from the page
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            full_url = urljoin(resp.url, href)
            #if is_valid(full_url):
            links.append(full_url)

    return links
    # return list()

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not re.match(r"(www\.)?(ics|cs|informatics|stat)\.uci\.edu", parsed.netloc):
            return False
        if not re.match(r"/\w+", parsed.path):
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

def update_word_frequency(response_content):
    global word_frequency

    english_stopwords = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", 
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", 
    "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", 
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", 
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", 
    "other", "ought", "our", "ours"
    }

    extracted_words = re.findall(r'\b[A-Za-z]+\b', response_content.decode('utf-8'))

    for word in extracted_words:
        word = word.lower()

        if word not in word_frequency and word not in english_stopwords:
            word_frequency[word] = 1
        elif word in word_frequency and word not in english_stopwords:
            word_frequency[word] += 1
        else:
            pass


def update_subdomain(url):
    global subdomains

    parsed_url = urlparse(url)
    domain = parsed_url.netloc.split('.')[0]
    if domain not in subdomains:
        subdomains[domain] = 0
    subdomains[domain] += 1
