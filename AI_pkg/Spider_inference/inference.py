import gymnasium as gym
from stable_baselines3 import PPO
from Spider_RL.RL_training_main import CustomSpiderEnv
from Spider_redirect_RL.RL_training_redirect import CustomSpiderRedirectEnv
from Spider_inference.inference_config import InferenceConfig
from utils import utils

class Inference:

    _forward_model = PPO.load(InferenceConfig.FORWARD_MODEL_PATH)
    _redirect_model = PPO.load(InferenceConfig.REDIRECT_MODEL_PATH)

    def gym_env_register(self, node, env_id: str, entry_point: str):
        gym.register(
            env_id,  
            entry_point
        )
        return gym.make(env_id, AI_node = node)
    
    def select_model(self, angle: float, current_model) -> str:
        """
        Select the model to use based on the spider toward angle.
        If angle < InferenceConfig.REDIRECT_SWITCH_TO_FORWARD_ANGLE degrees, use the forward model.
        If angle >= InferenceConfig.FORWORD_SWITCH_TO_REDIRECT_ANGLE degrees, use the turning model.
        """
        if current_model == "forward" and abs(angle) < InferenceConfig.FORWORD_SWITCH_TO_REDIRECT_ANGLE:
            next_model: str = "forward"
        elif current_model == "forward" and abs(angle) >= InferenceConfig.FORWORD_SWITCH_TO_REDIRECT_ANGLE:
            next_model: str = "redirect"
        elif current_model == "redirect" and abs(angle) > InferenceConfig.REDIRECT_SWITCH_TO_FORWARD_ANGLE:
            next_model: str = "redirect"
        elif current_model == "redirect" and abs(angle) <= InferenceConfig.REDIRECT_SWITCH_TO_FORWARD_ANGLE:
            next_model: str = "forward"
        else:
            print("Choose model fail...")

        return next_model
    
    def get_spider_toward_angle(self, node) -> float:
        unity_data: dict = utils.get_observation(node)
        angle: float = abs(unity_data["offset_angle"])
        
        return angle


    def inference(self, node) -> None:

        forward_env = self.gym_env_register(node, CustomSpiderEnv.ENV_NAME, "Spider_RL.RL_training_main:CustomSpiderEnv")
        redirect_env = self.gym_env_register(node, CustomSpiderRedirectEnv.ENV_NAME, "Spider_redirect_RL.RL_training_redirect:CustomSpiderRedirectEnv")

        redirect_env.reset()
        obs, _ = forward_env.reset()
        

        current_model = "forward"
        while (True):
            spider_toward_angle = self.get_spider_toward_angle(node)
            current_model = self.select_model(spider_toward_angle, current_model)

            if current_model == "forward":
                model = self._forward_model
                env = forward_env
            else:
                model = self._redirect_model
                env = redirect_env

            action, _ = model.predict(obs)
            obs, _, _, _, _ = env.step(action)