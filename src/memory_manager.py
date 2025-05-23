
class MemoryManager:
    def __init__(self, max_memory=10):
        self.max_memory = max_memory
        self.user_inputs = []
        self.uploaded_papers = []
        self.search_results = []

    def remember_input(self, user_input: str):
        self.user_inputs.append(user_input)
        if len(self.user_inputs) > self.max_memory:
            self.user_inputs.pop(0)

    def remember_uploaded(self, paper_metadata: dict):
        self.uploaded_papers.append(paper_metadata)
        if len(self.uploaded_papers) > self.max_memory:
            self.uploaded_papers.pop(0)

    def remember_search(self, search_result: list):
        self.search_results.append(search_result)
        if len(self.search_results) > self.max_memory:
            self.search_results.pop(0)

    def get_recent_inputs(self):
        return list(self.user_inputs)

    def get_recent_uploads(self):
        return list(self.uploaded_papers)

    def get_recent_searches(self):
        return list(self.search_results)
