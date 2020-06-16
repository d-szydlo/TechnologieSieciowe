#!/usr/bin/python

import networkx as nx
from pyvis.network import Network
from random import randint, uniform

edg = []

#funkcja generujaca losowy graf
def generate_random_graph(node_num, edg_num):
    graph = nx.Graph()
    graph.add_nodes_from(list(range(node_num))) #generowanie wierzcholkow
    edg_per_node = edg_num//node_num #rozdzielenie krawedzi kazdemu z wierzcholkow po rowno
    extra = edg_num%node_num #dodatkowe krawedzi do rozdania
    edges = []
    for i in range(node_num):
        if_extra = randint(0,1) #losowanie czy wierzcholek dostanie dodatkowa krawedz
        if extra > 0 and (node_num - i == extra or if_extra):
            rng = range(edg_per_node+1)
            extra -= 1
        else:
            rng = range(edg_per_node)

        for _ in rng:
            j = randint(0, node_num-1) #losowanie wierzcholka do ktorego zostanie poprowadzona krawedz
            while (i,j) in edges or (j,i) in edges or i == j: #losujemy dalej dopoki nie dostaniemy wierzcholka z ktorym biezacy nie jest polaczony
                j = randint(0, node_num-1)
            edges.append((i,j))
    for edge in edges:
        graph.add_edge(*edge, capacity = 0, taken = 0) #dodajemy wszystkie wygenerowane krawedzie do grafu
            
    return graph

#funckja generujaca dodecahedron
def generate_nice_graph():
    graph = nx.Graph()
    graph.add_nodes_from(list(range(20)))
    edges = []
    for i in range(19):
        edges.append((i, i+1))
    edges += [(4,0), (14,5), (15,19)]
    i = 0
    j = 13
    while i<5:
        edges.append((i,j))
        edges.append((i+16, j-1))
        i += 1
        j -= 2
    edges.remove((20, 4))
    for edge in edges:
        graph.add_edge(*edge, capacity = 0, taken = 0)
    global edg
    edg = edges
    return graph

#funkcja generujaca macierz natezen o maksymalnej liczbie wysylanych pakietow max_p
def generate_N_matrix(node_num, max_p):
    return [[randint(0, max_p) if i != j else 0 for j in range(node_num)] for i in range(node_num)]

#funkcja generujaca przepustowosc sieci
def generate_capacity(graph, N, m):
    for i in range(len(N)):
        max_size = max(N[i])
        for edge in graph.edges(i, data = True):
            edge[2]['capacity'] = max_size * len(N)**2 * m * uniform(2.0, 3.0)

#funkcja generujaca sciezke package pakietow z wierzcholka i do j
def generate_path(graph, i, j, package):
    try:
        path = nx.dijkstra_path(graph,i,j) #najpierw znajdujemy najkrotsza sciezke algorytmem dijksty
    except:
        return [] #jezeli nie istnieje to znaczy, ze graf sie rozspojnil
    if_ok = False
    gen = nx.all_simple_paths(graph, source = i, target = j) #generator wracajacy wszystkie sciezki z i do j
    while not if_ok:
        if_ok = True
        for k in range(0, len(path)-1):
            if graph[path[k]][path[k+1]]['taken'] + package > graph[path[k]][path[k+1]]['capacity']: #sprawdzamy czy pakiety 'zmieszcza sie' na wybranej trasie
                if_ok = False 
                try:
                    path = next(gen) #jezeli sie nie mieszcza to bierzemy kolejna trase
                except:
                    path = [] #jezeli wyczerpalismy wszystkie sciezki to znaczy, ze nie mozna przeslac pakietow z i do j
                break
    return path

#funkcja generujaca przeplyw, wraca true jezeli z kazdego wierzcholka mozna wszedzie wyslac okreslona w macierzy natezen liczbe pakietow, w p.p. false
def generate_flow(graph, N):
    for i in range(len(N)):
        for j in range(len(N)):
            if N[i][j] != 0:
                path = generate_path(graph, i, j, N[i][j]) #generowanie sciezki z wierzcholka i do j
                if len(path) == 0:
                    return False #jezeli nie udalo sie przeslac pakietow to wracamy false
                for k in range(0, len(path)-1):
                    graph[path[k]][path[k+1]]['taken'] += N[i][j] #zwiekszenie przeplywu na kazdej krawedzi na trasie o liczbe przesylanych pakietow
    return True

