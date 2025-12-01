"""Quick test for Factory environment."""

import realtimegym

# Test creating the environment
print("Creating Factory environment...")
env, seed, renderer = realtimegym.make("Factory-v0", seed=0, render=False)

print(f"Environment created successfully! Seed: {seed}")
print(f"Environment type: {type(env)}")

# Test reset
print("\nResetting environment...")
obs, done = env.reset()
print(f"Done: {done}")
print(f"Observation keys: {obs.keys()}")

# Print initial state
print("\n" + env.state_string())

# Test a few steps
print("\nRunning 5 steps...")
for i in range(5):
    obs, done, reward, reset = env.step("WAIT")
    print(f"Step {i+1}: Reward={reward:.2f}, Done={done}")

print("\nFinal state:")
print(env.state_string())

print("\n✅ Factory environment test completed successfully!")
