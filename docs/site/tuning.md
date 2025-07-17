# Tuning

Record Linker uses a tuning process to optimize matching accuracy by analyzing sample data from your database. During tuning, the system examines both confirmed matches (true-match records) and non-match Patient records to recommend optimal log-odds and RMS threshold values.

## How to Use the Tuning API

Since tuning requires processing substantial amounts of data, the operation runs asynchronously in the background rather than returning immediate results.

### Starting a Tuning Job

To begin tuning, send a POST request to the tuning endpoint:

```sh
curl -X POST -H "Content-Type: application/json" -d '{}' http://{API_SERVER}/api/tuning
```

The API will respond with a `status_url` that you can use to monitor the job's progress.

### Checking Job Status

Monitor your tuning job by making GET requests to the status URL:

```sh
curl -X GET {STATUS_URL}
```

The response includes a `status` field with one of these values:

- **`pending`** - Job is queued and waiting to start
- **`running`** - Tuning is currently in progress
- **`complete`** - Job finished successfully (results available in `results` field)
- **`failed`** - Job encountered an error (error details in `results` field)

### Expected Processing Time

Tuning jobs typically complete within a few minutes, though actual duration depends on several factors:

- The tuning parameters you've configured
- Available CPU and memory resources
- Size of your dataset

### Configuration Options

You can adjust tuning behavior through these application configuration parameters:

- **`TUNING_MATCH_PAIRS`** - Number of confirmed match pairs to analyze
- **`TUNING_NON_MATCH_PAIRS`** - Number of non-match pairs to analyze  
- **`TUNING_NON_MATCH_SAMPLE`** - Sample size for non-match analysis

The default values provide a good balance between processing speed and accuracy. While increasing these values may improve results, the benefits typically diminish as sample sizes grow larger.

### Additional Resources

For detailed API specifications, enable the `TUNING_ENABLED` environment variable and refer to the [API documentation](api-docs.md).

For complete configuration options, see the [Application Configuration guide](app-configuration.md).

## Mathematical Background

**Log-odds** are at the core of the Record Linker service. With new improvements around how missing data is handled, they drive everything from blocking, to skipped steps, to record-record comparisons, and even to assessing the overall fit of a Patient record to an existing Person cluster. But what exactly *is* a “log-odds” value? Where does it come from, and why is that important?

### Overview

Fundamentally, log-odds values are floating point numbers ranging from \~0 to an unspecified positive number (more on this in a bit). They quantify the probability that patient records will agree on a single field (e.g. first name, last name, date of birth, etc.) *because those patients are true matches*, rather than because of random chance. They are the closest means of approximating a **causal relationship** that a record linkage system can have, and the higher the log-odds value, the stronger is the prediction for this matching relationship.

Log-odds are so-called because they are literally logarithms of an odds-ratio: the odds (probability) that the same field in two different records agrees when the two records do match, divided by the odds (probability) that the field in different records agrees when the records do not match. For a field *X* and Records *A* and *B*, where *P\[ | \]* denotes a conditional probability, this is

LogOdds(X) \= log\[(P\[X in A \= X in B | A matches B\]) / (P\[X in A \= X in B | A doesn't match B\])\]

Since both parts of the odds formula measure field agreement in their numerator, the denominator captures how much more likely that agreement is because of true matching rather than true non-matching. Logarithms are used because these probabilities tend to be small decimal values, which can be difficult to work with for both humans (hard to read and interpret) and machines (fractionally small decimals can cause underflow and data loss); taking a logarithm preserves monotonicity, and so scales the numbers to a more manageable, readable range of values (here, monotonicity refers to the ability of a function to preserve number ordering: if you have numbers *x* and *y*, and *x \> y*, then it is always true that *log(x) \> log(y)* ). While it’s possible for a logarithm to evaluate to 0 (if the log\[1\] is taken), log-odds are set-up so that the ratio of probabilities never comes out to 1 (explained more in the steps of the training procedure—this is so that when we use log-odds values as points, every field is worth something rather than contributing 0 information). Additionally, as a consequence of taking the logarithm of a fraction, a log-odds weight has no upper bound—whether a particular set of data and fields has a highest log-odds weight of 10 or 30 depends entirely on the data itself. For our purposes, though, that’s perfectly okay.

### Importance of Training

From the definition above, several things are apparent:

1. Log-Odds values exist *per field* in a record,  
2. Calculating log-odds values depends on knowing in advance which pairs of records match and which don’t, and  
3. The result of the log-odds equation depends on the set of records that the pairs *A* and *B* are pulled from.

We’ll explore Point 2 a bit below, but Point 3 cannot be overstated. For log-odds to be useful in record linkage, they *must* be derived from the same population that will be linked using RecordLinker. It isn’t hard to see why: if weights are trained on a different population, with different fields or even different missingness that doesn’t line up with the characteristics of the population to-be-linked, then the log-odds values no longer function as indicators of causality. Higher numbers no longer mean the field possesses more information than other fields, and the results can no longer be combined to confidently predict a matching condition.

An easy example to visualize is the log-odds value generated for Identifier when working with LAC. In theory, we would expect a unique identification number—such as MRN or even SSN—to be *highly* predictive of the individual to whom it belongs. But LAC’s data was such that most of the time, Identifier was either missing or incorrect, giving it an incredibly low log-odds score (less than 1). This would be problematic to generalize to another population which might have SSN data be present, accurate, and extremely prescriptive. Even worse, consider the reverse scenario, where a log-odds value for SSN was derived from a population in which SSN was present and complete. Trying to port this to an environment like LAC, where identifier data was sparse and often wrong, would lead to disastrous matching decisions: their incomplete, missing, and inaccurate identifier data would be treated by the high log-odds value as being informative, accurate, and predictive, leading to  countless false positive mistakes. 

In order to ensure that log-odds values reflect the distributions of the population on which they will be used, they must be **trained** on data from that population. Fortunately, there’s no complex procedure involved here; it’s a generally straightforward matter to partition a training set of records into known true matches, known non-matches, count up some stats, then normalize and take the logarithm. This process is defined more explicitly below.