#funkcja rysujaca graf
def draw_graph(networkx_graph, output_filename='graph.html', show_buttons=False):
    pyvis_graph = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
    pyvis_graph.set_options("""
    var options = {
        "configure": {
            "enabled": false
        },
        "edges": {
            "color": {
                "inherit": true
            },
            "smooth": {
                "enabled": false,
                "type": "continuous"
            }
        },
        "interaction": {
            "dragNodes": true,
            "hideEdgesOnDrag": false,
            "hideNodesOnDrag": false
        },
        "physics": {
            "enabled": false,
            "stabilization": {
                "enabled": true,
                "fit": true,
                "iterations": 1000,
                "onlyDynamicEdges": false,
                "updateInterval": 50
            }
        }
    }""")
    for node, node_attrs in networkx_graph.nodes(data=True):
        pyvis_graph.add_node(node, **node_attrs)
    for source, target, edge_attrs in networkx_graph.edges(data=True):
        edge_attrs['label'] = edge_attrs['taken']
        edge_attrs['value'] = edge_attrs['taken']
        pyvis_graph.add_edge(source, target, **edge_attrs)
    if show_buttons:
        pyvis_graph.show_buttons()
    return pyvis_graph.show(output_filename)

#funkcja liczaca opoznienie pakietow wedlug wzoru z polecenia
def calculate_delay(graph, N, m):
    G = 0
    for row in N:
        for num in row:
            G += num
    sum_e = 0
    for i in range(len(N)):
        for edge in graph.edges(i, data = True):
            term = edge[2]['taken']/(edge[2]['capacity']/m-edge[2]['taken']) #liczenie wyrazenia dla kazdej krawedzi
            if term < 0: #jezeli wyszlo ujemne to znaczy, ze krawedz zostala przeciazona i nalezy wrocic fail
                return -1
            else:
                sum_e += term
    return 1/G * sum_e

#funkcja liczace miare niezawodnosci sieci
def calculate_reliability(graph, N, p, T_max, m):
    counter = 0
    for _ in range(1000):
        helper = graph.copy() #tworzenie kopii grafu wejsciowego, na ktorej bedzie prowadzona proba
        to_del = []
        for edge in graph.edges:
            i = uniform(0.0,1.0) #dla kazdej krawedzi losujemy czy zostatnie usunieta
            if i > p:
                to_del.append(edge)
        for edge in to_del:
            helper.remove_edge(*edge) #usuwamy wybrane krawedzi
        if_connected = generate_flow(helper, N) #generujemy na nowo przeplyw
        if if_connected: #jezeli nie doszlo do rozspojnienia to przeprowadzamy test
            T = calculate_delay(helper, N, m)
            if T < T_max and T > 0: 
                counter += 1
    return counter/1000

#funkcja generujaca dwa losowe wierzcholki do polaczenia
def add_edge():
    i = randint(0, 19)
    j = randint(0, 19)
    global edg
    while i == j or (i,j) in edg or (j,i) in edg: #losujemy dopoki nie otrzymamy dwoch roznych, niepolaczonych krawedzi
        i = randint(0, 19)
        j = randint(0, 19)
    return (i,j)

#funkcja liczaca srednia przepustowosc wszystich krawedzi grafu
def get_avg_cap(graph):
    cap = 0
    edg = 0
    for i in range(20):
        for edge in graph.edges(i, data = True):
            cap += edge[2]['capacity']
            edg += 1
    return cap/edg

#funkcja zwiekszajaca wartosci w macierzy natezen o inc
def increase_N(N, inc):
    for i in range(len(N)):
        for j in range(len(N[0])):
            N[i][j] += inc

