import json
from multiprocessing.pool import Pool

import requests

sites = dict()
visited_sites = set()


def is_html_text(url):

    if url.find('.css') != -1 or url.find('.png') != -1 or url.find('.xml') != -1 or url.find('.jpg') != -1:
        return False

    if url.startswith('http://'):
        r = requests.head(url)
        if r.status_code != 200:
            return False
        return r.headers["content-type"].startswith("text/html")
    else:
        return False


def extract_links(line, links):
    line = str(line)
    length = len(line)
    indexes = []

    start_search = 0
    while True:
        index = line.find('href', start_search)
        if index == -1:
            break
        indexes.append(index + 4)
        start_search = index + 1

    # state machine
    # 0 - start
    # 1 - =
    # 2 - link body

    for index in indexes:

        state = 0
        index_from = -1

        for i in range(index, length):

            if state == 2 and (line[i] == ' ' or line[i] == '"' or line[i] == "'" or line[i] == '>'):
                link = line[index_from:i]
                links.append(link)
                break

            if line[i] == ' ':
                continue

            if line[i] == '=' and state == 0:
                state = 1

            if state == 1 and line[i] == 'h':
                state = 2
                index_from = i


def verify_html(link, root=''):
    if link.find(root) == -1:
        return None
    is_text = is_html_text(link)
    if not is_text:
        print(link + ' is not html document, skip...')
        return None
    else:
        print(link + ' is html document, process...')
        if link[-1] == '/':
            link = link[:-1]
        return link


def grab_links(root, url) -> []:
    r = requests.get(url)
    if r.status_code != 200:
        return
    lines = r.text.split('\n')
    lines = filter(lambda x: x.find(root) != -1, lines)

    links = []
    result = set()

    for line in lines:
        extract_links(line, links)

    pool = Pool(8)
    result = pool.map(verify_html, links)
    result = filter(lambda x: x is not None, result)

    return result


def parse_site(root, url):
    print()
    print('-------------------- grab -----------------------')
    print('Start grab links from ' + url)
    print()
    links = grab_links(root, url)

    visited_sites.add(url)
    sites[url] = []

    links = list(links)

    for link in links:
        if not link in sites[url]:
            sites[url].append(link)
        if not link in visited_sites:
            parse_site(root, link)


def main():
    url = ''
    parse_site(url, url)
    print(sites)

    fp = open("report.json", "w")
    json.dump(sites, fp)
    fp.close()

if __name__ == '__main__':
    main()
