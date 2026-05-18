# Relationship to General-Ontology-Editor

`General-Ontology-Editor` is the reusable editor foundation. It provides generic visual editing for LinkML/RDF/SHACL-style semantic schemas and lightweight ontologies.

`ConstructDCAT-with-LinkML` is a specialized downstream application. It uses the generic editor foundation but configures it for Construct-DCAT application profile engineering.

The specialized repository adds:

- DCAT/DCAT-AP templates;
- Construct-DCAT starter profile;
- construction-domain semantic-anchor properties;
- profile-specific validation rules;
- profile package export;
- domain-specific documentation and examples;
- UI terminology focused on application profiles rather than generic ontology editing.

The intention is to keep generic editor capabilities reusable while allowing Construct-DCAT to evolve as a domain-specific research prototype.