def test_changing_N(p, T_max, m):
    graph = generate_nice_graph() #tworzenie grafu
    N = generate_N_matrix(20, 5) #tworzenie macierzy natezen o wartosciach <= 5
    generate_capacity(graph, N, m) #generowanie przepustowosci
    generate_flow(graph, N) #generowanie przeplywu
    out = []
    print('Testowanie niezawodnosci przy stopniowym zwiekszaniu wartosci w macierzy natezen')
    n = calculate_reliability(graph, N, p, T_max, m)
    print('Niezawodnosc poczatkowa: {}'.format(n))
    for i in range(10):
        print('\trozpoczecie testu dla wartosci zwiekszonych o {}'.format((i+1)*5))
        increase_N(N,5) #zwiekszenie wartosci o 5
        r = calculate_reliability(graph, N, p, T_max, m) #test
        out.append(r)
    i = 10
    with open('natezenia.txt', 'w') as f:
        f.write('p = {}, T_max = {}, m = {}, niezawodnosc poczatkowa {}\n'.format(p, T_max, m, n))
        for r in out:
            f.write('Maksymalna liczba wysylanych pakietow: {} Niezawodnosc: {}\n'.format(i, r))
            i += 5

#funkcja zwiekszajaca przepustowosci krawedzi
def increase_capacity(graph, mul):
    for i in range(20):
        for edge in graph.edges(i, data = True):
            edge[2]['capacity'] *= mul

def test_changing_capacity(p, T_max, m, mul):
    graph = generate_nice_graph() #tworzenie grafu
    N = generate_N_matrix(20, 50) #tworzenie macierzy natezen o wartosciach <= 50
    generate_capacity(graph, N, m//16) #generowanie przepustowosci
    generate_flow(graph, N) #generowanie przeplywu
    out = []
    print('Testowanie niezawodnosci przy stopniowym zwiekszaniu przepustowosci')
    n = calculate_reliability(graph, N, p, T_max, m)
    print('Niezawodnosc poczatkowa: {}'.format(n))
    for i in range(5):
        print('\trozpoczecie testu dla wartosci zwiekszonych {}-krotnie'.format(mul**(i+1)))
        increase_capacity(graph, mul) #zwiekszenie przepustowosci mul-krotnie
        r = calculate_reliability(graph, N, p, T_max, m) #test
        out.append(r)
    i = 1
    with open('przepustowosci.txt', 'w') as f:
        f.write('p = {}, T_max = {}, m = {}, niezawodnosc poczatkowa {}\n'.format(p, T_max, m, n))
        for r in out:
            f.write('Przepustowosci zwiekszone {}-krotnie Niezawodnosc: {}\n'.format(mul**i, r))
            i += 1

def test_adding_edges(p, T_max, m):
    graph = generate_nice_graph() #tworzenie grafu
    N = generate_N_matrix(20, 50) #tworzenie macierzy natezen o wartosciach <= 50
    generate_capacity(graph, N, m//16) #generowanie przepustowosci
    cap = get_avg_cap(graph) #obliczenie sredniej przepustowosci
    out = []
    print('Testowanie niezawodnosci przy dodawaniu krawedzi')
    n = calculate_reliability(graph, N, p, T_max, m)
    print('Niezawodnosc poczatkowa: {}'.format(n))
    for i in range(10):
        edg = add_edge()
        graph.add_edge(*edg, capacity = cap, taken = 0) #dodanie krawedzi
        print('\trozpoczecie testu po dodaniu krawedzi miedzy {} i {}'.format(*edg))
        r = calculate_reliability(graph, N, p, T_max, m) #test
        out.append(r)
    i = 1
    with open('krawedzie.txt', 'w') as f:
        f.write('p = {}, T_max = {}, m = {}, niezawodnosc poczatkowa {}\n'.format(p, T_max, m, n))
        for r in out:
            f.write('Liczba dodatkowych krawedzi {} Niezawodnosc: {}\n'.format(i, r))
            i += 1

def main():
    test_changing_N(0.8, 0.1, 128)
    test_changing_capacity(0.8, 0.1, 128, 1.0625)
    test_adding_edges(0.8, 0.1, 128)

if __name__ == "__main__":
    main()