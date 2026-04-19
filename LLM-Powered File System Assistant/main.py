from llm_integration.llm_file_assistant import handle_query

def main():
    query = "Create a summary file for python_resume.pdf give me in response "

    result = handle_query(query)

    print(result)


if __name__ == "__main__":
    main()