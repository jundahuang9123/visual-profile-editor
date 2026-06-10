# Stakeholder needs - construction dataspace onboarding (pilot excerpt)

Facility managers need to discover datasets by the construction asset type they
describe, for example pumps, air handling units, walls, or spaces, without
opening the underlying BIM or AAS files.

Data providers must publish a title, a description, and at least one keyword for
every dataset so that catalog search works across portals. Each dataset should
indicate its publisher organization.

Datasets exchanged in the dataspace should reference the AAS submodels they
represent, including the semantic IDs of the submodel, so that consumers can
interpret the payload without out-of-band agreements.

For BIM exchanges, every distribution must state the IFC schema version it
conforms to (for example IFC4 or IFC4X3) and the file format of the
distribution, so that consumers can check tool compatibility before download.

Access conditions are critical: each dataset must carry a license or access
rights statement, and restricted datasets should expose an access URL where the
access procedure is described.

Datasets should state the construction lifecycle phase the data was produced
in, such as design, construction, or operation, because reuse decisions depend
on it.

Where possible, provenance information about the source system (for example the
BIM authoring tool or the sensor gateway) should be included to support quality
assessment.
