# Algorithm Design

## Overview

The MPI (Master Patient Index) system uses a multi-pass record linkage algorithm to identify whether incoming patient records belong to existing person clusters in the database. The algorithm employs **blocking keys** to efficiently reduce the search space, then uses **fuzzy matching** with **log-odds scoring** to evaluate potential matches across multiple evaluation passes.

## Core Components

### Blocking Strategy
The algorithm uses **blocking keys** to dramatically reduce the number of comparisons needed. Rather than comparing every incoming record against every existing record, blocking groups records that share certain simplified characteristics. Some example blocking keys include birthdate, zipcode, and first 4 characters of first name (for a full list of blocking keys see [Algorithm Configuration](/algo-configuration.md#blocking-key-types)).

The algorithm uses a subset of these keys from the incoming record to quickly find potential matches against existing patients in the MPI, matching on their blocking values and including any patient records in the Person clusters of those blocked records.

### Record Evaluation with Log-Odds Scoring
The algorithm compares the incoming patient record against patient records that share the same blocking values, as well as patient records in the Person clusters of those that share the same blocking values which are missing data in the fields used for blocking (such records aren't blocked on individually because of this missingness, so including them after the fact allows them to be considered).

For each Person cluster found during blocking, the system computes an aggregated **log-odds sum** measuring the median number of **log-odds points** the incoming record scored in comparison to each Patient record in the cluster. These sums are tracked across the algorithm and are used to compute a **Relative Match Score (RMS)**, the percentage of total possible log-odds points the incoming record scored during evaluation. These **RMS** values are used in conjunction with **minimum match** and **certain match** thresholds supplied by the user to make final linkage decisions.

#### Scoring Process
1. **Field Comparison**: Each evaluation field is compared between the incoming record and candidate records using fuzzy matching algorithms
2. **Threshold Application**: Only similarity scores above the configured fuzzy threshold for each field contribute points (scores below threshold contribute 0 points)
3. **Weight Application**: Qualifying similarity scores are multiplied by pre-configured log-odds weights specific to each field
4. **Cluster Aggregation**: The median log-odds sum across all patient records in a cluster determines the cluster's overall score
5. **RMS Calculation**: The cluster's RMS is calculated as the median log-odds sum divided by total possible evaluation points for the pass

### Missing Data Handling
The algorithm includes sophisticated handling for incomplete records. These strategies recognize that purely missing data doesn't indicate that two records aren't for the same individual—rather, we might not have enough information to make that determination. These strategies are used in both the blocking and evaluation phases of the algorithm:

1. **Blocking with Missing Data**: Patient records missing blocking fields are still considered if they belong to Person clusters that contain records matching the blocking criteria
2. **Evaluation with Missing Data**: Missing fields receive partial credit based on the `missing_field_points_proportion` parameter (typically 0.5, meaning 50% of possible points)
3. **Missingness Threshold**: If more than `max_missingness_allowed_proportion` (typically 0.5) of evaluation points come from missing fields, the comparison is skipped entirely to avoid decisions based on insufficient data

### Match Grading
For each Person cluster found, a **match grade** is assigned based on where that cluster's **RMS** falls in relation to the provided thresholds:

- If **RMS** < **minimum match threshold**, the cluster is graded as **certainly-not** a match
- If **RMS** ≥ **certain match threshold**, the cluster is graded as a **certain** match
- Otherwise, if the **RMS** is between the two thresholds, the cluster is graded as a **possible** match

## Algorithm Workflow

### 1. Multi-Pass Processing
The algorithm executes multiple passes, each with different blocking and evaluation strategies designed to catch different types of matches. Each pass follows this workflow:

#### Blocking Phase
1. Generate blocking keys from the incoming record based on the pass configuration
2. Find all existing Patient records with matching blocking values
3. Include Patient records from Person clusters of blocked records, even if they have missing blocking data
4. Return the set of candidate Person clusters for evaluation

#### Evaluation Phase
1. For each candidate Person cluster, compare the incoming record against each matched Patient record in the cluster
2. Apply the scoring process described above to calculate log-odds sums
3. Calculate the cluster's RMS and assign a match grade
4. Track results for cross-pass aggregation

### 2. Cross-Pass Aggregation
- Clusters appearing in multiple passes retain their highest RMS score
- Match grades are updated if a higher grade is achieved in any pass
- Final results aggregate the best performance across all passes

### 3. Final Decision Logic
The algorithm makes final linkage decisions based on aggregated results:

**Automatic Linking:**
If at least one cluster is graded as **certain**, the **certain** cluster with the highest **RMS** is returned as the result, and a link is formed between that cluster and the incoming record.

**Manual Review Required:**
If no clusters grade as **certain** but at least one cluster grades as **possible**, no links are made automatically, but the **possible** clusters are returned to the user for manual evaluation.

**New Person Creation:**
If no clusters grade better than **certainly-not**, a new Person cluster is created for the incoming record.
