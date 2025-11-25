"""Test script for the Factory environment."""

import realtimegym


def test_factory_environment():
    """Test basic factory environment functionality."""
    print("=" * 60)
    print("Testing Factory Environment")
    print("=" * 60)

    # Create environment
    print("\n1. Creating Factory-v0 environment...")
    env, seed, renderer = realtimegym.make("Factory-v0", seed=0, render=False)
    print(f"   Environment created with seed: {seed}")

    # Reset environment
    print("\n2. Resetting environment...")
    obs, done = env.reset()
    print(f"   Reset complete. Terminal: {done}")
    print(f"   Observation keys: {obs.keys()}")

    # Print initial state
    print("\n3. Initial state:")
    print(env.state_string())

    # Run a few steps
    print("\n4. Running simulation steps...")
    actions = [
        "produce_ricotta_salad",
        "produce_shrimp_fried_rice",
        "produce_tomato_pasta",
        "continue",
        "continue",
    ]

    for i, action in enumerate(actions):
        print(f"\n   Step {i+1}: Action = {action}")
        obs, done, reward, reset = env.step(action)
        print(f"   Reward: {reward}, Terminal: {done}")

    # Run more steps to see production
    print("\n5. Running 50 more steps to see production progress...")
    for i in range(50):
        obs, done, reward, reset = env.step("continue")
        if reward != 0 or i % 10 == 0:
            print(f"   Step {i+1}: Reward = {reward}")

    # Print final state
    print("\n6. State after 55 steps:")
    print(env.state_string())

    # Check state builder
    print("\n7. Checking state builder...")
    state = env.state_builder()
    print(f"   State keys: {state.keys()}")
    print(f"   KPIs: {state['kpis']}")

    print("\n" + "=" * 60)
    print("Factory Environment Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_factory_environment()
