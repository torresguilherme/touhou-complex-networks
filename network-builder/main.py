import html.parser as parser
import json

INDEX = '../touhou_wiki/en.touhouwiki.net/index.html'

def main():
    # init file to be saved
    graph = {}

    # parse init page
    html_parser = parser.HTMLParser()
    index_file = open(INDEX, 'r')
    line_string = index_file.readlines()
    parser.feed(line_string)

if __name__ == "__main__":
    pass