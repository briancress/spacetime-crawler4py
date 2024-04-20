import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

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

def scraper(url, resp):
    global unique_pages
    global longest_page_words
    global word_frequency
    global subdomains
    global visited_urls

    links = extract_next_links(url, resp)

    # Return empty links and don't count if bad status
    if links == []:
        return []

    # Add url to visited
    # visited_urls contains all visited urls, the entire url (not used for counting unique urls, only for not re-visiting)
    visited_urls.add(url)

    # Uniqueness is only established by URL, not fragment
    # Get rid of fragment after '#' and add to unique pages
    no_fragment_url = url.split("#")[0]
    unique_pages.add(no_fragment_url)

    # Update longest page word count
    update_longest_word_page(url, resp.raw_response.content)

    # I think this is counting the words in the link instead of the words in the page
    # for link in links:
    #     words = link.split('/')
    #     word_count = len(words[-1].split('-')) if words[-1] else 0
    #     longest_page_words = max(longest_page_words, word_count)

    # Update word frequency for current URL page
    update_word_frequency(resp.raw_response.content)

    # Total subdomains in the ics.uci.edu domain
    update_subdomain(url)

    print(f"Visiting url : '{url}'")

    #return [link for link in links if is_valid(link)]
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
            full_url = urljoin(resp.url, href)
            links.append(full_url)

    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global visited_urls

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not re.match(r"(www\.)?(ics|cs|informatics|stat)\.uci\.edu", parsed.netloc):
            return False
        if not re.match(r"/\w+", parsed.path):
            return False
        if url in visited_urls:
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
        if subdomain not in subdomains:
            subdomains[subdomain] = 0
        subdomains[subdomain] 
