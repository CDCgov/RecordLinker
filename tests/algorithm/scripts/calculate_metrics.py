MATCH_GRADE_MAPPER = {"certain": "match", "certainly-not": "no_match", "possible": "possible_match"}

def compare_and_calculate_result_metrics(results_file):

    with open(results_file, 'r') as fp:
        test_cases = fp.readlines()
        test_cases = [x.strip().split(",") for x in test_cases[1:]]
        true_positives = 0.0
        true_negatives = 0.0
        false_positives = 0.0
        false_negatives = 0.0

        # Trackers for cases NBS said were possible but we didn't
        possible_matches_yes = 0.0
        possible_matches_no = 0.0
        possible_matches_maybe = 0.0

        # Trackers for cases we said were possible but NBS didn't
        pmy = 0.0
        pmn = 0.0
        pmm = 0.0

        for tc in test_cases:
            exp = tc[1].strip()
            grade = tc[2].strip()

            # Possible matches get handled separately because manual human
            # review is the desired way of making a final decision
            if exp == "possible_match":
                if grade == "certain":
                    possible_matches_yes += 1.0
                elif grade == "certainly-not":
                    possible_matches_no += 1.0
                elif grade == "possible":
                    possible_matches_maybe += 1.0

            # We track cases that the test set expected to be possible and cases
            # that we grade as possible separately, because there's no guarantee
            # those sets of cases overlap
            if grade == "possible":
                if exp == "match":
                    pmy += 1.0
                elif exp == "no_match":
                    pmn += 1.0
                elif exp == "possible_match":
                    pmm += 1.0

            # Checking if our predicted grade is defined allows us to handle the
            # error processing in a few test cases
            if grade in MATCH_GRADE_MAPPER:
                grade = MATCH_GRADE_MAPPER[grade]
                if grade == exp and grade == "match":
                    true_positives += 1.0
                elif grade == exp and grade == "no_match":
                    true_negatives += 1.0
                elif grade == "no_match" and exp == "match":
                    false_negatives += 1.0
                elif grade == "match" and exp == "no_match":
                    false_positives += 1.0
        
        # Let's make our prints nicely formatted
        print()
        print("Results:")
        print(str(true_positives), "true positives correctly identified")
        print(str(true_negatives), "true negatives correctly identified")
        print(str(false_positives), "false positives misidentified")
        print(str(false_negatives), "false negatives misidentified")
        print()

        sensitivity = true_positives / (true_positives + false_negatives)
        print("Sensitivity:", str(sensitivity))
        specificity = true_negatives / (true_negatives + false_positives)
        print("Specificity:", str(specificity))
        f1 = (2 * true_positives) / (2 * true_positives + false_positives + false_negatives)
        print("F1-Score:", str(f1))
        ppv = true_positives / (true_positives + false_positives)
        print("PPV:", str(ppv))
        print()

        print("Possible Matches, NBS Perspective")
        print(str(possible_matches_yes), "NBS-labelled possible matches we graded 'certain'")
        print(str(possible_matches_no), "NBS-labelled possible matches we graded 'certainly-not'")
        print(str(possible_matches_maybe), "NBS-labelled possible matches we graded 'possible-match'")
        print()
        print("Possible Matches, DIBBs Perspective")
        print(str(pmy), "DIBBs-labelled possible matches NBS graded 'certain'")
        print(str(pmn), "DIBBs-labelled possible matches NBS graded 'certainly-not'")
        print(str(pmm), "DIBBs-labelled possible matches NBS graded 'possible-match'")
