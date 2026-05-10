import json

class SEOData:
    def __init__(self, file_target: str, title: str, description: str, keywords: str, content: str):
        self.file_target = file_target
        self.title = title
        self.description = description
        self.keywords = keywords
        self.content = content

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "keywords": self.keywords,
            "content": self.content
        }

    @classmethod
    def from_dict(cls, data: dict, file_target: str = ""):
        # Resolves different potential dictionary keys gracefully
        return cls(
            file_target=data.get("file_target") or data.get("file_name") or file_target,
            title=data.get("title") or data.get("seo_title") or "",
            description=data.get("description") or data.get("seo_description") or "",
            keywords=data.get("keywords") or data.get("seo_keywords") or "",
            content=data.get("content") or data.get("seo_content") or data.get("content_optimized") or ""
        )
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, data_str: str, file_target: str = ""):
        return cls.from_dict(json.loads(data_str), file_target)

    # Getters and setters for compatibility
    def get_title(self) -> str:
        return self.title
    
    def get_description(self) -> str:
        return self.description
    
    def get_keywords(self) -> str:
        return self.keywords
    
    def get_content(self) -> str:
        return self.content
    
    def set_title(self, title: str) -> None:
        self.title = title
    
    def set_description(self, description: str) -> None:
        self.description = description
    
    def set_keywords(self, keywords: str) -> None:
        self.keywords = keywords
    
    def set_content(self, content: str) -> None:
        self.content = content
