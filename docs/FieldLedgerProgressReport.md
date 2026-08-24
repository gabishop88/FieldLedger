# FieldLedger Progress Report

## At a Glance

FieldLedger has progressed from exploratory database conceptualizing into a working research-oriented farm data platform. It has a spatial relational database model, a containerized architecture, initial John Deere integration UI, data validation, and provenance mechanisms.

The project is past the initial design and exploration phase and into prototype implementation and evaluation. The remaining work is increasingly focused on validating the design and making it robust enough to demonstrate its intended use cases using representative South Farms data.

> Progress Percentages are based on milestones completed, not hours spent.

## Progress Categories

Categories are designed as project requirements rather than the technologies or data sources needed to meet those requirements.

| Category | Status | Description |
| --- | --- | --- |
| 1. Foundational database model | ~79% | Multiple schema iterations completed, with the current schema substantially established. PostGIS is integrated into the core design as part of the structural hierarchy of data. Alembic migrations, database backups, role separation, and audit/change logging are established. The model is still expected to change as it is tested against more data and evaluated. |
| 2. Data ingestion and normalization | ~46% | John Deere APIs have been extensively explored and models and transformation logic are in place for the main data types. Representative data has been ingested for development. Reconciliation, incomplete records, and additional data sources remain. |
| 3. Data quality and validation | ~46% | Validation is a core design principle. Rules are established and easily extensible to check or transform incoming and outgoing data at the API layer. Identification of common data-quality issues, with issues raised to the user. Auditability included in the design. |
| 4. Synchronization architecture | ~61% | Containerized asynchronous job queue with Arq+Redis. Basic synchronization protocol in place with external-record links. Needs work on products, equipment, and connecting them to operations, often by correcting poor data validation on John Deere's side. Needs webhook support to maintain up-to-date records since eTags are soon to be deprecated by John Deere. Sync interface under development. |
| 5. User interface and workflows. | ~40% | A development dashboard supports authentication, John Deere authorization, synchronization, navigation, boundary visualization, operation display, and logs. The stakeholder workflows are largely in progress and will require evaluation. |
| 6. South Farm Data Preparation | ~62% | Historical sources, John Deere records, stakeholder understanding, and improved boundaries have all been considered and used during development. A representative dataset is being compiled, but comprehensive integration and validation remain. |
| 7. Documentation and Thesis Work | ~47% | Extensive notes, setup documentation, code documentation, basic unit tests, and initial thesis materials exist. Formal evaluation, integration testing, additional documentation, and the thesis writing remain. |

## Full Checklist

These checklists inform the percentages above.

### 1. Foundational Database Model

Progress: ████████░░ 11/14: 79%

* [x] Explore relation database technologies and industry standards for languages, tools, and platforms.
* [x] Develop an initial schema based on Killian's data.
* [x] Iterate on schema using John Deere data and stakeholder requirements.
* [x] Establish the current Organization/Farm/Field/Boundary hierarchy.
* [x] Start the current FieldLedger iteration as a docker-compose container stack.
* [x] Establish Alembic migrations and a repeatable migration workflow.
* [x] Incorporate admin, audit, read/write, and readonly database roles.
* [x] Implement core field, boundary, product, equipment, and operation models.
* [x] Implement database table auditing via changelog and triggers.
* [x] Integrate geometry, including eWKT representation, into the data model using geoalchemy2, shapely, and PostGIS.
* [x] Establish database backups and a restoration procedure.
* [ ] Finalize the database model after testing with South Farm data and stakeholder evaluations.
* [ ] Validate the model against South Farm historical data after John Deere data is handled.
* [ ] Establish access control through RLS (Row-level Security) for security and broader multi-organization use.

### 2. Data Integration and Normalization

Progress: █████░░░░░ 6/13: 46%

* [x] Investigate John Deere APIs and data structures.
* [x] Build tools for accessing and visualizing John Deere data.
* [x] Build models to store data from Operations Center APIs
* [x] Establish basic validation rules for Op Center ingestion
* [x] Create models to transform data from Op Center to be compatible with FieldLedger.
* [x] Ingest a test subset of more than 500ac worth of data from John Deere to use for testing and validation.
* [ ] Complete product and equipment reconciliation with operation records.
* [ ] Finalize procedures to address missing, duplicate, and inconsistent records.
* [ ] Establish repeatable ingestion procedures for additional data sources.
* [ ] Demonstrate ingestion at the scale needed for the complete South Farms dataset.
* [ ] Incorporate a test set of data from non-John-Deere sources.
* [ ] Establish consistent unit/measurement normalization across all records.
* [ ] Demonstrate a repeatable system for ingestion from multiple sources connecting to the same fields/boundaries seamlessly.

### 3. Data Quality and Validation

Progress: ████░░░░░░ 6/13: 46%

