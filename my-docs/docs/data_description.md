# Data description

#TODO: @students, where these description come from; @me: check if all columns are really covered


---

***Table of content***

- [Reference](#reference)
- [Data files](#data-files)
  - [Name.tsv](#nametsv)
    - [Summary](#summary)
  - [NameRelation.tsv](#namerelationtsv)
    - [Summary](#summary-1)
  - [Reference.tsv](#referencetsv)
    - [Summary](#summary-2)
  - [Taxon.tsv](#taxontsv)
    - [Summary](#summary-3)
  - [TypeMaterial.tsv](#typematerialtsv)
  - [Summary](#summary-4)

---

## Reference

- [DOI](https://doi.org/10.15468/uhllmw)
- [Download page](https://hosted-datasets.gbif.org/datasets/ipni.zip)

## Data files

Following tsv file are prt of [zip](https://hosted-datasets.gbif.org/datasets/ipni.zip)

---

### Name.tsv

- `ID`: Unique identifier for each entry.
- `rank`: Taxonomic rank of the organism, such as spec. (species).
- `scientificName`: The scientific name of the species or taxon.
- `authorship`: The authorship citation for the scientific name, indicating the person(s) who described or revised the taxon. 
- `status`: The status of the taxonomic name, such as comb. nov. (new combination) or unknown
- `referenceID`: A reference identifier, likely pointing to a specific citation or publication. For example, 3929-2$v1(3)pLief10)802(1997) or 885-2$vv.401(1934).
- `publishedInYear`: The year the scientific name or taxonomic act was published
- `publishedInPage`: The page number in the publication where the taxonomic name or act is documented.
- `link`: A URL linking to additional information or the source entry, such as https://www.ipni.org/n/1000000-1.
- `remarks`: Additional remarks or notes about the entry, often a reference collation providing context or details about the publication. For example, Reference collation: 1(3: Lief. 10): 802 (1997).

#### Summary

The data appears to be curated to document and verify taxonomic nomenclature and publication history. It connects:
- `Taxonomy`: The naming and classification of species.
- `Historical Context`: Authorship and publication details providing historical insight into how the species name or status has evolved.
- `Accessibility`: Reference IDs and links facilitate verification and further research.
This type of data is useful for botanists, taxonomists, or researchers studying species classification and nomenclature evolution.

---

### NameRelation.tsv

- `nameID`: A unique identifier for a specific name in the database (e.g., a plant or organism name).
- `relatedNameID`: The unique identifier of another name to which the nameID is related.
- `type`: Describes the type of relationship between the nameID and the relatedNameID. Possible values include:
- `BASIONYM`: Indicates that the relatedNameID is the original name from which the current name (nameID) derives.
- `validationOf`: Suggests that the nameID validates or confirms the usage of the relatedNameID.
- `HOMOTYPIC`: Denotes that the names share the same type (e.g., based on the same specimen or description).
- `CONSERVED`: Implies that the name is conserved against another name.
- `LATER_HOMONYM`: The name is a later duplicate of the same name applied to a different entity.
- `SPELLING_CORRECTION`: Indicates a corrected spelling of the relatedNameID.
- `orthographicVariantOf`: Shows that the name is an orthographic variant (a spelling variation) of the relatedNameID.
- `SUPERFLUOUS`: Indicates that the name is unnecessary because a prior name already applies.
- `isonymOf`: Indicates that the nameID and relatedNameID are isonyms (same name independently published).
  
#### Summary

This data links a scientific name (`nameID`) to another name (`relatedNameID`) and defines the `type` of relationship between them. These relationships help clarify:
- Name Evolution: How a name has changed over time (e.g., basionym to a new combination).
- Typological Relationships: Whether names share the same type or are corrections of each other.
- Consistency in Nomenclature: How names are conserved, validated, or corrected to maintain taxonomic clarity.
The type column is key to understanding the nomenclatural and taxonomic history of a name, especially in managing synonyms, homonyms, and orthographic variants.

---

### Reference.tsv

- `ID`: A unique identifier for the reference, which may include additional qualifiers such as volume ($v) or issue.
- `doi`: The Digital Object Identifier, a unique alphanumeric string to provide a permanent link to the digital content of the reference (e.g., articles, books).
- `alternativeID`: An alternative identifier that might be used for the reference, possibly from a different indexing system.
- `citation`: The full bibliographic citation for the reference, often including title, authors, journal name, and publication details.
- `title`: The title of the referenced work (e.g., books, articles, conference papers).
- `author`: The author(s) or editor(s) of the referenced work.
- `issued`: The year or date of publication, which may include ranges or specific years.
- `volume`: The volume number of the publication if it is part of a series or journal.
- `issue`: The issue number within a volume, indicating further subdivision of the work.
- `page`: The page range or specific pages within the publication where the reference is located.
- `issn`: The International Standard Serial Number, identifying a serial publication like a journal.
- `isbn`: The International Standard Book Number, identifying books or monographs.
- `link`: A URL or web link to access the reference.
- `remarks`: Additional notes or remarks about the reference, such as where copies are stored or other context.

#### Summary

The `referncer.tsv` file links bibliographic details to unique identifiers. It provides metadata for publications referenced in other datasets (e.g., `Name.tsv` or `NameRelation.tsv`), enabling:

- Identification: Mapping references to specific works, whether books, articles, or conference papers.
- Validation: Verifying taxonomic names or nomenclatural decisions by linking them to authoritative sources.
- Accessibility: Offering links (e.g., via DOI or other URLs) or bibliographic details to retrieve the original work.
- Categorization: Enabling organization by title, author, date, or other publication metadata for easier referencing.
- This file acts as the backbone of a citation system for taxonomic data, ensuring credibility and transparency in `scientific documentation`.

---

### Taxon.tsv

- `ID`: A unique identifier for the taxon (a unit in the biological classification system, such as species or genus).
- `nameID`: The unique identifier linking the taxon to a specific scientific name, as listed in the- `Name.tsv` file.
- `provisional`: A boolean value (e.g., True) indicating whether the taxon is provisional, meaning it is tentative or not yet fully validated.
- `status`: The status of the taxon, which might indicate its acceptance (e.g., "valid," "accepted") or provide additional notes on its classification. In this dataset, the column has `NaN` values, implying no status is currently assigned.
- `family`: The biological family to which the taxon belongs (e.g., *Poaceae*, *Asteraceae*), a higher-level taxonomic rank grouping related genera.
- `link`: A URL or reference to more information about the taxon, such as an external database entry. In this dataset, the column has `NaN` values, suggesting links are not provided.

#### Summary

The `taxon.tsv` file forms a bridge between the nomenclature (handled in `Name.tsv` and `NameRelation.tsv`) and broader classification systems, ensuring that names are properly situated within their biological contexts.

---

### TypeMaterial.tsv

- `ID`: A unique identifier for the type material record. In this dataset, it contains `NaN`.
- `nameID`: Links the type material to a specific scientific name in the `Name.tsv` file.
- `citation`: Describes the type material, often including its designation and the institution where it is stored.
- `status`: Indicates the role or designation of each type specimen in the process of nomenclature and taxonomic identification. 
- `spirit`: Refers to a type specimen preserved in alcohol or spirit, typically for preservation of plant tissues (e.g., flowers, leaves).
- `epitype`: A specimen designated to clarify the application of a name, usually when the original type is not sufficient for identification or when it has deteriorated.
- `holotype`: The single, original specimen designated when a species or new taxon is first described. It serves as the reference point for the species' identification.
- `unknown`: Used when the status of the specimen is unclear or not recorded.
- `isoepitype`: A duplicate specimen of the epitype, stored in a different herbarium, to ensure availability of a clarifying specimen for the name.
- `neotype`: A specimen selected as the type when the original holotype or other type material is lost or cannot be located.
- `isolectotype`: A duplicate of a lectotype, stored in a different institution or herbarium, to ensure availability of a type specimen.
- `lectotype`: A specimen selected from the original material (when multiple specimens were cited in the original description) to act as the definitive type specimen for a name.
- `isotype`: A duplicate specimen of the holotype, typically stored in a different herbarium, which serves as an additional reference for the taxon.
- `isoneotype`: A duplicate of a neotype, used when multiple copies of a neotype are made to ensure broad availability for reference.
- `null`: Indicates that no status has been assigned to the specimen, or it is not applicable.
- `institutionCode`: A short code identifying the institution housing the type material (e.g., "BM" for the Natural History Museum).
- `catalogNumber`: A unique catalog number assigned to the type material by the institution.
- `collector`: The individual(s) who collected the type material, often listed by last name (e.g., "Ludlow; Sherriff; Elliot").
- `date`: The date the type material was collected, often formatted as YYYY-MM-DD.
- `locality`: The location where the type material was collected, ranging from broad regions to specific sites.
- `latitude`: The geographic latitude of the collection site (if recorded).
- `longitude`: The geographic longitude of the collection site (if recorded).
- `remarks`: Additional notes or remarks about the type material.

### Summary

The `typematerial.tsv` file documents type specimens linked to specific plant names, providing key details about each specimen's role in taxonomic validation. It includes information such as the *type designation* (e.g., holotype, isotype), the *institution* where the specimen is stored, *collector* details, and *collection location*. This file helps track the origin and authenticity of plant species names, ensuring clarity in plant taxonomy by associating physical specimens with scientific nomenclature.
