from environs import Env

env = Env()
env.read_env()
# Should contain database name
MONGO_URI = env.str("MONGO_URI")
