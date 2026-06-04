"""
nodes
Created on Apr 18, 2016

@author: jpetrie

@description: Nodes is the definition and container for Known Tesla (and vendor) UDS Nodes.
    Importing this file should be all you need.  The package is designed to take it from there.
    If you need to recreate or modify the master JSON, use the functions defined here.

    UDS.Nodes.NONE
    UDS.Nodes.search["NONE"]
"""

__author__ = "jpetrie"

import os
import json

from node import Node

# If you're not first, you're last.
NONE = Node()

MASTER_JSON = os.path.join(os.path.dirname(__file__), "nodes.json")


def load_json_nodes(filename):
    """
    Load JSON Nodes takes saved node data from json and loads them into python Node members
    :param filename: <string> the full path to the filename of the node json.
    :return nodes: <dict of Nodes> a list of all of the loaded nodes.
    """
    nodes = {}

    with open(filename, "r") as nodeFile:
        nodeDict = json.load(nodeFile)

    for node in nodeDict:
        try:
            newNode = Node().deserialize(nodeDict[node], node)  # Hope this passes the test.
        except AssertionError as e:
            print "Invalid Node: {0}: {1}.".format(node, e.message)
            continue

        nodes[newNode.name] = newNode

    return nodes


def save_json_nodes(nodes, filename):
    """
    Save JSON Nodes saves the given list of nodes as JSON for later use.
    :param nodes: <list of Nodes> a list of UDS Nodes.
    :param filename: <string> the full path to the filename of the node json.
    """
    nodeDict = {node.serialize() for node in nodes}
    with open(filename, "w") as nodeFile:
        json.dump(nodeDict, nodeFile, indent=4)  # Make it pretty

# This is probably what you came here for.
search = load_json_nodes(MASTER_JSON)
globoD = globals()
globoD.update(search)

node_id_dict = {}
for node in search.values():
    node_id_dict[int(node.nodeID)] = node

del os, json

if __name__ == "__main__":
    print __doc__
