# RFC: Possible Match with Log Odds Score Threshold Range

- **Status**: Deferred
- **Author(s)**: @alhayward
- **Creation Date**: 2024-12-26
- **Last Updated**: 2025-01-02
- **RFC ID**: RFC-002

---

## Summary

The purpose of this Request for Change (RFC) is to recommend an approach for determining a Possible Match in the Record Linkage algorithm by evaluating a user-configurable threshold range for the (median) [Log Odds Score](https://cdc.sharepoint.com/:w:/r/teams/OPHDST-IRD-DIBBs/_layouts/15/doc2.aspx?sourcedoc=%7BCD3D39E1-FC95-4555-8841-15AE92ED317C%7D&file=DIBBs%20Record%20Linkage%20Algorithm%20and%20Terminology.docx&action=default&mobileredirect=true) between an incoming Patient record and the existing Patient records in a Person Cluster. This RFC proposes an alternative approach from the current implementaton, which is a user-configurable threshold range applied to the Belongingness Ratio. As such, the changes proposed in this RFC would fundamentally shift the concept of "Belongingness" in the Record Linkage algorithm by changing the calculation that determines Cluster Membership.

On the IDWA Record Linker Project in collaboration with NBS, this is Skylight's recommended Long-Term Approach for implementing Possible Match. It more robustly determines whether an incoming Patient record "belongs" to a given Person Cluster by evaluating a more granular similarity function: one of Log Odds Score. Compared to the current Short-Term Approach, this method retains more information about how similar Patient records are when comparing one incoming Patient record against *n* Patient records of an existing Person Cluster, and uses that information to make a more informed decision regarding Cluster Membership.

## Motivation

* **Record Linker Product Roadmap.** In the IDWA Record Linker Product Roadmap, this was originally Skylight's recommended Long-Term Approach for implementing Possible Match; ideally, when production data from a STLT became available to more effectively test the performance of this approach against the current implementation (Short-Term Approach). With NBS' Record Linker pilot with Montana in early 2025, this may now be possible. For previous work in the IDWA Record Linker Product Roadmap regarding this approach, see Possible Match [Visualizations](https://cdc.sharepoint.com/teams/OPHDST/Shared%20Documents/Forms/AllItems.aspx?csf=1&web=1&e=mFyMOs&CID=bb4d88fd%2Da9cd%2D4489%2Dbe4c%2D83b71d4da37a&FolderCTID=0x0120007CFDF2D06C84CB42802622FBC25C7BFB&id=%2Fteams%2FOPHDST%2FShared%20Documents%2FIDWA%2FRecord%20Linker%2FNBS%20%2D%20RL%20Collaboration%2FVisualization&viewid=16bc497e%2Dee77%2D45c7%2Dbc0a%2Ddad9183f0d5b) and [Examples](https://cdc.sharepoint.com/:b:/r/teams/OPHDST/Shared%20Documents/IDWA/Record%20Linker/NBS%20-%20RL%20Collaboration/Possible%20Match%20Examples.pdf?csf=1&web=1&e=Qejd20) (Fall 2024).

* **More Granular Similarity Metric.** Skylight recommends this approach because, compared to the current impementation, it retains more granular information about how similar Patient records are when comparing an incoming Patient record to those of an existing Person cluster, then uses that information to make a more informed decision about Cluster Membership.

    In the current Record Linkage algorithm, there are two decision points: 1) a Patient-Patient match decision (does incoming Patient record *i* match existing Patient record *j*?), and 2) a Patient-Person match decision (does incoming Patient record *i* match Person Cluster *A*?). The former evaluates a Log Odds Score (between two Patient records) against a user-configurable, currently binary threshold (i.e., [`true_match_threshold`](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json#L102)). The latter evaluates a Belongingness Ratio (between a Patient record and a Person Cluster) against a user-configurable threshold range (i.e., [`belongingness_ratio`](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json#L7) in the Short-Term Approach). 

    In this proposed approach, rather than make a preliminary (binary) decision about whether Patient *i* and Patient *j* match or not, the valuable information about *how similar* Patient record *i* and Patient record *j* are (captured by the Log Odds Score) is propagated through the algorithm, until a final decision is required regarding whether Patient *i* matches Person Cluster *A*. In this approach, the more granular information about the *extent of similarity* between Patient *i* and Patient *j*, *k*, ... *n* is not "lost" by premature binning. Rather, the information about how similar the incoming Patient record is with *each* existing Patient record is retained, until a final decision about Cluster Membership must be made. At this point, a function of the distribution of Log Odds Scores between incoming Patient record *i* and existing Patient records *j*, *k*, ... *n* in Person Cluster *A* (e.g., median) would be calculated. Upon configuration, the user defines a threshold range for this metric of Log Odds Score (e.g., a range of median Log Odd Scores), against which the metric will be evaluated to determine whether Patient record *i* matches Person Cluster *A*, for each Person Cluster found in Blocking. This allows for a more granular metric of "belongingness" than simply a function of Belongingness Ratio, which has some limitations as outlined below.

* **Low-*n* Person Clusters.** Our CDC stakeholders and NBS customers have raised concerns about the current implementation of applying a threshold range to the Belongingness Ratio due to its behavior with MPIs that have Person Clusters of low *n*. That is, when a Person Cluster has a low number of Patient records associated with it, the Belongingness Ratio between an incoming Patient record and that Person Cluster tends to 0% or 100% (see [Possible Match Examples](https://cdc.sharepoint.com/:b:/r/teams/OPHDST/Shared%20Documents/IDWA/Record%20Linker/NBS%20-%20RL%20Collaboration/Possible%20Match%20Examples.pdf?csf=1&web=1&e=Qejd20)). This extreme behavior limits the usefulness of a threshold applied to the Belongingness Ratio to model the concept of a "possible match" in certain cases. For example, STLTs with small MPIs, MPIs with low-*n* Person Clusters, or MPIs with poor quality Person Clusters. The third case may be relevant when a STLT wants to implement the Record Linker solution only to *incoming* Patient records, rather than applying Record Linker to *existing*  Patient records, to retrospectively "clean" the Person Clusters in the MPI (for example, these poor quality Person Clusters may be due to a lesser performing Record Linkage solution previously used by the STLT). There may be various reasons that disincentivize a STLT (or NBS) to perform the "batch" cleaning process of existing Person Clusters within an MPI using the Record Linker solution (e.g., computational resources).

* **User-Friendly.** Through Skylight's partnership with NBS, the IDWA Record Linker Team has gained insight into Subject Matter Experts (SMEs) and potential users, including public health epidemiologists. Through our collaboration, we have found that defining the concept of a "possible match"  may be more accessible and understandable to certain public health staff by using a function of the Log Odds Score (e.g., median). Based on our engagement, the Log Odds Score in particular is a statistical metric for similarity that is familiar to public health epidemiologists in the context of patient Record Linkage. By determining a "possible match" using a function of Log Odds Score, a metric that our customers have comfort and trust in, we may build further trust in the Record Linker product with customers and end-users.

See [#18](https://github.com/CDCgov/RecordLinker/issues/18#issuecomment-2387148409) for further Discussion.

## Proposal

Given a [Log Odds Score Threshold](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json#L102) Range, [X, Y],

When comparing incoming Patient record _i_ to all existing Patient records _j_, _k_, ... _n_ in Person Cluster *A*, store all intermediary Log Odds Scores, ${x_{i}}, \dots, {x_{n}}$. After all *n* Patient records are compared, calculate a single metric of the distribution of Log Odds Scores, ${M}$ (e.g., median).

If ${M}$ is...
* < X, return **No Match**
* \> Y, return **Match**
* \>= X and <= Y, return **Possible Match (Manual Review)**

For Patient record examples of this approach using median Log Odds Score, see [Possible Match Examples](https://cdc.sharepoint.com/:b:/r/teams/OPHDST/Shared%20Documents/IDWA/Record%20Linker/NBS%20-%20RL%20Collaboration/Possible%20Match%20Examples.pdf?csf=1&web=1&e=Qejd20).

## Alternatives Considered

### Short-Term Approach: Apply a User-Configurable Range to the [Belongingness Threshold](https://cdc.sharepoint.com/:w:/r/teams/OPHDST-IRD-DIBBs/_layouts/15/Doc.aspx?sourcedoc=%7BCD3D39E1-FC95-4555-8841-15AE92ED317C%7D&file=DIBBs%20Record%20Linkage%20Algorithm%20and%20Terminology.docx&action=default&mobileredirect=true) (i.e. [`cluster_ratio`](https://github.com/CDCgov/RecordLinker/blob/55352fdf898a139396a83c016987fcb1fc8122df/src/recordlinker/linkage/algorithms.py#L69))
*Patient-Person Level*

&nbsp;&nbsp;&nbsp;&nbsp;Given Belongingness Threshold Range, [X, Y],

&nbsp;&nbsp;&nbsp;&nbsp;If an incoming Patient record matches...
* < X of existing Patient records in a Person cluster, return **No Match**
* \> Y of existing Patient records in a Person cluster, return **Match**
* \>= X and <= Y of existing Patient records in a Person cluster, return **Possible Match (Manual Review)**

#### Motivation
* While there were many places in the code that could be adjusted to achieve Possible Match, this was a good, low-lift place to start. This initial Short-Term approach aimed to limit the amount of changes to the _underlying algorithm_, and moreso simply change the format of the _output prediction_ (3 classes instead of 2). Because the DIBBs team completed extensive [research & literature review](https://cdc.sharepoint.com/:w:/r/teams/CSELS-DHIS-ISB-NBS/_layouts/15/Doc.aspx?sourcedoc=%7BA6169829-A703-4DB4-98FB-6FCB50BECC01%7D&file=RL-PRD-and-Lit-Review.docx&action=default&mobileredirect=true) to design the algorithm (i.e., how Blocking/Matching is performed), the original algorithm was retained as much as possible, unless additional research showed that an alternative algorithm design is more performant.
* At a high-level, the output of the Record Linkage algorithm is a *probability* (of whether an incoming Patient record matches an existing Person Cluster). Initially, the probability was binned to 2 classes: **Match** (>= X threshold) or **No Match** (< X threshold). In this Short-Term Approach, we changed the binning to 3 classes: **Match** (> Y threshold), **Possible Match** (<= Y threshold but >= X threshold), and **No Match** (< X threshold). The underlying algorithm remained the same.

#### Limitations
* See above **Motivation** (e.g., **More Granular Similarity Metric**, **Low-*n* Person Clusters**, **User-Friendly**).

### NBS Approach: Apply a User-Configurable Range the [Log Odds Score](https://cdc.sharepoint.com/:w:/r/teams/OPHDST-IRD-DIBBs/_layouts/15/Doc.aspx?sourcedoc=%7BCD3D39E1-FC95-4555-8841-15AE92ED317C%7D&file=DIBBs%20Record%20Linkage%20Algorithm%20and%20Terminology.docx&action=default&mobileredirect=true) Threshold (i.e. [`true_match_threshold`](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json#L102))
*Patient-Patient Level*

&nbsp;&nbsp;&nbsp;&nbsp;Given a Log Odds Score Threshold Range, [X, Y],

&nbsp;&nbsp;&nbsp;&nbsp;When comparing incoming Patient record _i_ to existing Patient record _j_, if the sum of the log odds scores is...
* < X, return **No Match**
* \> Y, return **Match**
* \>= X and <= Y, return **Possible Match (Manual Review)**

#### Motivation
* This approach would allow for more granular review of Possible Matches (upon match decision between a Patient record-Patient record pair, rather than upon Cluster Membership decision).
* This is the approach [NBS](https://cdc.sharepoint.com/teams/CSELS-DHIS-ISB-NBS/_layouts/15/stream.aspx?id=%2Fteams%2FCSELS%2DDHIS%2DISB%2DNBS%2FShared%20Documents%2FNBS%20Modernization%20Project%2FDeDuplication%2FUX%2FPatient%20merge%20configuration%2Emov&referrer=StreamWebApp%2EWeb&referrerScenario=AddressBarCopied%2Eview%2Eb1b822b6%2Db97a%2D4550%2Db841%2Df79062d17baa) initially planned to take.

#### Limitations
* This approach implements Possible Match at a *pass level* (i.e., Manual Review of individual Patient record-Patient record match decisions), rather than a *Person level* (i.e., Manual Review of overall Person Cluster Membership decisions). As a result, there were limitations around how this approach would scale (e.g., Person Clusters with *n*>2 Patient records). For example, it is unclear how to determine whether an incoming Patient record matches a Person Cluster. Would this always be blocked by users completing Manual Review of all Possible Matches? Additionally, if a Patient record is pending Manual Review, will it be considered for comparison against future incoming Patient records in the queue? See [#18](https://github.com/CDCgov/RecordLinker/issues/18#top) for Patient record examples that demonstrate the limitations of this approach.
* Implementing Possible Match (and thus Manual Review) at a *pass level* can create additional manual work. This manual work may also block the Record Linkage algorithm from determining a match decision, which can create bottlenecks for required Manual Reviews as the MPI grows. To arrive at a match decision, the user may need to reconcile many Possible Matches between different permutations of record pairs.

## Risks and Drawbacks

* **Change in Concept of "Belongingness"**. This approach fundamentally changes the Record Linker algorithm, by propagating intermediary log odds scores and using them in the Cluster Membership decision. Thus, the calculation and concept of "belongingness" is shifted (the previous Belongingness Ratio is no longer used). Rather than prematurely "bin" (or "round") the similarity between two Patient records to either Match or No Match (based on the Log Odds Score between them), this approach retains that similarity information until later while iterating through the Person Cluster. As a result, that information about *extent of match* is not lost from "binning" to a binary decision early on, and rather becomes useful in the final Cluster Membership decision. This enhancement comes at the cost of changing the defintion or meaning of "Belongingness" as is currently understood in the Record Linker product, due to the change in Cluster Membership calculation. As a result, changes to documentation around how Cluster Membership is determined are needed.
* **Optimization of Default Log Odds Score Threshold Range Values.** Similar to the optimization process for the current default Log Odds Score Threshold values (e.g., for LA County), this approach may require calibration of optimal values to set a default Log Odds Score Threshold Range in the [initial Record Linker algorithms](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json#L102). Additionally, if distributions of Log Odds Scores differ by pass (e.g., Pass 1 vs. Pass 2), then optimization of these values would be required by pass. (For example, the optimal Log Odds Score Threshold Range values for Pass 1 may differ from the optimal values for Pass 2, just as the current binary threshold values of `12.2` and `17.0, respectively, differ.) However, this is not different from the current optimization process that was required to determine the existing default Log Odds Score Threshold values (i.e. [true_match_threshold](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json#L102) values), or that may be required to optimize the [Belongingness Ratio Threshold Range](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json#L7) values of the current Short-Term Approach, if desired.

* **Explainability.** While using a metric of Log Odds Score may be more understandble among certain users such as public health epidimiologists, this approach to determine Cluster Membership may be less explainable than the Belongingness Ratio (e.g., percentage of existing Patient records in the Person Cluster with which the incoming Patient record matches). However, if a STLT would like to use a more explainable approach to Record Linkage, they have the option of using the DIBBs Basic (deterministic) Algorithm to determine matches, which does not use Log Odds Scores.

* **DIBBs Basic Algorithm.** If a STLT does not wish to use functions with Log Odds Scores, i.e. use the DIBBs Basic Algorithm instead, then a Match Rule function that is not evaluating the sum of Log Odds Scores against a cutoff (e.g., `recordlinker.linking.matchers.rule_probabilistic_match`) will be used (e.g., `recordlinker.linking.matchers.rule_match`). In that case, the same behavior from the Feature Comparison and Match Rule functions of the deterministic DIBBs Basic Algorithm applies. See **Caveats** in [#18](https://github.com/CDCgov/RecordLinker/issues/18) for more information.

## Implementation Plan

### Code
* The [`true_match_threshold`](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json#L102) parameter of the [`initial_algorithms.json`](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json) configuration must be modified from accepting a binary threshold, e.g. `12.2`, to a valid range, e.g. `[10, 14]`. At minimum, validation should verify values >= 0.
* As necessary, Feature Comparison and Match Rule functions must be modified to return the Log Odds Score, not boolean values. This is so that the intermediary Log Odds Scores between incoming Patient record *i* and existing Patient records *j*, *k*, ... *n* may be stored for each Person Cluster evaluated.
* For each Person Cluster evaluated, all intermediary Log Odds Scores between incoming Patient record *i* and existing Patient records *j*, *k*, ... *n* must be stored. These values must be stored so that after all *n* Patient records are compared, the metric of the distribution of Log Odds Scores (e.g., median) may be calculated.
* After all *n* Patient records in the Person Cluster have been compared, to determine final Cluster Membership, a metric must be calculated from the distribution of Log Odds Scores stored (e.g., median), *M*. Then, *M* must be evaluated against the user-configured threshold range values for that metric of Log Odds Score (e.g., [`true_match_threshold`](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json#L102) range). If *M* < X, return **No Match**; if *M* \> Y, return **Match**; if *M* \>= X and <= Y, return **Possible Match (Manual Review)**. Depending on whether the `include_multiple_matches` flag is `true`, if multiple **Matches** are found, return the multiple matched Persons or the Person with the highest (median) Log Odds Score (proxy for highest "belongingness").

### Documentation
* Any documentation regarding Belongingness Ratio or how Cluster Membership is determined must be updated to reflect the new metric of Log Odds Score used (e.g., median), as well as the new non-binary, user-configured threshold range for this metric.

## Future Possibilities

**Identify Optimal Possible Match Approach with Production Data.** The most robust way to determine the highest performing approach for implementing Possible Match is to evaluate the match accuracy of the proposed approaches against production data. See **Long-Term** in [#18](https://github.com/CDCgov/RecordLinker/issues/18) for more information.

---

## Footnotes or References
1. [#139 rfc-002 cluster membership using log-odds scores](https://github.com/CDCgov/RecordLinker/issues/139)
2. [#18 Algorithm changes to support more diverse set of responses](https://github.com/CDCgov/RecordLinker/issues/18#issuecomment-2387148409)
3. [DIBBs Record Linkage Algorithm and Terminology](https://cdc.sharepoint.com/:w:/r/teams/OPHDST-IRD-DIBBs/_layouts/15/Doc.aspx?sourcedoc=%7BCD3D39E1-FC95-4555-8841-15AE92ED317C%7D&file=DIBBs%20Record%20Linkage%20Algorithm%20and%20Terminology.docx&action=default&mobileredirect=true) 
4. [Possible Match Visualizations](https://cdc.sharepoint.com/teams/OPHDST/Shared%20Documents/Forms/AllItems.aspx?csf=1&web=1&e=mFyMOs&CID=bb4d88fd%2Da9cd%2D4489%2Dbe4c%2D83b71d4da37a&FolderCTID=0x0120007CFDF2D06C84CB42802622FBC25C7BFB&id=%2Fteams%2FOPHDST%2FShared%20Documents%2FIDWA%2FRecord%20Linker%2FNBS%20%2D%20RL%20Collaboration%2FVisualization&viewid=16bc497e%2Dee77%2D45c7%2Dbc0a%2Ddad9183f0d5b)
5. [Possible Match Examples](https://cdc.sharepoint.com/:b:/r/teams/OPHDST/Shared%20Documents/IDWA/Record%20Linker/NBS%20-%20RL%20Collaboration/Possible%20Match%20Examples.pdf?csf=1&web=1&e=Qejd20)
6. [initial_algorithms.py](https://github.com/CDCgov/RecordLinker/blob/c07aea2f15b6a86f54bcf48a37dcc5fac44d3ba4/src/recordlinker/assets/initial_algorithms.json)