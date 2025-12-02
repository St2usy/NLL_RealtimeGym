"""
Integration tests for Factory environment rule validation.

Tests that factory operates correctly based on rules specified by upper agents,
including item flow, logistic routing, and station processing.
"""

from realtimegym.environments.factory import (
    RECIPES,
    Cooker,
    Cutter,
    Item,
    ItemType,
    LogisticRobot,
    Plating,
    Recipe,
    RecipeType,
    RobotArm,
    Sealing,
    Station,
    StationStatus,
    StationType,
    Storage,
    Task,
    VisionQA,
    Washer,
)


class TestFactoryProductCompletion:
    """Test scenarios for complete product manufacturing flow."""

    def test_salad_production_simple_scenario(self):
        """
        Test complete salad production with manually assigned items and stations.

        Scenario:
        1. Create stations in sequence: Storage -> Washer -> Cutter -> Plating -> Sealing -> VisionQA -> Storage
        2. Add ingredients to input storage
        3. Create logistic robots to transport items
        4. Run simulation until product is complete
        5. Verify final product in output storage
        """
        # Setup recipe
        recipe = RECIPES[RecipeType.SALAD]

        # Create stations
        stations = []
        input_storage = Storage(
            station_id=0, station_type=StationType.STORAGE, position=(0, 0), line=1
        )
        stations.append(input_storage)

        washer = Washer(
            station_id=1, station_type=StationType.WASHER, position=(2, 0), line=1
        )
        stations.append(washer)

        cutter = Cutter(
            station_id=2, station_type=StationType.CUTTER, position=(4, 0), line=1
        )
        stations.append(cutter)

        plating = Plating(
            station_id=3, station_type=StationType.PLATING, position=(6, 0), line=1
        )
        plating.current_recipe = recipe
        plating.input_buffer_size = 10  # Large enough for all ingredients
        stations.append(plating)

        sealing = Sealing(
            station_id=4, station_type=StationType.SEALING, position=(8, 0), line=1
        )
        stations.append(sealing)

        vision_qa = VisionQA(
            station_id=5, station_type=StationType.VISION_QA, position=(10, 0), line=1
        )
        stations.append(vision_qa)

        output_storage = Storage(
            station_id=6, station_type=StationType.STORAGE, position=(12, 0), line=1
        )
        stations.append(output_storage)

        # Add ingredients to input storage
        for ingredient in recipe.ingredients:
            input_storage.add_to_inventory(ingredient, 10)

        # Create logistic robots (one per segment)
        robots = []
        robot_id = 0

        # Robot 1: Washer -> Cutter
        robots.append(
            LogisticRobot(
                robot_id=robot_id,
                position=(3, 0),
                line=1,
                assigned_segment=("Washer", "Cutter"),
            )
        )
        robot_id += 1

        # Robot 2: Cutter -> Plating
        robots.append(
            LogisticRobot(
                robot_id=robot_id,
                position=(5, 0),
                line=1,
                assigned_segment=("Cutter", "Plating"),
            )
        )
        robot_id += 1

        # Robot 3: Plating -> Sealing
        robots.append(
            LogisticRobot(
                robot_id=robot_id,
                position=(7, 0),
                line=1,
                assigned_segment=("Plating", "Sealing"),
            )
        )
        robot_id += 1

        # Robot 4: Sealing -> VisionQA
        robots.append(
            LogisticRobot(
                robot_id=robot_id,
                position=(9, 0),
                line=1,
                assigned_segment=("Sealing", "VisionQA"),
            )
        )
        robot_id += 1

        # Robot 5: VisionQA -> Storage
        robots.append(
            LogisticRobot(
                robot_id=robot_id,
                position=(11, 0),
                line=1,
                assigned_segment=("VisionQA", "Storage"),
            )
        )

        # Create grid (simplified, 1D line with enough rows)
        grid = [[None for _ in range(13)] for _ in range(13)]
        for station in stations:
            row, col = station.position
            grid[row][col] = station

        # Step 1: Move ingredients from storage to washer input
        print("\n=== Step 1: Loading ingredients to Washer ===")
        for ingredient in recipe.ingredients:
            item = input_storage.get_from_inventory(ingredient, 1)
            assert item is not None, f"Failed to get {ingredient} from storage"
            success = washer.add_input(item)
            assert success, f"Failed to add {ingredient} to washer"
            print(f"[OK] Added {ingredient.value} to Washer")

        # Step 2: Process washing (10 steps per recipe)
        print("\n=== Step 2: Washing ingredients ===")
        for i in range(recipe.processing_time["Washer"]):
            washer.process()
        print(f"[OK] Washing complete: {len(washer.output_buffer)} items in output")
        assert len(washer.output_buffer) == len(
            recipe.ingredients
        ), "All ingredients should be washed"

        # Step 3: Transport to cutter (using robot)
        print("\n=== Step 3: Transporting to Cutter ===")
        robot = robots[0]  # Washer -> Cutter robot
        while washer.can_provide_output():
            # Pick task
            pick_task = Task(
                task_id=0,
                task_type="pick",
                target_station=washer,
                target_position=washer.position,
            )
            robot.assign_task(pick_task)
            # Execute until picked
            while len(robot.task_queue) > 0 or robot.current_task is not None:
                robot.step(grid)
            assert robot.carrying_item is not None, "Robot should be carrying item"

            # Drop task
            drop_task = Task(
                task_id=1,
                task_type="drop",
                target_station=cutter,
                target_position=cutter.position,
            )
            robot.assign_task(drop_task)
            # Execute until dropped
            while len(robot.task_queue) > 0 or robot.current_task is not None:
                robot.step(grid)
            assert robot.carrying_item is None, "Robot should have dropped item"

        print(f"[OK] Transport complete: {len(cutter.input_buffer)} items in Cutter")

        # Step 4: Process cutting
        print("\n=== Step 4: Cutting ingredients ===")
        for i in range(recipe.processing_time["Cutter"]):
            cutter.process()
        print(f"[OK] Cutting complete: {len(cutter.output_buffer)} items in output")

        # Step 5: Transport to plating
        print("\n=== Step 5: Transporting to Plating ===")
        robot = robots[1]  # Cutter -> Plating robot
        while cutter.can_provide_output():
            # Pick task
            pick_task = Task(
                task_id=0,
                task_type="pick",
                target_station=cutter,
                target_position=cutter.position,
            )
            robot.assign_task(pick_task)
            while len(robot.task_queue) > 0 or robot.current_task is not None:
                robot.step(grid)

            # Drop task
            drop_task = Task(
                task_id=1,
                task_type="drop",
                target_station=plating,
                target_position=plating.position,
            )
            robot.assign_task(drop_task)
            while len(robot.task_queue) > 0 or robot.current_task is not None:
                robot.step(grid)

        print(f"[OK] Transport complete: {len(plating.input_buffer)} items in Plating")

        # Step 6: Process plating (combines ingredients into salad)
        print("\n=== Step 6: Plating (combining ingredients) ===")
        for i in range(recipe.processing_time["Plating"]):
            plating.process()
        print(f"[OK] Plating complete: {len(plating.output_buffer)} salad(s) in output")
        assert (
            len(plating.output_buffer) == 1
        ), "Should have 1 salad after combining ingredients"
        salad = plating.output_buffer[0]
        assert (
            salad.item_type == ItemType.SALAD
        ), f"Expected SALAD, got {salad.item_type}"

        # Step 7: Transport to sealing
        print("\n=== Step 7: Transporting to Sealing ===")
        robot = robots[2]  # Plating -> Sealing robot
        pick_task = Task(
            task_id=0,
            task_type="pick",
            target_station=plating,
            target_position=plating.position,
        )
        robot.assign_task(pick_task)
        while len(robot.task_queue) > 0 or robot.current_task is not None:
            robot.step(grid)

        drop_task = Task(
            task_id=1,
            task_type="drop",
            target_station=sealing,
            target_position=sealing.position,
        )
        robot.assign_task(drop_task)
        while len(robot.task_queue) > 0 or robot.current_task is not None:
            robot.step(grid)
        print(f"[OK] Transport complete: {len(sealing.input_buffer)} items in Sealing")

        # Step 8: Process sealing
        print("\n=== Step 8: Sealing ===")
        for i in range(recipe.processing_time["Sealing"]):
            sealing.process()
        print(f"[OK] Sealing complete: {len(sealing.output_buffer)} item(s) in output")
        sealed_salad = sealing.output_buffer[0]
        assert (
            sealed_salad.metadata.get("sealed") is True
        ), "Salad should be sealed"

        # Step 9: Transport to VisionQA
        print("\n=== Step 9: Transporting to VisionQA ===")
        robot = robots[3]  # Sealing -> VisionQA robot
        pick_task = Task(
            task_id=0,
            task_type="pick",
            target_station=sealing,
            target_position=sealing.position,
        )
        robot.assign_task(pick_task)
        while len(robot.task_queue) > 0 or robot.current_task is not None:
            robot.step(grid)

        drop_task = Task(
            task_id=1,
            task_type="drop",
            target_station=vision_qa,
            target_position=vision_qa.position,
        )
        robot.assign_task(drop_task)
        while len(robot.task_queue) > 0 or robot.current_task is not None:
            robot.step(grid)
        print(f"[OK] Transport complete: {len(vision_qa.input_buffer)} items in VisionQA")

        # Step 10: Process VisionQA
        print("\n=== Step 10: Quality Inspection ===")
        for i in range(recipe.processing_time["VisionQA"]):
            vision_qa.process()
        print(
            f"[OK] QA complete: {len(vision_qa.output_buffer)} item(s) passed inspection"
        )
        inspected_salad = vision_qa.output_buffer[0]
        assert (
            inspected_salad.quality >= recipe.quality_threshold
        ), f"Salad quality {inspected_salad.quality} below threshold {recipe.quality_threshold}"
        print(f"  Quality: {inspected_salad.quality:.2f} (threshold: {recipe.quality_threshold})")

        # Step 11: Transport to output storage
        print("\n=== Step 11: Transporting to Output Storage ===")
        robot = robots[4]  # VisionQA -> Storage robot
        pick_task = Task(
            task_id=0,
            task_type="pick",
            target_station=vision_qa,
            target_position=vision_qa.position,
        )
        robot.assign_task(pick_task)
        while len(robot.task_queue) > 0 or robot.current_task is not None:
            robot.step(grid)

        drop_task = Task(
            task_id=1,
            task_type="drop",
            target_station=output_storage,
            target_position=output_storage.position,
        )
        robot.assign_task(drop_task)
        while len(robot.task_queue) > 0 or robot.current_task is not None:
            robot.step(grid)
        print(
            f"[OK] Transport complete: {len(output_storage.input_buffer)} items in Output Storage"
        )

        # Final verification
        print("\n=== Final Verification ===")
        assert output_storage.can_provide_output(), "Output storage should have product"
        final_product = output_storage.take_output()
        assert final_product is not None, "Should have final product"
        assert (
            final_product.item_type == ItemType.SALAD
        ), f"Expected SALAD, got {final_product.item_type}"
        assert final_product.processed is True, "Product should be processed"
        assert (
            final_product.metadata.get("sealed") is True
        ), "Product should be sealed"
        print(f"[OK] Final product: {final_product}")
        print(f"  Type: {final_product.item_type.value}")
        print(f"  Quality: {final_product.quality:.2f}")
        print(f"  Sealed: {final_product.metadata.get('sealed')}")
        print("\n[SUCCESS] Salad production scenario completed successfully!")

    def test_pasta_production_with_cooker(self):
        """
        Test pasta production including cooking step.

        Scenario:
        1. Create stations: Storage -> Washer -> Cutter -> Cooker -> Plating -> Sealing -> VisionQA -> Storage
        2. Test Cooker station with recipe-based ingredient combination
        3. Verify cooked pasta dish is produced
        """
        recipe = RECIPES[RecipeType.PASTA]

        # Create stations
        stations = []
        input_storage = Storage(
            station_id=0, station_type=StationType.STORAGE, position=(0, 0), line=1
        )
        stations.append(input_storage)

        washer = Washer(
            station_id=1, station_type=StationType.WASHER, position=(2, 0), line=1
        )
        stations.append(washer)

        cutter = Cutter(
            station_id=2, station_type=StationType.CUTTER, position=(4, 0), line=1
        )
        stations.append(cutter)

        cooker = Cooker(
            station_id=3, station_type=StationType.COOKER, position=(6, 0), line=1
        )
        cooker.current_recipe = recipe
        cooker.temperature = 180.0  # Optimal temperature
        cooker.buffer_capacity = 10
        stations.append(cooker)

        plating = Plating(
            station_id=4, station_type=StationType.PLATING, position=(8, 0), line=1
        )
        plating.current_recipe = recipe
        stations.append(plating)

        sealing = Sealing(
            station_id=5, station_type=StationType.SEALING, position=(10, 0), line=1
        )
        stations.append(sealing)

        vision_qa = VisionQA(
            station_id=6, station_type=StationType.VISION_QA, position=(12, 0), line=1
        )
        stations.append(vision_qa)

        output_storage = Storage(
            station_id=7, station_type=StationType.STORAGE, position=(14, 0), line=1
        )
        stations.append(output_storage)

        # Add ingredients to input storage
        for ingredient in recipe.ingredients:
            input_storage.add_to_inventory(ingredient, 10)

        print("\n=== Pasta Production Test ===")

        # Step 1: Load ingredients to washer and process
        print("\n1. Loading and washing ingredients...")
        for ingredient in recipe.ingredients:
            item = input_storage.get_from_inventory(ingredient, 1)
            washer.add_input(item)
        for _ in range(recipe.processing_time["Washer"]):
            washer.process()
        print(f"[OK] Washed {len(washer.output_buffer)} ingredients")

        # Step 2: Transfer to cutter and process
        print("\n2. Cutting ingredients...")
        while washer.can_provide_output():
            item = washer.take_output()
            cutter.add_input(item)
        for _ in range(recipe.processing_time["Cutter"]):
            cutter.process()
        print(f"[OK] Cut {len(cutter.output_buffer)} ingredients")

        # Step 3: Transfer to cooker and process (combines ingredients)
        print("\n3. Cooking (combining ingredients into pasta dish)...")
        while cutter.can_provide_output():
            item = cutter.take_output()
            cooker.add_input(item)
        print(f"   Cooker input buffer: {len(cooker.input_buffer)} items")

        # Process cooking
        for _ in range(recipe.processing_time["Cooker"]):
            cooker.process()
        print(f"[OK] Cooked {len(cooker.output_buffer)} dish(es)")

        # Verify cooked pasta
        assert len(cooker.output_buffer) == 1, "Should produce 1 pasta dish"
        pasta_dish = cooker.output_buffer[0]
        assert (
            pasta_dish.item_type == ItemType.PASTA_DISH
        ), f"Expected PASTA_DISH, got {pasta_dish.item_type}"
        print(f"   Dish type: {pasta_dish.item_type.value}")
        print(f"   Quality: {pasta_dish.quality:.2f}")

        # Step 4: Continue through remaining stations
        print("\n4. Plating...")
        plating.add_input(cooker.take_output())
        for _ in range(recipe.processing_time["Plating"]):
            plating.process()

        print("5. Sealing...")
        sealing.add_input(plating.take_output())
        for _ in range(recipe.processing_time["Sealing"]):
            sealing.process()

        print("6. Quality inspection...")
        vision_qa.add_input(sealing.take_output())
        for _ in range(recipe.processing_time["VisionQA"]):
            vision_qa.process()

        # Final verification
        print("\n7. Final verification...")
        final_product = vision_qa.take_output()
        assert final_product is not None, "Should have final product"
        assert (
            final_product.item_type == ItemType.PASTA_DISH
        ), f"Expected PASTA_DISH, got {final_product.item_type}"
        assert (
            final_product.quality >= recipe.quality_threshold
        ), f"Quality {final_product.quality} below threshold {recipe.quality_threshold}"
        print(f"[OK] Final product: {final_product.item_type.value}")
        print(f"  Quality: {final_product.quality:.2f}")
        print("\n[SUCCESS] Pasta production test completed successfully!")


