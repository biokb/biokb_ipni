# **Database Structure**

This project uses **MySQL** to store IPNI taxonomic data. The database consists of five main tables.

## **Tables Overview**
| Table Name        | Description |
|------------------ |-------------|
| name_relation     | records the relationships between names and their corresponding taxonomic ranks. |
| names             | Information on accepted taxon names |
| reference         | Stores publication references for taxonomic records |
| taxon             | Stores taxonomic details (name, provisional, family)  |
| type_material     | Records geographic distribution of taxa |