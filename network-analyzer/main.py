import json
import networkx

network_file = '../network.json'

#############################################
### AUXILIARY
#############################################

def refine_network(network_brute):
    network_refined = {}
    for key in network_brute.keys():
        network_refined[key] = {}
        for key1 in network_brute.keys():
            count = 0
            if key1 in network_brute[key]['dialogues'].keys():
                count += network_brute[key]['dialogues'][key1]
            if key1 in network_brute[key]['wiki_mentions'].keys():
                count += network_brute[key]['wiki_mentions'][key1]
            if count:
                network_refined[key][key1] = count
    return network_refined

#############################################
### MAIN
#############################################

def main():
    # get network
    f = open(network_file, 'r')
    network_brute = json.load(f)
    network = refine_network(network_brute)
    print(network)
    graph = networkx.Graph()
    for name in network.keys():
        graph.add_node(name)
    for name in network.keys():
        graph.add_weighted_edges_from([(name, other_name, value) for other_name, value in network[name].items()])

    # plot network
    networkx.write_graphml(graph, 'output.graphml')

    # make network-wise measurements and comparisons

    # plot network-wise measurements

    # make per node measurements

    # plot per node measurement graphs

if __name__ == "__main__":
    main()