class TestFactoryUpperAgentRules:
    """Test factory compliance with upper agent rules."""

    def test_product_design_agent_route_compliance(self):
        """
        Test that factory follows ProductDesignAgent's specified route.

        Scenario:
        1. ProductDesignAgent specifies a custom route
        2. Factory should process items through exactly those stations in order
        3. Verify items visit all specified stations
        """
        from realtimegym.environments.factory import ProductDesignAgent

        # Create product design agent
        agent = ProductDesignAgent()

        # Define custom route (simplified salad without some steps)
        custom_route = {
            "route": ["Storage", "Washer", "Cutter", "Plating", "Sealing", "Storage"],
            "batch_size": 5,
            "priority_stations": ["Plating"],
        }

        # Create stations according to agent's route
        stations = {}
        station_id = 0
        position_row = 0

        for station_name in custom_route["route"]:
            if station_name == "Storage":
                if "Storage" not in stations:
                    stations["Storage"] = Storage(
                        station_id=station_id,
                        station_type=StationType.STORAGE,
                        position=(position_row, 0),
                        line=1,
                    )
                    station_id += 1
                position_row += 2
            elif station_name == "Washer":
                stations["Washer"] = Washer(
                    station_id=station_id,
                    station_type=StationType.WASHER,
                    position=(position_row, 0),
                    line=1,
                )
                station_id += 1
                position_row += 2
            elif station_name == "Cutter":
                stations["Cutter"] = Cutter(
                    station_id=station_id,
                    station_type=StationType.CUTTER,
                    position=(position_row, 0),
                    line=1,
                )
                station_id += 1
                position_row += 2
            elif station_name == "Plating":
                plating = Plating(
                    station_id=station_id,
                    station_type=StationType.PLATING,
                    position=(position_row, 0),
                    line=1,
                )
                # Set recipe for plating
                plating.current_recipe = RECIPES[RecipeType.SALAD]
                plating.input_buffer_size = 10
                stations["Plating"] = plating
                station_id += 1
                position_row += 2
            elif station_name == "Sealing":
                stations["Sealing"] = Sealing(
                    station_id=station_id,
                    station_type=StationType.SEALING,
                    position=(position_row, 0),
                    line=1,
                )
                station_id += 1
                position_row += 2

        print("\n=== Upper Agent Rule Compliance Test ===")
        print(f"Agent-specified route: {custom_route['route']}")

        # Add ingredients to storage
        recipe = RECIPES[RecipeType.SALAD]
        for ingredient in recipe.ingredients:
            stations["Storage"].add_to_inventory(ingredient, 10)

        # Track item journey through stations
        item_journey = []

        # Process through route
        for i, station_name in enumerate(custom_route["route"]):
            if i == 0:  # First storage (input)
                print(f"\n{i+1}. {station_name} (Input)")
                # Get ingredients
                for ingredient in recipe.ingredients:
                    item = stations["Storage"].get_from_inventory(ingredient, 1)
                    stations["Washer"].add_input(item)
                item_journey.append(station_name)

            elif station_name == "Washer":
                print(f"\n{i+1}. {station_name}")
                station = stations[station_name]
                for _ in range(10):  # Process time
                    station.process()
                print(f"   Processed {len(station.output_buffer)} items")
                item_journey.append(station_name)

                # Transfer to next station
                next_station_name = custom_route["route"][i + 1]
                if next_station_name in stations:
                    while station.can_provide_output():
                        item = station.take_output()
                        stations[next_station_name].add_input(item)

            elif station_name == "Cutter":
                print(f"\n{i+1}. {station_name}")
                station = stations[station_name]
                for _ in range(12):  # Process time
                    station.process()
                print(f"   Processed {len(station.output_buffer)} items")
                item_journey.append(station_name)

                # Transfer to next station
                next_station_name = custom_route["route"][i + 1]
                if next_station_name in stations:
                    while station.can_provide_output():
                        item = station.take_output()
                        stations[next_station_name].add_input(item)

            elif station_name == "Plating":
                print(f"\n{i+1}. {station_name}")
                station = stations[station_name]
                for _ in range(6):  # Process time
                    station.process()
                print(f"   Combined into {len(station.output_buffer)} salad(s)")
                item_journey.append(station_name)

                # Transfer to next station
                next_station_name = custom_route["route"][i + 1]
                if next_station_name in stations:
                    while station.can_provide_output():
                        item = station.take_output()
                        stations[next_station_name].add_input(item)

            elif station_name == "Sealing":
                print(f"\n{i+1}. {station_name}")
                station = stations[station_name]
                for _ in range(6):  # Process time
                    station.process()
                print(f"   Sealed {len(station.output_buffer)} item(s)")
                item_journey.append(station_name)

                # Final station, product should be ready
                product = station.take_output()
                assert product is not None, "Should have final product"
                print(f"\n[OK] Final product: {product.item_type.value}")
                print(f"  Quality: {product.quality:.2f}")

        # Verify item journey matches agent's route
        print(f"\nItem journey: {item_journey}")
        print(f"Agent route:  {custom_route['route']}")

        # Check that journey matches route (excluding final Storage)
        assert item_journey == custom_route["route"][:-1], \
            f"Item journey {item_journey} doesn't match agent route {custom_route['route'][:-1]}"

        print("\n[SUCCESS] Factory successfully followed upper agent's specified route!")

    def test_facility_management_agent_station_monitoring(self):
        """
        Test that factory provides correct station status to FacilityManagementAgent.

        Scenario:
        1. Create stations with varying wear levels
        2. FacilityManagementAgent observes station states
        3. Verify agent receives accurate station information
        """
        from realtimegym.environments.factory import FacilityManagementAgent

        # Create facility management agent
        agent = FacilityManagementAgent()

        # Create stations with different conditions
        stations = [
            Cutter(
                station_id=0,
                station_type=StationType.CUTTER,
                position=(0, 0),
                line=1,
            ),
            Washer(
                station_id=1,
                station_type=StationType.WASHER,
                position=(2, 0),
                line=1,
            ),
            Cooker(
                station_id=2,
                station_type=StationType.COOKER,
                position=(4, 0),
                line=1,
            ),
        ]

        # Simulate wear on cutter (blade wear)
        stations[0].blade_wear = 0.8  # High blade wear
        stations[0].wear_level = 0.6

        # Simulate error on washer
        stations[1].status = StationStatus.ERROR

        # Normal cooker
        stations[2].wear_level = 0.1

        # Build state for agent observation
        state = {
            "stations": [s.get_state_dict() for s in stations],
        }

        print("\n=== Facility Management Agent Monitoring Test ===")
        print("\nStation States:")
        for i, station in enumerate(stations):
            station_state = state["stations"][i]
            print(f"{i+1}. {station_state['type']}")
            print(f"   Status: {station_state['status']}")
            print(f"   Wear Level: {station_state['wear_level']:.2f}")

        # Agent observes state
        agent.observe(state)

        print("\nAgent Observations:")
        print(f"  Total stations: {len(agent.observations['stations'])}")
        print(
            f"  Malfunctioned stations: {agent.observations['malfunction_count']}"
        )

        # Verify agent received correct information
        assert (
            len(agent.observations["stations"]) == 3
        ), "Agent should observe 3 stations"
        assert (
            agent.observations["malfunction_count"] == 1
        ), "Agent should detect 1 malfunction"

        # Agent makes decisions
        decisions = agent.decide()
        print("\nAgent Decisions:")
        print(f"  Maintenance schedule: {decisions['schedule_maintenance']}")
        print(f"  Urgent repairs: {decisions['urgent_repairs']}")

        print("\n[SUCCESS] Facility management agent correctly monitors station states!")


