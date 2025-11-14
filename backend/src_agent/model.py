from langchain_deepseek import ChatDeepSeek
from langchain_community.chat_models.tongyi import ChatTongyi


class ModelFactory:
    def __init__(self, model_type: str):
        self.model_type = model_type
        self.model = self._get_model()
        # self.summary_model = self._get_summary_model()

    def _get_model(self):
        match self.model_type:
            case "deepseek":
                return ChatDeepSeek(model="deepseek-chat", temperature=0.0)
            case "tongyi":
                return ChatTongyi(model="qwen3-max", temperature=0.0)
            case _:
                raise ValueError(f"Invalid model type: {self.model_type}")

    def get_summary_model(self, model_type: str):
        match self.model_type:
            case "deepseek":
                return ChatDeepSeek(model=model_type, temperature=0.0)
            case "tongyi":
                return ChatTongyi(model=model_type, temperature=0.0)
            case _:
                raise ValueError(f"Invalid model type: {self.model_type}")
