from langchain_deepseek import ChatDeepSeek
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.chat_models.moonshot import MoonshotChat
import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# from pydantic import SecretStr


class ModelFactory:
    def __init__(self, model_type: str):
        self.model_type = model_type
        self.model = self._get_model()
        # self.summary_model = self._get_summary_model()

    def _get_model(self):
        match self.model_type:
            case "deepseek":
                return ChatDeepSeek(model=os.getenv("DEEPSEEK_MODEL"), temperature=0.0)
            case "tongyi":
                return ChatTongyi(model=os.getenv("DASHSCOPE_MODEL"), temperature=0.0)
            case "ANTHROPIC":
                return ChatAnthropic(model=os.getenv("ANTHROPIC_MODEL"), temperature=0.0)
            case "moonshot":
                return ChatOpenAI(
                    model=os.getenv("MOONSHOT_MODEL"),
                    base_url=os.getenv("MOONSHOT_BASE_URL"),
                    api_key=os.getenv("MOONSHOT_API_KEY"),
                    temperature=0.0,
                )
            case _:
                raise ValueError(f"Invalid model type: {self.model_type}")

    def get_summary_model(self, model_type: str):
        match self.model_type:
            case "deepseek":
                return ChatDeepSeek(model=model_type, temperature=0.0)
            case "tongyi":
                return ChatTongyi(model=model_type, temperature=0.0)
            case "ANTHROPIC":
                return ChatAnthropic(model=model_type, temperature=0.0)
            case "moonshot":
                return ChatOpenAI(
                    model=model_type,
                    base_url=os.getenv("MOONSHOT_BASE_URL"),
                    api_key=os.getenv("MOONSHOT_API_KEY"),
                    temperature=0.0,
                )
            case _:
                raise ValueError(f"Invalid model type: {self.model_type}")
