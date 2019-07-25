from rdflib import Graph

g = Graph()
g.parse("rml.owl", format="turtle")

qres = g.query(
    """
    SELECT DISTINCT ?class ?propuri
       WHERE {
          ?aname rr:subjectMap ?smap.
          ?smap rr:class  ?class .
          OPTIONAL {?aname rr:predicateObjectMap ?predicateObjectMap .
          ?predicateObjectMap rr:predicate ?propuri . 
          }
       }""")
clases = {}
for row in qres:
    if row[0].value not in clases:
        clases[row[0].value] = []
    if row[1]:
        clases[row[0].value].append(row[1].value)

clases