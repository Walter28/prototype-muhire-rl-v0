"""REAL Environment for Traffic Signal Control."""

from gymnasium.envs.registration import register


register(
    id="maquette-muhire-rl-v0",
    entry_point="CustomGymEnvSetup.environment.env:RealEnvironment",
)
