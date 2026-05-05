from app.services.config_parser import DocOpsConfig


class ModuleMatcher:
    def __init__(self, config: DocOpsConfig):
        self.config = config

    def match(self, changed_files: list[str]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for filepath in changed_files:
            module = self.config.get_module_for_file(filepath)
            if module:
                if module not in result:
                    result[module] = []
                result[module].append(filepath)
        return result

    def find_affected_docs(self, changed_files: list[str]) -> list[str]:
        modules = self.match(changed_files)
        docs = set()
        for mod_name in modules:
            for doc in self.config.get_docs_for_module(mod_name):
                docs.add(doc)
        return list(docs)

    def find_candidate_docs(self, changed_files: list[str]) -> list[dict]:
        modules = self.match(changed_files)
        result = []
        for mod_name, files in modules.items():
            mod = self.config.modules.get(mod_name)
            result.append({
                "module": mod_name,
                "owner": mod.owner if mod else "",
                "changed_files": files,
                "candidate_docs": self.config.get_docs_for_module(mod_name),
            })
        return result
