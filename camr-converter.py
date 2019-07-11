import argparse
from rdflib.namespace import RDF
from rdflib import URIRef, Namespace, Graph, Literal

def cleanNodeValue(value):
    return value.rstrip().split("-")[0]

def ontoToLabel(fileIn):
    base = Namespace("https://github.com/tetherless-world/TWC-NHANES/AMR/")
    doco = Namespace("http://purl.org/spar/doco/")
    prov = Namespace("http://www.w3.org/ns/prov#")

    g = Graph()
    g.bind('prov', prov)
    g.bind('doco', doco)
    g.bind('amr', base)

    entity = ""
    stack = []
    with fileIn as f:
        for line in f:
            # parse id
            if "# ::id " in line:
                id = line.split("# ::id ")[1].rstrip()
                entity = "Sentence/" + id + "/"
                g.add( (base[entity], RDF.type, doco.Sentence) )

                # reset stack
                uniqueID = 0
                stack = []
                stack.append(base[entity])

            else: # not id
                # parse sentence
                if "# ::snt " in line:
                    snt = line.split("# ::snt ")[1].rstrip()
                    g.add( (stack[-1], prov.value, Literal(snt)) )

                else: # not sentence
                    # parse root node
                    if line[0] == "(":
                        node = line[1:].split(" / ")[0]
                        node_value = cleanNodeValue(line[1:].split(" / ")[1])

                        nodeIRI = base[entity + "AMRNode/" + node + "/"]
                        g.add( (nodeIRI, RDF.type, base.AMRNode) )
                        g.add( (stack[-1], base.hasRootNode, nodeIRI) )
                        g.add( (nodeIRI, prov.value, Literal(node_value)) )

                        stack.append(nodeIRI)
                        # print(node + ": " + node_value)

                    else: # not root node
                        # parse node
                        if line[0] == "\t":
                            noDepth = line.lstrip("\t")
                            currentDepth = len(line) - len(noDepth)

                            parse = noDepth.split(" (")
                            if len(parse) == 1: # 2 value line
                                edge = parse[0].split(" ")[0][1:]
                                node = edge + "Node" + str(uniqueID)
                                value = parse[0].split(" ")[1].rstrip("\n)")
                                uniqueID = uniqueID + 1
                            else:
                                if len(parse) == 2: # 3 value line
                                    edge = parse[0][1:]
                                    node = parse[1].split(" / ")[0]
                                    value = parse[1].split(" / ")[1].rstrip("\n)")
                                else: # Unknown Case
                                    print("Unkown Case = " + line)

                            # check if this node is a child, if its not get rid of unneeded state
                            while (currentDepth <= (len(stack)-2)):
                                stack.pop()

                            nodeIRI = base[entity + "AMRNode/" + node + "/"]
                            g.add( (nodeIRI, RDF.type, base.AMRNode) )
                            g.add( (stack[-1], base[edge], nodeIRI) )
                            g.add( (nodeIRI, prov.value, Literal(value)) )
                            stack.append(nodeIRI)

                        else: # not a node
                            if not (line.rstrip() == ""): # your not empty lines so what are you?
                                print("vvvvvvBADvvvvvvv")
                                print(line)
                                print("^^^^^^BAD^^^^^^^")
    g.serialize(destination=str(fileIn.name) + ".rdf", format="pretty-xml")

parser = argparse.ArgumentParser(description='Convert C-AMR Parsed text files into RDF')
parser.add_argument("file_path", metavar='camrFile', type=argparse.FileType('r'))
args = parser.parse_args()

print('Attempting to parse ' + str(args.file_path.name))
ontoToLabel(args.file_path)
print('Finished parsing!')
