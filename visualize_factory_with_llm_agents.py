"""
Factory Visualization with LLM-based Agents.

This script shows the production process with intelligent LLM agents making strategic
and design decisions in real-time.
"""

import sys
import time
from collections import defaultdict

import pygame

import realtimegym
from realtimegym.environments.factory import (
    LLMDesignAgent,
    LLMMetaPlannerAgent,
    RecipeType,
)
from realtimegym.environments.factory.items import Item, ItemType
from realtimegym.prompts import factory_upper_agents as prompts

# Create environment
print("Creating Factory environment with LLM-based intelligent agents...")
env, seed, renderer = realtimegym.make("Factory-v0", seed=0, render=True)

# Create LLM agents
print("Initializing LLM agents...")
meta_planner = LLMMetaPlannerAgent(
    prompts=prompts,
    file="logs/llm_meta_planner.csv",
    time_unit="token"
)

design_agent = LLMDesignAgent(
    prompts=prompts,
    file="logs/llm_design_agent.csv",
    time_unit="token"
)

# Configure LLM agents (will use rule-based fallback if no API key)
try:
    meta_planner.config_model1(
        "configs/example-meta-planner.yaml",
        internal_budget=1500  # Reduced for faster response
    )
    print("[OK] MetaPlannerAgent configured with LLM (GPT-4o)")
    llm_enabled_meta = True
except Exception as e:
    print(f"[INFO] MetaPlannerAgent using rule-based fallback: {e}")
    llm_enabled_meta = False

try:
    design_agent.config_model1(
        "configs/example-design-agent.yaml",
        internal_budget=1500
    )
    print("[OK] DesignAgent configured with LLM (GPT-4o)")
    llm_enabled_design = True
except Exception as e:
    print(f"[INFO] DesignAgent using rule-based fallback: {e}")
    llm_enabled_design = False

if llm_enabled_meta or llm_enabled_design:
    print("[INFO] LLM agents active - decisions will be powered by AI!")
else:
    print("[INFO] Using rule-based fallback - set API keys in .env for LLM mode")

# Reset environment
obs, done = env.reset()
print(f"Environment initialized. Target: {env.target_products} products\n")

# Setup pygame window
pygame.init()
screen_width = 1400
screen_height = renderer.height + 100
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption(f"Factory with LLM Agents - {env.current_recipe.value.upper()}")
clock = pygame.time.Clock()

# Fonts
title_font = pygame.font.Font(None, 28)
font = pygame.font.Font(None, 22)
small_font = pygame.font.Font(None, 18)
tiny_font = pygame.font.Font(None, 14)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BLUE = (200, 220, 255)
LIGHT_GREEN = (200, 255, 200)
LIGHT_YELLOW = (255, 255, 200)
LIGHT_RED = (255, 200, 200)
GRAY = (220, 220, 220)
DARK_GRAY = (100, 100, 100)
LLM_BLUE = (100, 150, 255)
AI_GREEN = (0, 200, 100)


def start_production_batch():
    """Start a new production batch."""
    if env.completed_products >= env.target_products:
        return False

    from realtimegym.environments.factory import RECIPES
    recipe = RECIPES[env.current_recipe]
    required_ingredients = recipe.ingredients

    added = False

    for station in env.stations:
        if station.station_type.value == "Washer" and len(station.input_buffer) < 2:
            for ingredient in required_ingredients:
                item = Item(
                    item_type=ingredient,
                    quantity=1,
                    quality=1.0,
                    processed=False,
                    line=station.line
                )
                station.input_buffer.append(item)
                added = True
            break

    return added


