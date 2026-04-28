from resume_rag import load_resumes, create_vector_store
from job_matcher import match_candidates
import json

def main():
    # Step 1: Load resumes
    folder_path = "resumes"
    print("Loading resumes...")
    documents = load_resumes(folder_path)

    # Step 2: Create vector DB
    print("Creating vector database...")
    create_vector_store(documents)

    # Step 3: Job Description
    job_description = """
    Looking for a Python developer with experience in Machine Learning,
    SQL, and AWS. Candidate should have at least 2 years of experience.
    """

    # Step 4: Match candidates
    print("Matching candidates...")
    results = match_candidates(job_description)

    # Step 5: Print results
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()