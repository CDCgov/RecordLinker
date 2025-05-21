# README

This file explains the purpose and function of each of the data files present
in this directory.

## better_test.csv

This test suite is the result of combining two sources into one testing source of truth:
first, a regraded version of a testing suite initially provided for RL development; 
second, a set of expanded permutation cases developed to more robustly test
combinations of fields, typos, missingness, and logical cases. This is the recommended
testing file for generating algorithm matching performance metrics.

## expanded_nbs_test.csv

This test suite is the product of applying controlled random scrambling to the initial
suite provided for RL development. Simulated random dropout and data quality introduction
is used to produce a larger number of test cases. It is not recommended to use this file
file for general-purpose algorithm performance metrics. However, it provides some utility
as a testing suite for highly randomized experimental data.

## nbs_seed.csv

This file of ~1050 patient records comprises a seeded extract of an MPI that is used
across various algorithm testing configurations. This should always be used as the
seed file for algorithm matching tests.

## nbs_test.csv

This file of 83 cases represents the initial suite of extracted test cases provided
for RL development by our partners. Data is purely synthetic and relies on automated
match grading as part of extraction from its initial system. This was originally the
file used for obtaining general-purpose match performance metrics, but it has now
been replaced with `better_test.csv`.

## sample_seed_data.csv

A small seed file developed for edge case testing of RL during early iterations. Generally
not used over `nbs_seed.csv`.

## sample_test_data.csv

A small test file developed for edge case testing of RL during early iterations. Generally
no longer used.