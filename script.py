import ontospy
from jinja2 import Template

val = input("Enter URL file: ")
val_output = input("Enter URL output file: ")
id_service = input("Enter id_service: ")

if id_service == "":
    id_service = "example-sparql"

if val_output == "":
    val_output = "example.graphql"

if val == "":
    val = "esquema2.owl"
model = ontospy.Ontospy(val, verbose=True)


class OntClass:
    def __init__(self, uri, id, name, parents):
        self.uri = uri
        self.id = id
        self.name = name
        self.properties = []
        self.parents = parents
        self.hijos = []

    def get_formated_name(self):
        return self.name.replace("-", "_")

    def add_property(self, property):
        self.properties.append(property)
        if len(self.hijos) > 0:
            for hijo in self.hijos:
                list_all_class[hijo].add_property(property)


    def get_class_string(self):
        t = Template(
            """
            type {{name}} @service(id:"{{id}}") { 
                {% for n in properties %} {{n}}
                {% endfor %}
            }
            """)
        properties_list_string = []
        for prop in self.properties:
            properties_list_string.append(prop.get_as_string())
        return t.render(id=self.id, name=self.get_formated_name(), properties=properties_list_string)


class OntProperty:
    def __init__(self, uri, id, name, type):
        self.obligatorio = None
        self.uri = uri
        self.id = id
        self.name = name
        self.type = type
        self.typesConvert = {
            "Literal": "String",
            "integer": "Int",
            "int": "Int",
            "boolean": "Boolean",
        }
    def get_formated_name(self):
        return self.name.replace("-", "_")

    def transform_type(self):
        if self.type in self.typesConvert:
            return self.typesConvert[self.type]
        return self.type

    def get_as_string(self):
        t = Template("""{{name}}: {{type}}{{obligatorio}} @service(id:"{{id}}")""")
        mandatory = ""
        if self.obligatorio:
            mandatory = "!"
        return t.render(id=self.id, type=self.transform_type(), name=self.get_formated_name(), obligatorio=mandatory)


list_all_class = {}
list_all_properties = []

t = Template(
    """
    type __Context {
        {% for cont in contextos %} {{cont.name}}: _@href(iri: "{{cont.uri}}")
        {% endfor %}
    }
    {% for class_i in clases %} {{class_i}}
        {% endfor %}
    """)
clases = model.all_classes
ontoproperties = model.all_properties

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
clases_rml = {}
for row in qres:
    if row[0].value not in clases_rml:
        clase = row[0].value.replace("<","").replace(">","")
        clases_rml[clase] = []
    if row[1]:
        clases_rml[clase].append(row[1].value)

list_keys = list(clases_rml.keys())
for clases_i in clases:
    '''se crean las instacias de clases'''
    #Si no estna en las clases de rml entonces no la proceso
    if clases_i.uri not  in list_keys:
        continue
    padres = clases_i._parents
    lista_padres = []
    lista_hijos = []
    for padre in padres:
        lista_padres.append(padre.uri)
        if padre.uri in list_all_class:
            if not clases_i.uri in list_all_class[padre.uri].hijos:
                list_all_class[padre.uri].hijos.append(clases_i.uri)
        else:
            classpobj = OntClass(padre.uri, id_service, padre.locale, [])
            classpobj.hijos.append(clases_i.uri)
            list_all_class[padre.uri] = classpobj
    if clases_i.uri in list_all_class:
        classobj = list_all_class[clases_i.uri]
        classobj.parents = lista_padres
    else:
        classobj = OntClass(clases_i.uri, id_service, clases_i.locale, lista_padres)
        list_all_class[clases_i.uri] = classobj
for property_i in ontoproperties:

    if len(property_i.domains) != 0:
        for domain in property_i.domains:
            if domain.uri in list_all_class:
                if property_i.uri not in clases_rml[domain.uri]:
                    continue
                ranges = property_i.ranges
                if len(ranges) == 0:
                    # Si no tienen al menos un rango no agrego
                    continue
                range = ranges[0]
                prop_name = range.locale
                property_object = OntProperty(property_i.uri, id_service, property_i.locale, prop_name)
                # print("Dominios", dir(property_i))
                # print("Rangos", property_i.ranges)
                list_all_class[domain.uri].add_property(property_object)

contextos = []
list_all_class_string = []
for clase_i in list_all_class.items():
    contextos.append({"name": clase_i[1].get_formated_name(), "uri": clase_i[1].uri})
    for property_i in clase_i[1].properties:
        contextos.append({"name": property_i.get_formated_name(), "uri": property_i.uri})
    list_all_class_string.append(clase_i[1].get_class_string())

#TOdo poner el nombre de archivo como input de la consola
f = open(val_output, "w")
f.write(t.render(contextos=contextos, clases=list_all_class_string))
f.close()
print("Generated Class: {}".format(len(list_all_class_string)))
