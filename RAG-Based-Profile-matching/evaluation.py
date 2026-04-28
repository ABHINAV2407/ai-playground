from job_matcher import match_candidates
import time

jd = """
Looking for a Python developer with experience in Machine Learning,
SQL, and AWS. Candidate should have at least 2 years of experience.
"""

# Run matching
results = match_candidates(jd)

# Print results
print("\nTop Matches:\n", results["top_matches"])


# -------------------------------
# METRIC 1: Precision@K
# -------------------------------
def precision_at_k(results, ground_truth, k=10):
    predicted = [r["candidate_name"] for r in results["top_matches"][:k]]
    correct = len(set(predicted) & set(ground_truth))
    return correct / k


# Replace with real names from your resumes
ground_truth = ["Abhinav"]

precision = precision_at_k(results, ground_truth)
print("\nPrecision@10:", precision)


# -------------------------------
# METRIC 2: Latency
# -------------------------------
start = time.time()
match_candidates(jd)
end = time.time()

print("Latency:", end - start, "seconds")