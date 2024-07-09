import gymnasium as gym
from gymnasium.utils.env_checker import check_env

# import sumo_rl
from CustomGymEnvSetup import *


def test_api():
    env = gym.make(
        "instigo-goma-rl-v0",
        num_seconds=1000,
        use_gui=False,
        sumoconfig_file="E:\Instigo-TS-CTRL\\network\osm.sumocfg"
    )
    env.reset()
    check_env(env.unwrapped, skip_render_check=True)
    env.close()


if __name__ == "__main__":
    test_api()