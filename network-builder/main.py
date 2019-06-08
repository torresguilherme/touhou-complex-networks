import html.parser as parser
import json
from urllib.parse import unquote

WIKI_PREFIX = '../touhou_wiki/en.touhouwiki.net/wiki/'
CHARACTERS_PAGE = 'Category_Characters.html'
GAMES_PAGE = 'Touhou_Wiki.html'
LITERATURE_PAGE = 'Official_Literature.html'

network = {}
char_links = []
characters = []
link_queue = []
links_visited = []
games = {}
print_works = {}

################################################
### PARSERS - FINDERS
################################################

class CharactersFinder(parser.HTMLParser):
    def handle_starttag(self, tag, attrs):
        global network
        if tag == 'div':
            if self.reading_chars:
                self.reading_chars = False
            for name, attr in attrs:
                if name == 'class' and attr == 'mw-category-group':
                    self.reading_chars = True
        
        if tag == 'a' and self.reading_chars:
            for name, attr in attrs:
                if name == 'href' and not 'Characters' in attr:
                    char_links.append(unquote(attr))
                elif name == 'title' and not 'Characters' in attr:
                    network[attr] = {
                        'dialogues': {},
                        'fought': {},
                        'wiki_mentions': {},
                        'major_relationship_wiki': {},
                        'minor_relationship_wiki': {}
                    }
                    characters.append(attr)

class GamesFinder(parser.HTMLParser):
    def handle_data(self, data):
        if 'Games' in data and not self.lock:
            if 'Other' in data:
                self.reading_games = False
                self.lock = True
            else:
                self.reading_games = True

    def handle_starttag(self, tag, attrs):
        if tag == 'a' and self.reading_games:
            page_name = ''
            page_addr = ''
            for name, attr in attrs:
                if name == 'href':
                    page_addr = attr
                elif name == 'title':
                    page_name = attr
            games[page_name] = page_addr
        
    def handle_endtag(self, tag):
        if tag == 'p' and self.reading_games:
            self.reading_games = False

class PrintWorksFinder(parser.HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'li':
            self.reading_prints = True
        if tag == 'a' and self.reading_prints:
            page_name = None
            page_addr = None
            for name, attr in attrs:
                if name == 'href':
                    page_addr = attr
                elif name == 'title':
                    page_name = attr
            if page_addr and page_name:
                print_works[page_name] = page_addr

    def handle_endtag(self, tag):
        if tag == 'li':
            self.reading_prints = False

################################################
### PARSERS - NETWORK BUILDERS
################################################

class DialogueParser(parser.HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == '':
            pass

class FightParser(parser.HTMLParser):
    def handle_starttag(self, tag, attrs):
        pass

class MentionParser(parser.HTMLParser):
    def handle_data(self, data):
        for name in characters:
            index = data.find(name)
            if index != -1:
                # exception cases
                if name == self.character or (len(data) > index + len(name) and data[index + len(name)].isalpha()):
                    pass
                elif name in network[self.character]['wiki_mentions'].keys():
                    network[self.character]['wiki_mentions'][name] += 1
                else:
                    network[self.character]['wiki_mentions'][name] = 1

class RelationshipParser(parser.HTMLParser):
    def handle_starttag(self, tag, attrs):
        pass

def parse_page(html_parser, page_addr):
    html_parser.reset()
    try:
        with open(WIKI_PREFIX + page_addr, 'r') as f:
            for line in f.readlines():
                html_parser.feed(line)
    except FileNotFoundError:
        print('nao encontrou arquivo no prefixo da wiki: ' + page_addr)

################################################
### MAIN
################################################

def main():
    # parse init page
    html_parser = CharactersFinder()
    html_parser.reading_chars = False
    parse_page(html_parser, CHARACTERS_PAGE)
    
    ################################################
    ### BUILDING NETWORK
    ################################################

    # parsing dialogues
    # first, get the games from the wiki
    html_parser = GamesFinder()
    html_parser.reading_games = False
    html_parser.lock = False
    parse_page(html_parser, GAMES_PAGE)

    # and print works
    html_parser = PrintWorksFinder()
    html_parser.reading_prints = False
    parse_page(html_parser, LITERATURE_PAGE)
    print(print_works)

    # parsing dialogues
    html_parser = DialogueParser()
    for page_name in games.keys():
        parse_page(html_parser, games[page_name])
    
    for print_name in print_works.keys():
        parse_page(html_parser, print_works[print_name])

    # parsing fights

    # parsing mentions
    for i in range(len(characters)):
        html_parser = MentionParser()
        html_parser.character = characters[i]
        link = char_links[i]
        parse_page(html_parser, link)

    # parsing relationships

    ################################################
    ### END OF NETWORK BUILDING
    ################################################

    json_string = json.dumps(network)
    with open('../network.json', 'w') as f:
        f.write(json_string)
    
    return 0

if __name__ == "__main__":
    main()