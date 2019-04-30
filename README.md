# rl-sokoban
Sokoban game with RL based playing

# Contents:
<ul>
    <li>
    SokobanGame.py: <br/>
        contains Sokoban game for manual playing. <br/>
        Use command "python SokobanGame.py -h" for list of available options <br/>
    <li>
    SokobanEnv.py: <br/>
        contains SokobanEnv class extending keras-rl rl.core.Env which is used by RL agent <br/>
        RL agent in keras-rl requires environment with specific interface
    <li>
    BasicDQN.py: <br/>
        contains basic example of working Deep Q Learning agent using SokobanEnv class as environment <br/>
        with basic statistics.
    <li>
    DQNAgentUtils.py: <br/>
        contains common utility functions for DQN agents such as saving model summary and weights or plotting rewards <br/>
<ul/>