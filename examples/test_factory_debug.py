"""Debug test for Factory environment."""

import realtimegym


def test_factory_debug():
    """Test with detailed debugging output."""
    print("=" * 60)
    print("Factory Environment Debug Test")
    print("=" * 60)

    # Create and reset
    env, seed, renderer = realtimegym.make("Factory-v0", seed=0, render=False)
    obs, done = env.reset()

    print("\n Initial state:")
    state = env.state_builder()
    print(f"Storage[0] queue: {len(env.stations['Storage'][0].queue)}")
    print(f"Storage[0] output: {len(env.stations['Storage'][0].output_buffer)}")
    print(f"Storage[0] current_work: {env.stations['Storage'][0].current_work}")

    # Produce one item
    print("\n Step 1: produce_ricotta_salad")
    obs, done, reward, reset = env.step("produce_ricotta_salad")

    print(f"Products in progress: {len(env.products_in_progress)}")
    if len(env.products_in_progress) > 0:
        item = env.products_in_progress[0]
        print(f"  Product ID: {item.product_id}")
        print(f"  Product type: {item.product_type}")
        print(f"  Current step: {item.current_step}")
        print(f"  Time remaining: {item.time_remaining}")

    print(f"\nStorage[0] status: {env.stations['Storage'][0].status.value}")
    print(f"Storage[0] queue: {len(env.stations['Storage'][0].queue)}")
    print(f"Storage[0] output: {len(env.stations['Storage'][0].output_buffer)}")
    print(f"Storage[0] current_work: {env.stations['Storage'][0].current_work}")

    # Run several steps
    for i in range(20):
        print(f"\n Step {i+2}:")
        obs, done, reward, reset = env.step("continue")

        # Check all stations
        for station_type in ["Storage", "Washer", "Cutter", "Cooker", "Plating", "Sealing", "VisionQA", "FinalStorage"]:
            for idx, station in enumerate(env.stations[station_type]):
                if len(station.queue) > 0 or station.current_work or len(station.output_buffer) > 0:
                    print(f"  {station_type}[{idx}]: status={station.status.value}, "
                          f"queue={len(station.queue)}, "
                          f"working={station.current_work is not None}, "
                          f"output={len(station.output_buffer)}")
                    if station.current_work:
                        print(f"    -> Processing: {station.current_work.product_type}, "
                              f"time_remaining={station.current_work.time_remaining}")

        print(f"  Reward: {reward}, Completed: {len(env.completed_products)}")

    print("\n" + "=" * 60)
    print("Debug Test Complete!")
    print(f"Total completed: {len(env.completed_products)}")
    print(f"Total rejected: {env.rejected_products}")
    print("=" * 60)


if __name__ == "__main__":
    test_factory_debug()
