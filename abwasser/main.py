#!/usr/bin/env python3
import enum
import math
import networkx as nx
import matplotlib.pyplot as plt

class Node:
    def __init__(self, name: str):
        self.name: str = name

    def du(self) -> float:
        raise NotImplementedError()

    def qtot(self) -> float:
        raise NotImplementedError()

    def max_source(self):
        raise NotImplementedError()

class Source(Node):
    def __init__(self, name, flow_rate):
        super().__init__(name)
        self.flow_rate = flow_rate

    def du(self) -> float:
        return self.flow_rate

    def qtot(self):
        return self.flow_rate

    def qww(self):
        return self.flow_rate

    def max_source(self):
        return self.flow_rate

class Junction(Node):
    def __init__(self, name: str):
        super().__init__(name)
        self.inflow = []

    def add_inflow(self, inflow: Node) -> None:
        self.inflow.append(inflow)

    def du(self) -> float:
        return sum([inflow.du() for inflow in self.inflow])

    def qww(self) -> float:
        return 0.5 * math.sqrt(self.du())

    def max_source(self):
        return max(inflow.max_source() for inflow in self.inflow) if self.inflow else 0

    def qtot(self):
        return max(self.qww(), self.max_source())

    # https://www.stadtentwaesserung-braunschweig.de/wp-content/uploads/sites/6/2022/03/Anlage1_Berechnung_Schmutzwasser.pdf
class Flows(enum.Enum):
    Waschtisch = 0.5
    Dusche_ohne_Stopfen = 0.6
    Dusche_mit_Stopfen = 0.8
    Kuechenspuele = 0.8
    Geschirrspueler = 0.8
    Waschmaschine = 1.5
    WC = 2.5



toilette_og = Source("Toilette OG", Flows.WC.value)
waschbecken_toilette_og = Source("Waschbecken Toilette OG", Flows.Waschtisch.value)
dusche_og = Source("Dusche OG", Flows.Dusche_ohne_Stopfen.value*2)
waschbecken_dusche_og = Source("Waschbecken Dusche OG", Flows.Waschtisch.value*2)
waschmaschine_og = Source("Waschmaschine OG", Flows.Waschmaschine.value)

kueche_og = Source("Kueche OG", Flows.Kuechenspuele.value)
geschirrspueler_1_og = Source("Geschirrspueler OG", Flows.Geschirrspueler.value)
geschirrspueler_2_og = Source("Geschirrspueler OG", Flows.Geschirrspueler.value)

toilette_eg = Source("Toilette EG", Flows.WC.value)
waschbecken_toilette_eg = Source("Waschbecken Toilette EG", Flows.Waschtisch.value)
dusche_eg = Source("Dusche EG", Flows.Dusche_ohne_Stopfen.value*2)
waschbecken_dusche_eg = Source("Waschbecken Dusche EG", Flows.Waschtisch.value*2)
waschmaschine_eg = Source("Waschmaschine EG", Flows.Waschmaschine.value)

schlafzimmer_eg = Source("Schlafzimmer EG", Flows.Waschtisch.value)

toilette_abwzeig_og = Junction("Toilette OG Abzweig")
toilette_abwzeig_og.add_inflow(toilette_og)
toilette_abwzeig_og.add_inflow(waschbecken_toilette_og)
dusche_abwzeig_og = Junction("Dusche OG Abzweig")
dusche_abwzeig_og.add_inflow(dusche_og)
dusche_abwzeig_og.add_inflow(toilette_abwzeig_og)
fallrohr_hwr_og = Junction("Fallrohr HWR OG")
fallrohr_hwr_og.add_inflow(dusche_abwzeig_og)
fallrohr_hwr_og.add_inflow(waschmaschine_og)