def draw_side_panel(screen, step_count, meta_decision, design_decision):
    """Draw side panel with LLM agent information."""
    panel_x = renderer.width + 10
    panel_width = screen_width - renderer.width - 20

    # Background
    pygame.draw.rect(screen, GRAY, (panel_x, 0, panel_width, screen_height))

    y = 10

    # Title with LLM indicator
    if llm_enabled_meta or llm_enabled_design:
        title = title_font.render("AI AGENT CONTROL", True, LLM_BLUE)
        screen.blit(title, (panel_x + 10, y))
        y += 25
        subtitle = tiny_font.render("Powered by Large Language Models", True, AI_GREEN)
        screen.blit(subtitle, (panel_x + 10, y))
    else:
        title = title_font.render("AGENT CONTROL", True, BLACK)
        screen.blit(title, (panel_x + 10, y))
        y += 25
        subtitle = tiny_font.render("Rule-based fallback mode", True, DARK_GRAY)
        screen.blit(subtitle, (panel_x + 10, y))

    y += 20

    # === Meta Planner Section ===
    section_title = font.render("META PLANNER", True, (50, 50, 150))
    screen.blit(section_title, (panel_x + 10, y))
    y += 25

    # Performance status
    perf = meta_decision.get("performance_assessment", {})
    status_colors = {"excellent": (0, 150, 0), "acceptable": (200, 150, 0), "critical": (200, 0, 0)}
    status_color = status_colors.get(perf.get("overall_status", "unknown"), DARK_GRAY)

    status_bg = pygame.Surface((panel_width - 20, 22))
    status_bg.fill(status_color)
    status_bg.set_alpha(50)
    screen.blit(status_bg, (panel_x + 10, y))

    status_text = small_font.render(
        f"Status: {perf.get('overall_status', 'unknown').upper()}",
        True,
        status_color
    )
    screen.blit(status_text, (panel_x + 15, y + 3))
    y += 28

    # LLM Analysis
    if "llm_analysis" in meta_decision:
        llm_icon = tiny_font.render("[AI]", True, LLM_BLUE)
        screen.blit(llm_icon, (panel_x + 15, y))

        llm_analysis = meta_decision["llm_analysis"]

        # Situation Assessment
        if "situation_assessment" in llm_analysis:
            assessment = llm_analysis["situation_assessment"][:80]
            assess_text = tiny_font.render(
                f"Assessment: {assessment}...",
                True,
                BLACK
            )
            screen.blit(assess_text, (panel_x + 45, y))
            y += 16

        # Strategic Priorities
        if "strategic_priorities" in llm_analysis:
            y += 5
            priorities_title = small_font.render("AI Strategic Priorities:", True, LLM_BLUE)
            screen.blit(priorities_title, (panel_x + 15, y))
            y += 20

            for priority in llm_analysis["strategic_priorities"][:2]:
                priority_text = tiny_font.render(
                    f"  • {priority[:45]}",
                    True,
                    BLACK
                )
                screen.blit(priority_text, (panel_x + 20, y))
                y += 16

        # Immediate Actions
        if "immediate_actions" in llm_analysis:
            y += 5
            actions_title = small_font.render("AI Recommendations:", True, AI_GREEN)
            screen.blit(actions_title, (panel_x + 15, y))
            y += 20

            for action in llm_analysis["immediate_actions"][:2]:
                action_text = tiny_font.render(
                    f"  → {action[:45]}",
                    True,
                    (0, 100, 0)
                )
                screen.blit(action_text, (panel_x + 20, y))
                y += 16
    else:
        # Show rule-based objectives
        objectives = meta_decision.get("objectives", [])
        if objectives:
            obj_title = small_font.render("Active Objectives:", True, BLACK)
            screen.blit(obj_title, (panel_x + 15, y))
            y += 20

            for obj in objectives[:2]:
                obj_text = tiny_font.render(
                    f"[{obj['priority']}] {obj['description'][:35]}",
                    True,
                    (100, 100, 100)
                )
                screen.blit(obj_text, (panel_x + 20, y))
                y += 16

    # === Design Agent Section ===
    y += 15
    design_title = font.render("DESIGN AGENT", True, (150, 50, 50))
    screen.blit(design_title, (panel_x + 10, y))
    y += 25

    # System metrics
    sys_metrics = design_decision.get("system_metrics", {})
    metrics_lines = [
        f"Line Balance: {sys_metrics.get('line_balance', 0)*100:.0f}%",
        f"Utilization: {sys_metrics.get('average_utilization', 0)*100:.0f}%",
        f"Bottlenecks: {sys_metrics.get('bottleneck_count', 0)}",
    ]
    for line in metrics_lines:
        text = tiny_font.render(line, True, BLACK)
        screen.blit(text, (panel_x + 15, y))
        y += 16

    # LLM Analysis
    if "llm_analysis" in design_decision:
        y += 5
        llm_icon = tiny_font.render("[AI]", True, LLM_BLUE)
        screen.blit(llm_icon, (panel_x + 15, y))

        llm_analysis = design_decision["llm_analysis"]

        # System Assessment
        if "system_assessment" in llm_analysis:
            assessment = llm_analysis["system_assessment"][:75]
            assess_text = tiny_font.render(
                f"{assessment}...",
                True,
                BLACK
            )
            screen.blit(assess_text, (panel_x + 45, y))
            y += 16

        # Design Recommendations
        if "design_recommendations" in llm_analysis:
            y += 5
            rec_title = small_font.render("AI Design Advice:", True, LLM_BLUE)
            screen.blit(rec_title, (panel_x + 15, y))
            y += 20

            for rec in llm_analysis["design_recommendations"][:2]:
                rec_text = tiny_font.render(
                    f"  • {rec.get('recommendation', '')[:40]}",
                    True,
                    BLACK
                )
                screen.blit(rec_text, (panel_x + 20, y))
                y += 14

                # Show rationale
                rationale = rec.get('rationale', '')[:45]
                if rationale:
                    rat_text = tiny_font.render(
                        f"    ↳ {rationale}",
                        True,
                        DARK_GRAY
                    )
                    screen.blit(rat_text, (panel_x + 25, y))
                    y += 14
    else:
        # Show bottlenecks
        bottlenecks = [a for a in design_decision.get("capacity_analysis", []) if a.get("is_bottleneck", False)]
        if bottlenecks:
            y += 5
            bn_title = small_font.render("Bottlenecks:", True, (200, 100, 0))
            screen.blit(bn_title, (panel_x + 15, y))
            y += 20

            for bn in bottlenecks[:2]:
                bn_text = tiny_font.render(
                    f"{bn['station_type']}: {bn['utilization_rate']*100:.0f}%",
                    True,
                    (150, 80, 0)
                )
                screen.blit(bn_text, (panel_x + 20, y))
                y += 16

    # === Station Status Section ===
    y += 15
    station_title = font.render("STATION STATUS", True, BLACK)
    screen.blit(station_title, (panel_x + 10, y))
    y += 25

    station_types = ["Washer", "Cutter", "Plating", "Sealing", "VisionQA"]
    for st_type in station_types:
        stations_of_type = [s for s in env.stations if s.station_type.value == st_type]
        if stations_of_type:
            busy_count = sum(1 for s in stations_of_type if s.status.value == "Busy")
            in_count = sum(len(s.input_buffer) for s in stations_of_type)
            out_count = sum(len(s.output_buffer) for s in stations_of_type)

            if busy_count == len(stations_of_type):
                color = (0, 150, 0)
            elif busy_count > 0:
                color = (150, 150, 0)
            else:
                color = DARK_GRAY

            status_text = tiny_font.render(
                f"{st_type}: {busy_count}/{len(stations_of_type)} | I:{in_count} O:{out_count}",
                True,
                color
            )
            screen.blit(status_text, (panel_x + 15, y))
            y += 18


