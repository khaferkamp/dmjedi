# ROADMAP for DMJEDI

This is the roadmap for Data Modeling Jedi.
We really appreciate your [contribution](CONTRIBUTING.md) help in every form.

Feel free to get in touch with us or file PRs to submit your work.

## Versions

### 0.0.1

* Modelling of stage tables (relational)
* Modelling of the basic DV2 entities (hub, link, satellite)
* Modelling of Dimension and Fact
* Pytest Usage

### 0.0.2

* Reading metadata from external source (e.g. Excel)
* Visualize Model (Dot?)
* Template Generation
  * for PostgresSQL
  * for Talend
* Code Generation out of the DV2 model
  * for Python scripts
  * integration in Dagster/Bonobo/Airflow DAGs

### 0.0.3

* Choice for Sequence Keys or Hash Keys
* Choice for Insert Only or LEDTS

### unordered

* CDC
* ELT
* Model Validation
* Documentation Generation
* Lineage
* Realtime integration
  * Spark?
  * MQs, like Kafka/Pulsar?
* Icons
* VS Code Extension
* Jupyter Notebook Integration
* GPDR Encryption in data/tables/etc
