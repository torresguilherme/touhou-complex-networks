import html.parser as parser
import json

INDEX = '../touhou_wiki/en.touhouwiki.net/index.html'
CHARACTERS_PAGE = '../touhou_wiki/en.touhouwiki.net/wiki/Category_Characters.html'
MAIN_CHAR_1 = '../touhou_wiki/en.touhouwiki.net/wiki/Reimu_Hakurei.html'
MAIN_CHAR_2 = '../touhou_wiki/en.touhouwiki.net/wiki/Marisa_Kirisame.html'

network = {}
links = []

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
                    links.append(attr)
                elif name == 'title' and not 'Characters' in attr:
                    network[attr] = {
                        'dialogues': {},
                        'fought': {},
                        'mentions': {},
                        'major_relationship_wiki': {},
                        'minor_relationship_wiki': {}
                    }

def main():
    # parse init page
    html_parser = CharactersFinder()
    html_parser.reading_chars = False
    html_parser.count = 0
    characters_file = open(CHARACTERS_PAGE, 'r')
    line_list = characters_file.readlines()
    for line in line_list:
        html_parser.feed(line)
    
    json_string = json.dumps(network)
    with open('../network.json', 'w') as f:
        f.write(json_string)
    
    return 0

if __name__ == "__main__":
    main()