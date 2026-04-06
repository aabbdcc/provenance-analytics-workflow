# Tracing AI-Assisted Analytics Workflows: A Provenance-Based Approach to Reproducibility

## 1. Introduction

Automated analytics workflows are increasingly used to produce reporting outputs such as dashboards, summaries, and performance indicators. In these workflows, final results are often generated through multiple intermediate steps including data ingestion, preprocessing, aggregation, comparison, and reporting.

Although automation improves efficiency, it also introduces a recurring difficulty: when a result changes between workflow runs, it can be hard to explain exactly why the change occurred. In practice, users may ask questions such as:

- Which dataset version produced this result?
- Which processing step contributed to the change?
- Which entities were most affected?
- Can the workflow result be reproduced and interpreted consistently?

This project explores these questions through a lightweight prototype focused on **traceability** and **reproducibility** in analytics workflows. The prototype is inspired by real reporting contexts in learning analytics and business reporting, where outputs need to remain interpretable across repeated runs.

---

## 2. Objective

The purpose of this prototype is to study how a simple provenance layer can support the interpretation of workflow outputs when input data changes across runs.

More specifically, the project aims to answer the following questions:

1. Which workflow elements should be recorded to make analytics outputs traceable?
2. How can structured provenance help compare workflow runs?
3. Can provenance improve the interpretation of changes in reporting outputs?

The goal is not to provide a complete provenance framework, but rather to build a small experimental setting in which these issues can be observed concretely.

---

## 3. Workflow Scenario

The workflow is based on a simulated learning reporting pipeline. Each row in the dataset represents a learner-course record with attributes such as:

- country
- department
- course name
- learning status
- progress
- time spent
- activity dates
- dataset version

Two dataset versions are generated:

- **Version 1**: baseline dataset
- **Version 2**: updated dataset with structured shifts

The second dataset is designed to simulate a performance decline affecting:

- **Germany** at country level
- **Sales Training West** at department level
- **Azure Basics** at course level

This setup creates a controlled scenario in which the same workflow is executed on two related inputs, making version comparison meaningful.

---

## 4. Workflow Design

![Workflow Overview](../figures/workflow_overview.png)

The workflow contains the following steps:

1. **Synthetic data generation**  
   Two versions of the dataset are created.

2. **Basic dataset inspection**  
   Initial descriptive checks are performed to verify that the intended shifts are visible.

3. **Aggregation**  
   Metrics are aggregated by country, department, and course.

4. **Comparison across versions**  
   Aggregated outputs from version 1 and version 2 are merged and compared.

5. **Provenance recording**  
   Workflow runs and main steps are recorded in structured JSON files.

6. **Summary generation**  
   A short text summary is produced from comparison outputs.

This workflow is intentionally simple, but it reflects the main logic of many real reporting pipelines.

---

## 5. Metrics

The aggregation step computes the following indicators:

- **learner_count**
- **completion_rate**
- **completion_gap_vs_overall**
- **active_learner_ratio**
- **avg_progress_pct**
- **avg_time_spent_hours**
- **missing_hours_ratio**

These metrics are calculated for each of the three reporting dimensions:

- country
- department
- course

This makes it possible to identify weak-performing entities and compare their changes across runs.

---

## 6. Provenance Design

![Provenance Structure](../figures/provenance_structure.png)

A lightweight provenance model is used in this prototype.

Each workflow run is represented by a JSON record with:

- `run_id`
- `timestamp`
- `workflow_name`
- `workflow_version`
- `dataset_version`
- `input_files`
- `steps`

Each step contains:

- `step_name`
- `step_type`
- `timestamp`
- `input_files`
- `output_files`
- `parameters`
- `row_count_in`
- `row_count_out`
- `observations`

This structure allows the workflow to preserve information not only about outputs, but also about how those outputs were produced.

In the aggregation workflow, provenance records capture:

- which dataset was used
- which grouping dimension was applied
- which files were produced
- which entity had the lowest completion rate

In the comparison workflow, provenance records capture:

- which aggregated files were compared
- which entities showed the strongest declines
- which comparison outputs were generated

---

## 7. Results

![Strongest Declines](../figures/strongest_declines.png)

The workflow comparison revealed a clear difference between the two dataset versions.

The strongest completion declines were:

- **Germany** at country level: **-21.35%**
- **Sales Training West** at department level: **-18.82%**
- **Azure Basics** at course level: **-12.53%**

These findings are consistent with the simulated shifts introduced in the second dataset version. This shows that the workflow is able to recover the intended changes through aggregation and comparison.

The generated text summary also reflects the same result pattern, making the workflow outputs easier to interpret.

---

## 8. Why Provenance Helps

Without provenance, a change in reported metrics may be visible, but difficult to explain in a structured way. Provenance improves the situation by linking output changes to:

- input dataset versions
- workflow steps
- aggregation parameters
- saved intermediate outputs
- explicit observations recorded during the run

In this prototype, provenance does not solve reproducibility in a formal sense, but it does support a more transparent understanding of workflow behavior across runs.

For example, instead of only observing that a completion rate changed, the workflow can also indicate:

- which comparison run produced the observation
- which files were used
- which dimension contained the strongest decline
- which entity was most affected

This makes the workflow easier to inspect and communicate.

---

## 9. Discussion

This prototype sits at the intersection of:

- analytics workflows
- reporting automation
- provenance tracking
- reproducibility analysis

Its main contribution is not algorithmic complexity, but rather **workflow interpretability**. It provides a concrete example of how a simple provenance layer can be added to an analytics pipeline so that changes across runs can be interpreted more systematically.

The project is also useful as a bridge between applied analytics experience and research questions in data management and AI. It shows how real reporting problems can motivate more general questions about workflow traceability and reproducibility.

---

## 10. Limitations

This project has several limitations.

First, the dataset is synthetic. Although the workflow is inspired by real reporting situations, the data itself is simulated.

Second, the provenance design is lightweight and JSON-based. It does not implement a formal provenance ontology or graph-based model.

Third, the workflow is intentionally simple. It does not include richer transformations, complex rule layers, or iterative re-execution scenarios.

Fourth, the summary generation step is template-based. It does not explore more advanced text generation or reasoning mechanisms.

These limitations are acceptable for a first prototype, but they also point to several useful extensions.

---

## 11. Future Work

Several extensions could improve this prototype:

1. **Graph-based provenance representation**  
   Replace the current JSON structure with a richer graph or PROV-inspired model.

2. **Richer reproducibility experiments**  
   Compare additional workflow runs, parameter settings, or dataset perturbations.

3. **More detailed evidence tracking**  
   Capture intermediate metrics, filtering logic, and step dependencies more explicitly.

4. **Cross-domain adaptation**  
   Apply the same workflow design to other reporting domains such as retail analytics or product performance monitoring.

5. **More advanced reporting outputs**  
   Add visual reports, markdown summaries, or structured explanation tables.

---

## 12. Conclusion

This project presents a lightweight prototype for studying provenance and reproducibility in analytics workflows. By generating two related dataset versions and processing them through a common workflow, the project creates a concrete setting in which result changes can be observed, compared, and partially explained.

The main finding is that even a simple provenance layer can make workflow outputs more transparent by linking results to specific steps, files, and recorded observations.

As a small research-oriented prototype, the project demonstrates how practical reporting workflows can be used to investigate broader questions about traceability and reproducibility in data-driven systems.