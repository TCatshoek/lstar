import gym
import pickle

from equivalencecheckers.bruteforce import BFEquivalenceChecker
from experiments.reinforcementlearning.approximatelstar import ApproximateMealyLearner
from experiments.reinforcementlearning.approximaterandomwalk import ApproximateRandomWalkEquivalenceChecker
from suls.sul import SUL
import numpy as np

from statistics import mean

from teachers.teacher import Teacher


def s_to_rc(s, ncol):
    return s // ncol, s % ncol

def rc_to_s(row, col, ncol):
    return row*ncol + col

def sample_future_reward(s, env, discount=0.9, n_samples=10000):
    env_backup = pickle.dumps(env)
    _env = pickle.loads(env_backup)

    # old_s = env.unwrapped.s
    # old_lastaction = env.unwrapped.lastaction
    #
    # new_s = s #rc_to_s(row, col)
    # env.unwrapped.s = new_s

    best_reward = None
    rewards = []

    for i in range(n_samples):
        done = False
        n_steps = 0

        _env.reset()
        _env.unwrapped.s = s
        _env.lastaction = None
        _env.seed(seed=np.random.randint(99999))

        # env.reset()
        #print("begin")
        # env.unwrapped.s = new_s
        # env.unwrapped.lastaction = None
        #_env.render()

        while not done:
            action = np.random.randint(4)#_env.action_space.sample()
            observation, reward, done, info = _env.step(action)
            n_steps += 1
            #_env.render()
            if done:
                #print(env.s)
                #_env.render()
                discounted_reward = (discount ** n_steps) * reward
                rewards.append(discounted_reward)
                if best_reward is None or discounted_reward > best_reward:
                    best_reward = discounted_reward
                    #print("end", reward)
                    #env.reset()
                #break

    
    #return best_reward
    return mean(rewards)

class GymSUL(SUL):
    def __init__(self, env, discount=0.9, n_access_samples=10, n_samples=100):
        self.env = env
        self.discount = discount
        self.n_samples = n_samples
        self.n_access_samples = n_access_samples

    def process_input(self, inputs):
        rewards = []
        for i in range(self.n_access_samples):
            env.reset()

            for input in inputs:
                observation, reward, done, info = env.step(input)

            rewards.append(sample_future_reward(observation, env, self.discount, self.n_samples))

        return mean(rewards)

    def reset(self):
        self.env.reset()

    def get_alphabet(self):
        return set(range(self.env.action_space.n))

class DirectGymSUL(SUL):
    def __init__(self, env, n_samples=100):
        self.env = env
        self.n_samples = n_samples

    def process_input(self, inputs):
        rewards = []

        for i in range(self.n_samples):
            self.reset()
            for input in inputs:
                observation, reward, done, info = env.step(input)
            rewards.append(reward)

        return mean(rewards)

    def reset(self):
        self.env.reset()

    def get_alphabet(self):
        return set(range(self.env.action_space.n))


if __name__ == "__main__":

    e = 0.5

    env = gym.make('FrozenLake-v0', is_slippery=True)
    sul = DirectGymSUL(env)

    eqc = ApproximateRandomWalkEquivalenceChecker(sul, e=e)

    teacher = Teacher(sul, eqc)

    learner = ApproximateMealyLearner(teacher, e=e)

    hyp = learner.run(show_intermediate=True)


    env.close()