toilette_abwzeig_eg = Junction("Toilette EG Abzweig")
toilette_abwzeig_eg.add_inflow(toilette_eg)
toilette_abwzeig_eg.add_inflow(waschbecken_toilette_eg)
dusche_abwzeig_eg = Junction("Dusche EG Abzweig")
dusche_abwzeig_eg.add_inflow(dusche_eg)
dusche_abwzeig_eg.add_inflow(toilette_abwzeig_eg)
fallrohr_technik = Junction("Fallrohr Technik")
fallrohr_technik.add_inflow(dusche_abwzeig_eg)
fallrohr_technik.add_inflow(fallrohr_hwr_og)
grundleitung_technik = Junction("Grundleitung Technik")
grundleitung_technik.add_inflow(fallrohr_technik)

waschbecken_dusche_abzweig_og = Junction("Waschbecken Dusche Abzweig OG")
waschbecken_dusche_abzweig_og.add_inflow(waschbecken_dusche_og)
waschbecken_dusche_abzweig_eg = Junction("Waschbecken Dusche Abzweig EG")
waschbecken_dusche_abzweig_eg.add_inflow(waschbecken_dusche_abzweig_og)
waschbecken_dusche_abzweig_eg.add_inflow(waschbecken_dusche_eg)

grundleitung_dusche_waschbecken = Junction("Grundleitung Dusche Waschbecken")
grundleitung_dusche_waschbecken.add_inflow(waschbecken_dusche_abzweig_eg)
grundleitung_dusche_waschbecken.add_inflow(grundleitung_technik)

kueche_becken_abzweig_og = Junction("Kueche Becken Abzweig OG")
kueche_becken_abzweig_og.add_inflow(kueche_og)
kueche_becken_abzweig_og.add_inflow(geschirrspueler_1_og)

kueche_verzug_in_decke = Junction("Kueche Verzug in Decke")
kueche_verzug_in_decke.add_inflow(kueche_becken_abzweig_og)

kueche_abzweig_og = Junction("Kueche Abzweig OG")
kueche_abzweig_og.add_inflow(geschirrspueler_2_og)
kueche_abzweig_og.add_inflow(kueche_verzug_in_decke)

schlafzimmer_eg_abzweig = Junction("Schlafzimmer Abzweig EG")
schlafzimmer_eg_abzweig.add_inflow(schlafzimmer_eg)
schlafzimmer_eg_abzweig.add_inflow(kueche_abzweig_og)

grundleitung_schlafzimmer_eg = Junction("Grundleitung Schlafzimmer EG")
grundleitung_schlafzimmer_eg.add_inflow(schlafzimmer_eg_abzweig)
grundleitung_schlafzimmer_eg.add_inflow(grundleitung_dusche_waschbecken)

abwasserschacht = Junction("Abwasserschacht")
abwasserschacht.add_inflow(grundleitung_schlafzimmer_eg)

def print_recursive(node: Node):
    print(f"{node.name}; {node.du()}; {node.qww()}; {node.qtot()}")
    if isinstance(node, Junction):
        for inflow in node.inflow:
            print_recursive(inflow)

print("Name; du; Qww; Qtot")
print_recursive(abwasserschacht)

def draw_graph():
    node_queue = [abwasserschacht]
    edge_list = []
    node_labels = {}
    edge_labels = {}
    G = nx.DiGraph()
    while len(node_queue) > 0:
        node = node_queue.pop(0)
        G.add_node(node.name, org=node)
        node_labels[node.name] = node.name.replace(" ", "\n").replace("ue", "ü").replace("oe", "ö").replace("ae", "ä")
        if isinstance(node, Junction):
            for inflow in node.inflow:
                node_queue.append(inflow)
                edge_list.append((inflow, node))
    for src, dst in edge_list:
        G.add_edge(dst.name, src.name)
        edge_labels[(dst.name, src.name)] = f"{src.du()}:{src.qww():0.2f}:{src.qtot()}\n"
    layout = nx.bfs_layout(G, abwasserschacht.name)
    nx.draw_networkx_nodes(G, pos=layout)
    nx.draw_networkx_edges(G, pos=layout)
    nx.draw_networkx_labels(G, pos=layout, labels=node_labels)
    nx.draw_networkx_edge_labels(G, pos=layout, edge_labels=edge_labels)
    plt.show()

draw_graph()



