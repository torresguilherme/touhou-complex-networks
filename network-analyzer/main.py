import json
import networkx
import csv
import random
import time
import matplotlib.pyplot as plt

network_file = '../network.json'
data_csv = 'data.csv'
network = {}
network_connected_components = 14
network_biggest_component_size = 0

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

def parse_csv():
    f = open(data_csv, 'r')
    iterable = csv.reader(f)
    ret = {}
    for it in iterable:
        try:
            ret[it[0]] = float(it[9])
        except ValueError:
            pass
    return ret

#############################################
### ATTACK SIMULATION
#############################################

def normalization(network):
    sum = 0
    for key in network.keys():
        sum += network[key]
    
    for key in network.keys():
        network[key] *= 1/sum

def resisted(attacked_network, nodes_taken):
    # ve se o grafo é conectado
    can_be_reached = [False] * len(attacked_network.keys())
    components = 0
    biggest_component = 0
    while False in can_be_reached:
        point_queue = [can_be_reached.index(False)]
        count = 0
        while len(point_queue):
            current_point = point_queue[0]
            can_be_reached[current_point] = True
            count += 1
            for i in range(len(attacked_network.keys())):
                if list(attacked_network.keys())[i] in network[list(attacked_network.keys())[current_point]].keys():
                    if not can_be_reached[i]:
                        can_be_reached[i] = True
                        point_queue.append(i)
            point_queue.remove(current_point)
        components += 1
        biggest_component = max(count, biggest_component)
    if nodes_taken == 0:
        global network_biggest_component_size
        network_biggest_component_size = biggest_component
    return biggest_component > network_biggest_component_size // 2

def single_attack(network_with_weights, n):
    network_to_attack = network_with_weights.copy()
    for i in range(n):
        randfloat = random.uniform(0, 1)
        for key in network_to_attack.keys():
            randfloat -= network_to_attack[key]
            if randfloat <= 0:
                network_to_attack.pop(key)
                normalization(network_to_attack)
                break
    if resisted(network_to_attack, n):
        return 0
    else:
        return 1

def attack_success_probability(network_with_weights, n):
    successes = 0
    for i in range(30):
        successes += single_attack(network_with_weights, n)
    print('conseguiu atacar com chance ' + str(successes/30))
    return successes / 30

def attack_network(network_with_weights):
    results = []
    for n in range(len(network_with_weights.keys()) // 2):
        print('Atacando rede tirando ' + str(n) + ' nos')
        results.append((n, attack_success_probability(network_with_weights, n)))
    return results

#############################################
### MAIN
#############################################

def main():
    global network
    random.seed(time.time())
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

    # simulate attacks
    network_with_weights = parse_csv()
    normalization(network_with_weights)

    to_be_plotted = attack_network(network_with_weights)

    # plot network attack results
    plt.title('Attack simulation')
    plt.xlabel('Nodes taken out')
    plt.ylabel('Success probability')
    plt.plot([x[0] for x in to_be_plotted], [x[1] for x in to_be_plotted], 'bo')
    plt.axis([0, 100, 0, 1])
    plt.savefig('attack_sim.png')
    plt.show()

    return 0

if __name__ == "__main__":
    main()