def draw_main_view(screen):
    """Draw main factory view."""
    frame = renderer.render(env)
    screen.blit(frame, (0, 0))

    bar_y = renderer.height + 10
    bar_height = 30
    bar_x = 50
    bar_width = renderer.width - 100

    progress = env.completed_products / env.target_products

    pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * progress), bar_height))
    pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height), 2)

    progress_text = font.render(
        f"Progress: {env.completed_products}/{env.target_products} ({progress*100:.1f}%) | Quality: {100 if env.completed_products == 0 else env.completed_products/(env.completed_products+env.defective_products)*100:.1f}%",
        True,
        BLACK
    )
    text_rect = progress_text.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
    screen.blit(progress_text, text_rect)

    controls_y = bar_y + bar_height + 10
    if llm_enabled_meta or llm_enabled_design:
        controls_text = small_font.render(
            "SPACE: Speed | DOWN: Slow | P: Pause | ESC: Quit | [LLM AI ACTIVE]",
            True,
            LLM_BLUE
        )
    else:
        controls_text = small_font.render(
            "SPACE: Speed Up | DOWN: Slow Down | P: Pause | ESC: Quit",
            True,
            DARK_GRAY
        )
    screen.blit(controls_text, (bar_x, controls_y))


# Main simulation loop
running = True
step_count = 0
speed = 1
paused = False

# Agent update frequency
agent_update_interval = 20  # Update LLM agents every 20 steps to reduce API calls

print("\nStarting detailed visualization with LLM AI agents...")
print("Controls:")
print("  SPACE: Speed up (2x, 4x, 8x, 16x, 32x)")
print("  DOWN: Slow down")
print("  P: Pause/Resume")
print("  ESC: Quit")
print()
if llm_enabled_meta or llm_enabled_design:
    print("[INFO] LLM agents will update every", agent_update_interval, "steps to optimize API usage")
    print()

# Initial agent decisions
meta_decision = {}
design_decision = {}

