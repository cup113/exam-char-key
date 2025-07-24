from train.models import AiEvaluator

class QwenLongEvaluator(AiEvaluator):
    model_code = "qwen-long-latest"
    model_name = "ql"

class QwenPlusEvaluator(AiEvaluator):
    model_code = "qwen-plus-latest"
    model_name = "qp"