* [x] Use SQLModel/pydantic models to enforce validation at both data input and output boundaries.
* [x] Identify common inconsistencies and validation issues with the data from Op Center.
* [x] Add audit logging for data changes
* [x] Track provenance of externally synchronized records.
* [x] Establish extensible data validation architecture.
* [x] Begin handling malformed and inconsistent records from Op Center on test data.
* [ ] Finalize data validation rules for Operations Center data.
* [ ] Use stakeholder interviews to separate automatic from manual validation requirements.
* [ ] Create explicit flags/warnings to inform user of manual validation needs.
* [ ] Build user workflows around validating data, and prioritizing validated data.
* [ ] Comprehensively test validation behavior.
* [ ] Demonstrate a measurable improvement in data completeness and accuracy.
* [ ] Document how quality issues and corrections are preserved in change records.

### 4. Synchronization Architecture

Progress: ██████░░░░ 11/18: 61%

* [x] Establish John Deere connection/authorization procedure
* [x] Test eTag workflow for maintaining up-to-date data (soon to be deprecated).
* [x] Establish tables for external record linking
* [x] Add sync states and define transition logic.
* [x] Create Redis-based asynchronous job queue tied to the API lifespan.
* [x] Register functions to perform sync-related jobs with Arq worker and give access to queue.
* [x] Create endpoints to request jobs on the Redis queue.
* [x] Add sync worker job logs and progress reporting. Bonus webhook to monitor them.
* [x] Build the initial Sync UI to manage synchronization.
* [x] Test the initial workflow to sync orgs, farms, fields, boundaries, and operations with the test data.
* [x] Remove eTag-based synchronization in preparation for webhook support.
* [ ] Complete webhook-based update process.
* [ ] Improve concurrent job handling.
* [ ] Implement recovery/reconciliation for errors or incomplete synchronization.
* [ ] Complete sync process for Products and Equipment (and Operations by extension).
* [ ] Perform basic tests of sync process and UI
* [ ] Demonstrate synchronization with evaluations from stakeholders.
* [ ] Demonstrate repeated synchronization and incorporation of additional data without breaking or duplicating data.

### 5. User Interface and Workflows

Progress: ████░░░░░░ 4/10: 40%

* [x] Establish a React/Typescript frontend.
* [x] Create and test an authentication workflow that works with tokens and cookies.
* [x] Establish the John Deere synchronization workflow and UX via a tree and details panel.
* [x] Build basic field/boundary visualization and operation details view.
* [ ] Create a general data curation workflow built into the sync process.
* [ ] Create summary and management workflows for administrator stakeholders.
* [ ] Create data, templates, and query focused workflows for researcher stakeholders.
* [ ] Include data ingestion (outside of Op Center data) and review workflows for farm manager stakeholders.
* [ ] Conduct formal stakeholder prototype evaluations.
* [ ] Incorporate stakeholder findings into UI/UX.

### 6. South Farm Data Preparation

Progress: ██████░░░░ 8/13: 62%

* [x] Obtain and examine Killian's management data.
* [x] Investigate historical data in various formats in the South Farms Box folder.
* [x] Incorporate stakeholder recommendations into decisions on data sources and importance.
* [x] Investigate John Deere Operations Center data and formatting.
* [x] Collect improved field boundaries and incorporate into FieldLedger.
* [x] Organize, name, and present field boundaries to farm managers.
* [x] Add a representative set of test data from the South Farms into FieldLedger for testing.
* [x] Reconcile incoming data with existing records (such as from manual field boundaries).
* [ ] Validate integrated data against source.
* [ ] Digitalize and format various historical data sources against data templates for use in FieldLedger.
* [ ] Demonstrate integration of field-scale and plot-scale operation records.
* [ ] Demonstrate at least one research-oriented use of the data.
* [ ] Establish processes for adding and cleaning South Farms data.

> The actual ingestion of most of that historical data is outside of the scope of this project.

### 7. Documentation and Thesis Work

Progress: █████░░░░░ 7/15: 47%

* [x] Maintain Extensive Implementation Notes.
* [x] Track changes using a Github Repo and document usage of outside sources and tools.
* [x] Include basic inline and docstring-style code documentation as I go.
* [x] Establish simple automated unit testing for core functionalities.
* [x] Conduct stakeholder interviews to inform the design process.
* [x] Present slides and poster to various stakeholders.
* [x] Demonstrate sample visualizations and data outputs using test dataset.
* [ ] Present thesis proposal.
* [ ] Consolidate and finalize usage and code documentation.
* [ ] Expand tests to cover most backend functionality.
* [ ] Establish a public and reproducible prototype demonstration procedure.
* [ ] Conduct formal prototype evaluation with stakeholders.
* [ ] Formalize evaluation criteria for quantitative progress metrics.
* [ ] Document project limitations, scope, and future deployment, development, and maintenance requirements.
* [ ] Complete and defend thesis manuscript.