while running and not done:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                speed = min(speed * 2, 32)
                print(f"Speed: {speed}x")
            elif event.key == pygame.K_DOWN:
                speed = max(speed // 2, 1)
                print(f"Speed: {speed}x")
            elif event.key == pygame.K_p:
                paused = not paused
                print("Paused" if paused else "Resumed")

    if not paused:
        for _ in range(speed):
            # Start production every 20 steps
            if step_count % 20 == 0:
                start_production_batch()

            # Update LLM agents periodically
            if step_count % agent_update_interval == 0:
                state = env.state_builder()
                observation = {
                    "state_string": env.state_string(),
                    "game_turn": env.game_turn,
                    "state": state
                }

                # Update agents
                meta_planner.observe(observation)
                design_agent.observe(observation)

                # Think (calls LLM if configured)
                try:
                    meta_planner.think(timeout=1500)
                    meta_decision = meta_planner.get_decision()
                    if "llm_analysis" in meta_decision:
                        print(f"[Step {step_count}] Meta Planner AI: {meta_decision['llm_analysis'].get('situation_assessment', '')[:60]}...")
                except Exception as e:
                    print(f"[Step {step_count}] Meta Planner error: {e}")

                try:
                    design_agent.think(timeout=1500)
                    design_decision = design_agent.get_decision()
                    if "llm_analysis" in design_decision:
                        print(f"[Step {step_count}] Design Agent AI: {design_decision['llm_analysis'].get('system_assessment', '')[:60]}...")
                except Exception as e:
                    print(f"[Step {step_count}] Design Agent error: {e}")

            # Step environment
            obs, done, reward, reset = env.step("WAIT")
            step_count += 1

            # Check for completed items
            for station in env.stations:
                if station.station_type.value == "Storage" and station.position[0] == 19:
                    while len(station.input_buffer) > 0:
                        item = station.input_buffer.pop(0)
                        if item.item_type != ItemType.DEFECTIVE:
                            env.completed_products += 1
                            print(f"[OK] [Line {item.line}] Product #{env.completed_products} completed at step {step_count}")
                        else:
                            env.defective_products += 1
                            print(f"[DEFECT] [Line {item.line}] Defective product at step {step_count}")

            if done:
                break

    # Render
    screen.fill(WHITE)
    draw_main_view(screen)
    draw_side_panel(screen, step_count, meta_decision, design_decision)

    pygame.display.flip()
    clock.tick(30)

# Final results
print("\n" + "="*70)
print("SIMULATION COMPLETE".center(70))
print("="*70)
print(f"\nProduction Statistics:")
print(f"  Total Steps: {step_count}")
print(f"  Completed Products: {env.completed_products}/{env.target_products}")
print(f"  Defective Products: {env.defective_products}")
total = env.completed_products + env.defective_products
if total > 0:
    print(f"  Quality Rate: {env.completed_products/total*100:.1f}%")
print(f"  Final Reward: {env.reward:.2f}")

# Final agent analysis
print(f"\n" + "-"*70)
print("FINAL AI AGENT ANALYSIS".center(70))
print("-"*70)

# Get final decisions
state = env.state_builder()
observation = {"state_string": env.state_string(), "game_turn": env.game_turn, "state": state}

meta_planner.observe(observation)
design_agent.observe(observation)

try:
    meta_planner.think(timeout=1500)
    final_meta = meta_planner.get_decision()
except Exception:
    final_meta = meta_decision

try:
    design_agent.think(timeout=1500)
    final_design = design_agent.get_decision()
except Exception:
    final_design = design_decision

print("\nMeta Planner Final Assessment:")
if "llm_analysis" in final_meta:
    llm = final_meta["llm_analysis"]
    if "situation_assessment" in llm:
        print(f"  AI Assessment: {llm['situation_assessment']}")
    if "strategic_priorities" in llm:
        print(f"  AI Priorities:")
        for p in llm["strategic_priorities"][:3]:
            print(f"    - {p}")
else:
    perf = final_meta.get("performance_assessment", {})
    print(f"  Overall Status: {perf.get('overall_status', 'unknown').upper()}")
    print(f"  Production Progress: {perf.get('production_progress', 0)*100:.1f}%")
    print(f"  Quality Performance: {perf.get('quality_performance', 0)*100:.1f}%")

print("\nDesign Agent Final Analysis:")
if "llm_analysis" in final_design:
    llm = final_design["llm_analysis"]
    if "system_assessment" in llm:
        print(f"  AI Assessment: {llm['system_assessment']}")
    if "design_recommendations" in llm:
        print(f"  AI Recommendations:")
        for rec in llm["design_recommendations"][:3]:
            print(f"    - {rec.get('recommendation', 'N/A')}")
else:
    sys_metrics = final_design.get("system_metrics", {})
    print(f"  Line Balance: {sys_metrics.get('line_balance', 0)*100:.1f}%")
    print(f"  Average Utilization: {sys_metrics.get('average_utilization', 0)*100:.1f}%")

print("\n" + "="*70)
if llm_enabled_meta or llm_enabled_design:
    print("LLM AI was active during this simulation!")
    print("Decisions were powered by Large Language Models.")
else:
    print("Simulation ran with rule-based fallback.")
    print("To enable LLM AI: Set OPENAI_API_KEY in .env file")
print("="*70)

# Wait before closing
time.sleep(3)
pygame.quit()
sys.exit()
