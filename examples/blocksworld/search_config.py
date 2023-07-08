import numpy as np

import utils
from world_model import BWState, BWAction
from rap import SearchConfig, LanguageModel

class BWConfig(SearchConfig):
    def __init__(self,
                 base_model: LanguageModel,
                 prompt: dict,
                 batch_size=2,
                 reward_alpha=0.5,
                 goal_reward_default=0.,
                 goal_reached_reward=100) -> None:
        super().__init__()
        self.base_model = base_model
        self.example = None
        self.prompt = prompt
        self.batch_size = batch_size
        self.reward_alpha = reward_alpha
        self.goal_reward_default = goal_reward_default
        self.goal_reached_reward = goal_reached_reward

    def get_actions(self, state: BWState) -> list[BWAction]:
        # print("state: ", state)
        # print("type: ", type(state))
        blocks_state = state.blocks_state
        return utils.generate_all_actions(blocks_state)

    def fast_reward(self, state: BWState, action: BWAction) -> tuple[float, dict]:
        if state.buffered_action == "":
            # if no action buffered
            current_blocks_state = state.blocks_state
        else:
            # if action buffered
            current_blocks_state = state.last_blocks_state
        previous_action = state.buffered_action + "\n" if state.buffered_action != "" else ""
        inputs = self.prompt["icl"].replace("<init_state>", current_blocks_state)\
            .replace("<goals>", utils.extract_goals(self.example, return_raw=True)).replace("<action>", previous_action)
        # print("inputs:", inputs)
        # print("actions:", [inputs + action])
        intuition = self.base_model.get_loglikelihood(inputs, [inputs + action])[0]
        # print("intuition:", intuition)
        return self.calculate_reward(intuition), {'intuition': intuition}

    def calculate_reward(self, intuition, goal_reached=None):
        if goal_reached is None:
            goal_reward = self.goal_reward_default
        elif goal_reached[0]:
            goal_reward = self.goal_reached_reward
        else:
            goal_reward = goal_reached[1]
        return intuition * self.reward_alpha + goal_reward * (1 - self.reward_alpha)

    def reward(self, state: BWState, action: BWAction,
               intuition: float = None,
               goal_reached: tuple[bool, float] = None) -> float:
        assert intuition is not None, "intuition is required to calculate reward in this search config, consider passing it in fast_reward"
        assert goal_reached is not None, "goal_reached is required to calculate reward in this search config, consider passing it in world model's step"
        return self.calculate_reward(intuition, goal_reached), {'intuition': intuition, 'goal_reached': goal_reached}

    def update_example(self, example) -> None:
        super().update_example(example)
        # print("goal", utils.extract_goals(example, return_raw=True))