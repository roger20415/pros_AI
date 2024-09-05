class redirect_PPOConfig:
    """
    The redirect_PPOConfig class encapsulates all configuration parameters for training a redirect PPO model
    for a spider robot. 
    This includes settings related to model creation, loading, training, and environment configuration.

    Attributes:
        LEARNING_RATE (float): The learning rate for the PPO model.
        N_STEPS (int): The number of steps to run in each environment per update.
        BATCH_SIZE (int): The mini-batch size for each gradient update.
        N_EPOCHS (int): The number of epochs for optimizing the PPO model.

        MODEL_PATH (str): The file path for saving and loading the PPO model.
        DEFAULT_MODLE_NAME (str): The default model name used when saving the PPO model.

        SAVE_MODEL_FREQUENCE (int): The frequency (in timesteps) at which the model is saved during training.
        TOTAL_TIME_STEPS (int): The total number of timesteps for training the PPO model. 
        RESET_SCENE_STEP (int): The step numbers PPO training terminate per time and unity scene reset.

        Z_INIT_VALUE (float): The initial value for the pre-z parameter in the environment.
        Z_QUEUE_SIZE (int): The size of the queue for storing pre-z values. Note that the queue is later used to calculate model reward.
        
        REWARD_MODE (str):  "TARGET_MODE" / "NO_TARGET_MODE"

        X_MOTIPLY_PARAM (float) : The penalty multiply parameter of X offset.
        Z_MOTIPLY_PARAM (float) : The reward multiply parameter of forward z behavior.

        TARGET_X (float) : "TARGET_MODE" parameters.
        TARGET_Z (float) : "TARGET_MODE" parameters.

        DISTANCE_MULTIPLY_PARAM (float) : The multiply parameter of calculating distance reward.
        TIME_MULTIPLY_PARAM (float) : The multiply parameter of calculating time penalty.

    Note: 
        n_updates = total_timesteps // (n_steps * n_envs)
    
    """
    
    # Create PPO model
    LEARNING_RATE: float = 0.001
    N_STEPS: int = 1024
    BATCH_SIZE: int = 64
    N_EPOCHS: int = 10

    # Load PPO model
    MODEL_PATH: str = "./redirect_Model/redirect_PPO_spider_2024-09-05.pt"
    DEFAULT_MODLE_NAME: str = "./redirect_Model/redirect_PPO_spider"

    # training PPO model
    SAVE_MODEL_FREQUENCE: int = 1024 * 16
    TOTAL_TIME_STEPS: int = 1024 * 128 * 256
    RESET_SCENE_STEP: int = 1024 * 8

    # Env setting
    X_INIT_VALUE: float = 0.0
    Z_INIT_VALUE: float = 0.0

    # reward setting
    REWARD_MODE: str = "TARGET_MODE"  # "TARGET_MODE" / "NO_TARGET_MODE"
    
    # no target reward mode setting
    X_MOTIPLY_PARAM: float = -5.0 * pow(10, 2) # The penalty multiply parameter of X offset.
    Z_MOTIPLY_PARAM: float = 1.5 * pow(10, 3) # The reward multiply parameter of forward z behavior.
    
    # target reward mode setting
    TARGET_X: float = 0.0 # "TARGET_MODE" parameters.
    TARGET_Z: float = 70.0 # "TARGET_MODE" parameters.

    DISTANCE_MULTIPLY_PARAM: float = 10.0 # The multiply parameter of calculating distance reward.
    TIME_MULTIPLY_PARAM: float = 1.0  # The multiply parameter of calculating time penalty.




