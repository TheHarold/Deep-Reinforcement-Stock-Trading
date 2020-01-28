import random
from collections import deque

import numpy as np
from tensorflow.keras import Sequential
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import TensorBoard


class Agent:
    def __init__(self, state_dim, balance=50000, is_eval=False, model_name=""):
        self.model_type = 'DQN'
        self.state_dim = state_dim
        self.action_dim = 3  # hold, buy, sell
        self.memory = deque(maxlen=100)
        self.batch_size = 60
        self.initial_portfolio_value = balance
        self.balance = balance
        self.inventory = []
        self.return_rates = []
        self.portfolio_values = [balance]
        self.buy_dates = []
        self.sell_dates = []

        self.gamma = 0.95
        self.epsilon = 1.0  # initial exploration rate
        self.epsilon_min = 0.01  # minimum exploration rate
        self.epsilon_decay = 0.995 # decrease exploration rate as the agent becomes good at trading
        self.is_eval = is_eval
        self.model = load_model("saved_models/" + model_name) if is_eval else self.model()

        self.tensorboard = TensorBoard(log_dir='./logs/DQN', update_freq=90)
        self.tensorboard.set_model(self.model)

    def model(self):
        model = Sequential()
        model.add(Dense(units=64, input_dim=self.state_dim, activation="relu"))
        model.add(Dense(units=32, activation="relu"))
        model.add(Dense(units=8, activation="relu"))
        model.add(Dense(self.action_dim, activation="softmax"))
        model.compile(loss="mse", optimizer=Adam(lr=0.001))
        return model

    def reset(self, balance):
        self.balance = balance
        self.inventory = []
        self.return_rates = []
        self.portfolio_values = [balance]
        self.epsilon = 1.0

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if not self.is_eval and np.random.rand() <= self.epsilon:
            return random.randrange(self.action_dim)
        options = self.model.predict(state)
        return np.argmax(options[0])

    def experience_replay(self, batch_size):
        # retrieve recent batch_size long memory
        mini_batch = []
        l = len(self.memory)
        for i in range(l - batch_size + 1, l):
            mini_batch.append(self.memory[i])

        for state, action, reward, next_state, done in mini_batch:
            if not done:
                target_value = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
            else:
                target_value = reward
            next_actions = self.model.predict(state)
            next_actions[0][action] = target_value
            history = self.model.fit(state, next_actions, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        return history.history['loss'][0]
