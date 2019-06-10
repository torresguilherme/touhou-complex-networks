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
games_text = {}
print_works = {}
print_works_text = {}

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
                        'wiki_mentions': {},
                        'relationship_wiki': []
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
            games_text[page_name] = page_addr.split('.')[0] + '/Story.html'
        
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

class LinkEnqueuer(parser.HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, attr in attrs:
                if name == 'href':
                    tree = link_queue[0].split('/')
                    cur_dir = ''
                    for i in range(len(tree)-1):
                        cur_dir = cur_dir + tree[i] + '/'
                    attr = cur_dir + attr
                    attr = unquote(attr)
                    query_index = attr.find('?')
                    if query_index != -1:
                        attr = attr.split('?')[0]
                    if attr not in link_queue:
                        print('found new link: ' + attr)
                        link_queue.append(attr)

class ScenarioLinkEnqueuer(parser.HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, attr in attrs:
                if name == 'href' and 'Scenario' in attr:
                    tree = link_queue[0].split('/')
                    cur_dir = ''
                    for i in range(len(tree)-1):
                        cur_dir = cur_dir + tree[i] + '/'
                    attr = cur_dir + attr
                    attr = unquote(attr)
                    query_index = attr.find('?')
                    if query_index != -1:
                        attr = attr.split('?')[0]
                    if attr not in link_queue:
                        print('found new link: ' + attr)
                        link_queue.append(attr)

################################################
### PARSERS - NETWORK BUILDERS
################################################

char_stack = {}

class DialogueParser(parser.HTMLParser):
    def handle_data(self, data):
        global char_stack
        for name in characters:
            if name in data:
                index = data.find(name)
                if len(data) > index + len(name) and data[index + len(name)].isalpha():
                    pass
                else:
                    char_stack[name] = 5
            elif name.split()[0] in data:
                first_name = name.split()[0]
                index = data.find(first_name)
                if len(data) > index + len(first_name) and data[index + len(first_name)].isalpha():
                    pass
                else:
                    char_stack[name] = 3
        for key in char_stack.keys():
            char_stack[key] -= 1
        char_stack = {key:val for key, val in char_stack.items() if val != 0}
        for key1 in char_stack.keys():
            for key2 in char_stack.keys():
                if key1 != key2:
                    tie_in_dialogue(key1, key2)

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
        if tag == 'h3':
            for name, attr in attrs:
                if name == 'class' and attr == 'in-block':
                    self.reading_relationships = True
    
    def handle_data(self, attr):
        if self.reading_relationships:
            for name in characters:
                index = attr.find(name)
                if index != -1:
                    # exception cases
                    if name == self.character or (len(attr) > index + len(name) and attr[index + len(name)].isalpha()):
                        pass
                    elif not name in network[self.character]['relationship_wiki']:
                        network[self.character]['relationship_wiki'].append(name)

    def handle_endtag(self, tag):
        if tag == 'h3':
            self.reading_relationships = False

def tie_in_dialogue(char1, char2):
    if char2 in network[char1]['dialogues'].keys():
        network[char1]['dialogues'][char2] += 1
    else:
        network[char1]['dialogues'][char2] = 1
    if char1 in network[char2]['dialogues'].keys():
        network[char2]['dialogues'][char1] += 1
    else:
        network[char2]['dialogues'][char1] = 1

def parse_page(html_parser, page_addr):
    html_parser.reset()
    try:
        with open(WIKI_PREFIX + page_addr, 'r') as f:
            for line in f.readlines():
                html_parser.feed(line)
    except FileNotFoundError:
        print('nao encontrou arquivo no prefixo da wiki: ' + page_addr)

def parse_page_recursive(html_parser, page_addr, scenario=False):
    aux_parser = LinkEnqueuer()
    if scenario:
        aux_parser = ScenarioLinkEnqueuer()
    link_queue.append(page_addr)
    while len(link_queue):
        parse_page(html_parser, link_queue[0])
        parse_page(aux_parser, link_queue[0])
        link_queue.remove(link_queue[0])

################################################
### MAIN
################################################

def main():
    # parse init page
    html_parser = CharactersFinder()
    html_parser.reading_chars = False
    parse_page(html_parser, CHARACTERS_PAGE)

    # remove noise/not real characters
    characters.remove('Rin Satsuki')
    characters.remove('Hakurei God')
    characters.remove('Marisa\'s unnamed father')
    characters.remove('Reisen')
    char_links.remove('Rin_Satsuki.html')
    char_links.remove('Hakurei_God.html')
    char_links.remove('Marisa\'s_unnamed_father.html')
    char_links.remove('Reisen.html')

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

    # parsing dialogues
    html_parser = DialogueParser()
    for page_name in games_text.keys():
        parse_page_recursive(html_parser, games_text[page_name], scenario=True)
    
    for print_name in print_works.keys():
        parse_page(html_parser, print_works[print_name])

    # parsing wiki
    for i in range(len(characters)):
        # parse mentions
        html_parser = MentionParser()
        html_parser.character = characters[i]
        link = char_links[i]
        parse_page(html_parser, link)

        # parse relationships
        html_parser = RelationshipParser()
        html_parser.character = characters[i]
        html_parser.reading_relationships = False
        link = char_links[i]
        parse_page(html_parser, link)

    ################################################
    ### END OF NETWORK BUILDING
    ################################################

    json_string = json.dumps(network)
    with open('../network.json', 'w') as f:
        f.write(json_string)
    
    return 0

if __name__ == "__main__":
    main()