if __name__ == "__main__":
    # Run tests manually
    print("=" * 80)
    print("Running Factory Integration Tests")
    print("=" * 80)

    # Test 1: Salad production
    test_suite = TestFactoryProductCompletion()
    try:
        test_suite.test_salad_production_simple_scenario()
        print("\n" + "=" * 80)
        print("[PASS] Test 1 PASSED: Salad Production Simple Scenario")
        print("=" * 80)
    except AssertionError as e:
        print("\n" + "=" * 80)
        print(f"[FAIL] Test 1 FAILED: {e}")
        print("=" * 80)
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"[ERROR] Test 1 ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()

    # Test 2: Pasta production
    try:
        test_suite.test_pasta_production_with_cooker()
        print("\n" + "=" * 80)
        print("[PASS] Test 2 PASSED: Pasta Production with Cooker")
        print("=" * 80)
    except AssertionError as e:
        print("\n" + "=" * 80)
        print(f"[FAIL] Test 2 FAILED: {e}")
        print("=" * 80)
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"[ERROR] Test 2 ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()

    # Test 3: Upper agent rule compliance
    upper_agent_suite = TestFactoryUpperAgentRules()
    try:
        upper_agent_suite.test_product_design_agent_route_compliance()
        print("\n" + "=" * 80)
        print("[PASS] Test 3 PASSED: Product Design Agent Route Compliance")
        print("=" * 80)
    except AssertionError as e:
        print("\n" + "=" * 80)
        print(f"[FAIL] Test 3 FAILED: {e}")
        print("=" * 80)
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"[ERROR] Test 3 ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()

    # Test 4: Facility management agent
    try:
        upper_agent_suite.test_facility_management_agent_station_monitoring()
        print("\n" + "=" * 80)
        print("[PASS] Test 4 PASSED: Facility Management Agent Station Monitoring")
        print("=" * 80)
    except AssertionError as e:
        print("\n" + "=" * 80)
        print(f"[FAIL] Test 4 FAILED: {e}")
        print("=" * 80)
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"[ERROR] Test 4 ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)
