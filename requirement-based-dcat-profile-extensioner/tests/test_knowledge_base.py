"""Base profile registry and vocabulary index."""
from rdflib import Graph

from profile_extensioner.contracts import Term
from profile_extensioner.knowledge import list_base_profiles, load_base_profile, load_knowledge_base
from profile_extensioner.knowledge.vocab_index import VocabularyIndex, terms_from_graph, tokenize

DCAT = "http://www.w3.org/ns/dcat#"
DCT = "http://purl.org/dc/terms/"
FOAF = "http://xmlns.com/foaf/0.1/"


def test_official_base_profiles_are_listed():
    ids = {info.id for info in list_base_profiles()}
    assert {"dcat-ap-3.0.1", "dcat-ap-3.0.0"} <= ids


def test_base_profile_reads_official_constraints_and_spec_obligations():
    base = load_base_profile("dcat-ap-3.0.1")
    assert base.info.class_count == 33 and base.info.element_count == 131
    title = base.element(DCAT + "Dataset", DCT + "title")
    assert title.facets.obligation == "mandatory" and title.facets.min_count == 1
    publisher = base.element(DCAT + "Dataset", DCT + "publisher")
    assert publisher.facets.obligation == "recommended"       # from the specification text
    assert publisher.facets.max_count == 1 and publisher.facets.range_class == FOAF + "Agent"
    assert base.element(DCAT + "Catalog", DCT + "publisher").facets.obligation == "mandatory"
    assert base.element(DCAT + "Distribution", DCAT + "byteSize").facets.obligation == "optional"
    assert base.element(DCAT + "Dataset", DCT + "bibliographicCitation") is None
    assert [cls.iri for cls in base.classes()][:2] == [DCAT + "Catalog", DCAT + "Dataset"]
    assert base.class_label(DCAT + "Catalog") == "Catalogue"


def test_plain_word_subjects_map_to_classes():
    base = load_base_profile("dcat-ap-3.0.1")
    assert base.class_for_subject("dataset") == DCAT + "Dataset"
    assert base.class_for_subject("Distributions") == DCAT + "Distribution"
    assert base.class_for_subject("catalogue") == DCAT + "Catalog"
    assert base.class_for_subject("data service") == DCAT + "DataService"
    assert base.class_for_subject("portal") is None


def test_knowledge_base_expands_curies_and_mint_markers():
    kb = load_knowledge_base("dcat-ap-3.0.1", profile_namespace="https://example.org/lab#", profile_prefix="lab")
    assert kb.expand("dct:title") == DCT + "title" and kb.expand("dcterms:title") == DCT + "title"
    assert kb.expand("NEW:specimenMaterial") == "https://example.org/lab#specimenMaterial"
    assert kb.expand("NEW:not a name") is None and kb.expand("nope:thing") is None
    assert kb.curie("https://example.org/lab#specimenMaterial") == "lab:specimenMaterial"
    assert kb.is_minted("https://example.org/lab#x") and not kb.is_minted(DCT + "title")
    # every term the base uses is retrievable, in the base's own words
    assert kb.term(DCT + "spatial") is not None
    assert kb.term(DCAT + "Dataset").kind == "class"


def test_namespace_exclusion_hides_terms_from_the_index():
    kb = load_knowledge_base("dcat-ap-3.0.1", profile_namespace="https://example.org/x#", profile_prefix="x",
                             exclude_namespaces=("http://data.europa.eu/r5r/",))
    assert kb.term("http://data.europa.eu/r5r/applicableLegislation") is None
    assert kb.term(DCT + "title") is not None


VOCAB = """
@prefix ex: <http://example.org/v#> . @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> . @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
ex:Agent a rdfs:Class ; rdfs:label "Agent"@en .
ex:Organisation a owl:Class ; rdfs:subClassOf ex:Agent ; rdfs:label "Organisation"@en .
ex:Laboratory a owl:Class ; rdfs:subClassOf ex:Organisation ; rdfs:label "Laboratory"@en .
ex:bibliographicCitation a rdf:Property ; rdfs:label "Bibliographic Citation"@en ;
    rdfs:comment "A bibliographic reference for the resource."@en ; rdfs:range rdfs:Literal .
ex:contributor a owl:ObjectProperty ; rdfs:label "Contributor"@en ;
    rdfs:comment "An entity responsible for making contributions to the resource."@en ; rdfs:range ex:Agent .
ex:oldThing a rdf:Property ; rdfs:label "Contributor (old)"@en ; owl:deprecated true .
<http://elsewhere.org/foreign> a rdf:Property ; rdfs:label "Foreign"@en .
"""


def vocab_index() -> VocabularyIndex:
    graph = Graph().parse(data=VOCAB, format="turtle")
    return VocabularyIndex(terms_from_graph(graph, "http://example.org/v#", "ex"))


def test_terms_are_read_from_a_vocabulary_graph():
    index = vocab_index()
    assert len(index) == 6                                   # the foreign term is not part of this vocabulary
    contributor = index.get("http://example.org/v#contributor")
    assert contributor.kind == "property" and contributor.property_type == "object"
    assert contributor.range == ["http://example.org/v#Agent"]
    assert index.get("http://example.org/v#oldThing").deprecated is True
    info = index.vocabularies()[0]
    assert (info.prefix, info.class_count, info.property_count) == ("ex", 3, 3)


def test_search_ranks_by_label_and_definition():
    index = vocab_index()
    hits = index.search("people who contributed to carrying out the tests", kind="property")
    assert hits[0].term.iri == "http://example.org/v#contributor"     # stems match; the deprecated one ranks lower
    assert index.search("cite a dataset in a publication")[0].term.iri.endswith("bibliographicCitation")
    assert index.search("zzz unknown words") == []
    assert [hit.term.kind for hit in index.search("organisation", kind="class")] == ["class"]


def test_subclass_closure_is_reflexive_and_transitive():
    index = vocab_index()
    lab, org, agent = (f"http://example.org/v#{name}" for name in ("Laboratory", "Organisation", "Agent"))
    assert index.is_subclass_of(lab, agent) and index.is_subclass_of(org, agent) and index.is_subclass_of(lab, lab)
    assert not index.is_subclass_of(agent, lab)


def test_tokenize_stems_and_drops_stopwords():
    # related forms meet on one stem; stopwords and modal verbs are dropped
    assert tokenize("Each distribution must state the licence of its files") == tokenize("distributions licenses file")
    assert tokenize("cite") == tokenize("citation") == tokenize("citations")
    assert tokenize("contributed") == tokenize("contributor") == tokenize("contributions")
    assert tokenize("identifies") == tokenize("identify")
    assert tokenize("catalogue") == tokenize("catalog") and tokenize("organisation") == tokenize("organizations")
    assert tokenize("access") != tokenize("acces") and tokenize("status") == ["status"]
    assert set(tokenize("bibliographicCitation")) == set(tokenize("bibliographic citation"))
